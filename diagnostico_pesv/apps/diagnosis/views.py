import traceback
import re
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
import base64
import pandas as pd
from apps.diagnosis_requirement.models import Diagnosis_Requirement, Recomendation
from apps.diagnosis_requirement.serializers import Recomendation_Serializer
from .models import Diagnosis_Questions, CheckList
from .serializers import Diagnosis_QuestionsSerializer, CheckListSerializer
from apps.company.models import (
    Company,
    VehicleQuestions,
    DriverQuestion,
    Fleet,
    Driver,
)
from utils.functionUtils import blank_to_null
from django.db import transaction
from docx import Document
from io import BytesIO
import os
from django.conf import settings
from .helper import *
from django.db.models import Sum, FloatField, Max, Avg, Count
import openpyxl
from openpyxl.chart import BarChart, Reference
from openpyxl.drawing.image import Image
from PIL import Image as PILImage
import matplotlib.pyplot as plt
from collections import defaultdict
from enum import Enum
from django.db.models import Prefetch, Value, Case, CharField, When
from django.db.models.functions import Coalesce
from .services import DiagnosisService
from django.core.exceptions import ObjectDoesNotExist


class CompanySizeEnum(Enum):
    AVANZADO = 3
    ESTANDAR = 2
    BASICO = 1


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def findQuestionsByCompanySize(request: Request):
    try:
        company_id = request.query_params.get("company")
        group_by_step = (
            request.query_params.get("group_by_step", "false").lower() == "true"
        )

        # Validar parámetro company_id
        if not company_id:
            return Response(
                {"error": "El parámetro 'company' es requerido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            company = Company.objects.get(pk=company_id)
        except Company.DoesNotExist:
            return Response(
                {"error": "Empresa no encontrada."}, status=status.HTTP_404_NOT_FOUND
            )

        # Obtener requisitos de diagnóstico según el tamaño de la empresa
        size_id = company.size.id
        if size_id == CompanySizeEnum.BASICO.value:
            diagnosis_requirements = Diagnosis_Requirement.objects.filter(basic=True)
        elif size_id == CompanySizeEnum.ESTANDAR.value:
            diagnosis_requirements = Diagnosis_Requirement.objects.filter(standard=True)
        elif size_id == CompanySizeEnum.AVANZADO.value:
            diagnosis_requirements = Diagnosis_Requirement.objects.filter(advanced=True)
        else:
            return Response(
                {"error": "Tamaño de empresa no válido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Obtener preguntas de diagnóstico
        diagnosis_questions = (
            Diagnosis_Questions.objects.filter(requirement__in=diagnosis_requirements)
            .select_related("requirement")
            .order_by("requirement__step")
        )

        if group_by_step:
            grouped_questions = group_questions_by_step(diagnosis_questions)
            return Response(grouped_questions, status=status.HTTP_200_OK)
        else:
            serialized_questions = Diagnosis_QuestionsSerializer(
                diagnosis_questions, many=True
            )
            return Response(serialized_questions.data, status=status.HTTP_200_OK)

    except Exception as ex:
        # logger.error(f"Error en findQuestionsByCompanySize: {str(ex)}")
        return Response(
            {"error": "Error interno del servidor."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def group_questions_by_step(questions):
    grouped_questions = {}
    for question in questions:
        step = question.requirement.step
        if step not in grouped_questions:
            grouped_questions[step] = {
                "id": question.requirement.id,
                "step": step,
                "cycle": question.requirement.cycle,
                "requirement_name": question.requirement.name,
                "questions": [],
            }
        grouped_questions[step]["questions"].append(question)

    grouped_questions_list = [
        {
            "id": group_data["id"],
            "step": group_data["step"],
            "cycle": group_data["cycle"],
            "requirement_name": group_data["requirement_name"],
            "questions": Diagnosis_QuestionsSerializer(
                group_data["questions"], many=True
            ).data,
        }
        for group_data in grouped_questions.values()
    ]
    return grouped_questions_list


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def uploadDiagnosisQuestions(request: Request):
    data = request.data.get("diagnosis_questions")
    if not data:
        return Response(
            {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
        )

    # Decodificar el base64
    try:
        decoded_file = base64.b64decode(data)
        excel_file = BytesIO(decoded_file)
        df = pd.read_excel(excel_file)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    processed_data = []

    for paso in df["PASO PESV"].unique():
        preguntas_por_paso = df[df["PASO PESV"] == paso]
        num_preguntas_por_paso = preguntas_por_paso[
            "CRITERIO DE VERIFICACIÓN"
        ].nunique()
        valor_pregunta = round(100 / num_preguntas_por_paso)

        for i, pregunta in preguntas_por_paso.iterrows():
            nombre_pregunta = pregunta["CRITERIO DE VERIFICACIÓN"]
            requisito = Diagnosis_Requirement.objects.get(step=paso)
            resultado = {
                "Requisito": requisito,
                "Nombre_Pregunta": nombre_pregunta,
                "Valor_Pregunta": valor_pregunta,
            }

            question_data = {
                "requirement": resultado["Requisito"].id,
                "name": str(resultado["Nombre_Pregunta"]).strip(),
                "variable_value": resultado["Valor_Pregunta"],
            }

            try:
                existing_question = Diagnosis_Questions.objects.get(
                    requirement=resultado["Requisito"],
                    name__iexact=resultado["Nombre_Pregunta"],
                )
                serializer = Diagnosis_QuestionsSerializer(
                    existing_question, data=question_data
                )
            except Diagnosis_Questions.DoesNotExist:
                serializer = Diagnosis_QuestionsSerializer(data=question_data)

            if serializer.is_valid():
                serializer.save()
                processed_data.append(serializer.data)
            else:
                errors = {
                    field: f"at row {i + 1}, column '{field.upper()}' - {error}"
                    for field, error in serializer.errors.items()
                }
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)

    return Response(processed_data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def saveDiagnosis(request):
    try:
        diagnosis_data = request.data.get("diagnosis_data", [])
        diagnosis_errors = []

        with transaction.atomic():
            for diagnosis in diagnosis_data:
                company_id = diagnosis.get("company")
                company = get_object_or_404(Company, pk=company_id)
                company.diagnosis_step = 2
                company.save()

                question_id = diagnosis.get("question")
                diagnosis_instance = CheckList.objects.filter(
                    company=company_id, question=question_id
                ).first()

                # Actualizar o crear nueva instancia de CheckList
                diagnosis["verify_document"] = blank_to_null(
                    diagnosis.get("verify_document")
                )
                diagnosis["observation"] = blank_to_null(diagnosis.get("observation"))

                if diagnosis["observation"] is None:
                    diagnosis["observation"] = "SIN OBSERVACIONES"
                serializer = CheckListSerializer(
                    instance=diagnosis_instance, data=diagnosis
                )
                diagnosis["is_articuled"] = bool(diagnosis.get("is_articuled", False))
                if serializer.is_valid():
                    serializer.save()
                else:
                    diagnosis_errors.append(serializer.errors)

            if diagnosis_errors:
                return Response(
                    {"diagnosis_errors": diagnosis_errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                diagnosis_data,
                status=status.HTTP_201_CREATED,
            )

    except Exception as ex:
        tb_str = traceback.format_exc()  # Formatear la traza del error
        return Response(
            {"error": str(ex), "traceback": tb_str},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def generateReport(request: Request):
    try:
        company_id = request.query_params.get("company")
        company: Company = Company.objects.get(pk=company_id)
        vehicle_questions = VehicleQuestions.objects.all()
        driver_questions = DriverQuestion.objects.all()
        fleet_data = Fleet.objects.filter(company=company_id)
        driver_data = Driver.objects.filter(company=company_id)

        totals_vehicles = Fleet.objects.filter(company=company_id).aggregate(
            total_owned=Sum("quantity_owned"),
            total_third_party=Sum("quantity_third_party"),
            total_arrended=Sum("quantity_arrended"),
            total_contractors=Sum("quantity_contractors"),
            total_intermediation=Sum("quantity_intermediation"),
            total_leasing=Sum("quantity_leasing"),
            total_renting=Sum("quantity_renting"),
        )
        total_quantity_driver = (
            Driver.objects.filter(company=company_id).aggregate(
                total_quantity=Sum("quantity")
            )["total_quantity"]
            or 0
        )

        # Extraer los valores y manejar casos en los que no haya registros
        total_owned = totals_vehicles["total_owned"] or 0
        total_third_party = totals_vehicles["total_third_party"] or 0
        total_arrended = totals_vehicles["total_arrended"] or 0
        total_contractors = totals_vehicles["total_contractors"] or 0
        total_intermediation = totals_vehicles["total_intermediation"] or 0
        total_leasing = totals_vehicles["total_leasing"] or 0
        total_renting = totals_vehicles["total_renting"] or 0

        # Calcular el total general sumando todos los totales parciales
        total_general_vehicles = (
            total_owned
            + total_third_party
            + total_arrended
            + total_contractors
            + total_intermediation
            + total_leasing
            + total_renting
        )
        template_path = os.path.join(
            settings.MEDIA_ROOT, "templates/DIAGNÓSTICO_BOLIVAR.docx"
        )
        doc = Document(template_path)
        month, year = get_current_month_and_year()
        variables_to_change = {
            "{{CRONOGRAMA}}": "#######",
            "{{SECUENCIA}}": "########",
            "{{COMPANY_NAME}}": company.name.upper(),
            "{{NIT}}": format_nit(company.nit),
            "{{MES_ANNO}}": f"{month.upper()} {year}",
            "{{CONSULTOR_NOMBRE}}": f"{company.consultor.first_name.upper()} {company.consultor.last_name.upper()}",
            "{{LICENCIA_SST}}": (
                company.consultor.licensia_sst
                if company.consultor.licensia_sst is not None
                else "SIN LICENCIA"
            ),
            "{{TABLA_DIAGNOSTICO}}": "",
            "{{PLANEAR_TABLE}}": "",
            "{{HACER_TABLE}}": "",
            "{{VERIFICAR_TABLE}}": "",
            "{{ACTUAR_TABLE}}": "",
            "{{MISIONALIDAD_ID}}": str(company.mission.id),
            "{{MISIONALIDAD_NAME}}": company.mission.name.upper(),
            "{{NIVEL_PESV}}": company.size.name.upper(),
            "{{QUANTITY_VEHICLES}}": str(total_general_vehicles),
            "{{QUANTITY_DRIVERS}}": str(total_quantity_driver),
            "{{CONCLUSIONES_TABLE}}": "",
            "{{GRAPHIC_BAR}}": "",
            "{{TOTALS_TABLE}}": "",
            "{{GRAPHIC_RADAR}}": "",
            "{{RECOMENDATIONS}}": "",
            "{{TOTAL_PERCENTAGE}}": "",
            "{{ARTICULED_TABLE}}": "",
            "{{TOTALS_ARTICULED}}": "",
        }

        # Datos de la tabla
        now = datetime.now()
        formatted_date = now.strftime("%d-%m-%Y")
        fecha = str(formatted_date)
        empresa = company.name
        nit = format_nit(company.nit)
        actividades = "Ejemplo Actividades"

        insert_table_after_placeholder(
            doc,
            "{{TABLA_DIAGNOSTICO}}",
            fecha,
            empresa,
            nit,
            actividades,
            vehicle_questions,
            fleet_data,
            driver_questions,
            driver_data,
            company.size.name.upper(),
            str(company.segment.name),
            f"{company.dependant} - {company.dependant_position}".upper(),
            company.acquired_certification or "",
        )

        datas_by_cycle = DiagnosisService.calculate_completion_percentage(company_id)
        filter_cycles = ["P", "H", "V", "A"]
        placeholders = {
            "P": "{{PLANEAR_TABLE}}",
            "H": "{{HACER_TABLE}}",
            "V": "{{VERIFICAR_TABLE}}",
            "A": "{{ACTUAR_TABLE}}",
        }

        for f_cycle in filter_cycles:
            filtered_data = [
                cycle for cycle in datas_by_cycle if cycle["cycle"] == f_cycle
            ]
            insert_table_results(doc, placeholders[f_cycle], filtered_data)

        insert_table_conclusion(
            doc, "{{CONCLUSIONES_TABLE}}", datas_by_cycle, company.size.name.upper()
        )
        insert_table_conclusion_articulated(
            doc, "{{ARTICULED_TABLE}}", datas_by_cycle, company.size.name.upper()
        )
        compliance_counts = (
            CheckList.objects.filter(company=company_id)
            .values("compliance_id")  # Agrupa por compliance_id
            .annotate(
                count=Count("id")
            )  # Cuenta la cantidad de registros en cada grupo
            .order_by("compliance_id")  # Ordena por compliance_id
        )

        # Inicializar variables para calcular el porcentaje general
        total_percentage = 0.0
        num_cycles = len(datas_by_cycle)
        for cycle in datas_by_cycle:
            total_percentage += round(cycle["cycle_percentage"], 2)
        general_percentage = round((total_percentage / num_cycles), 2)
        insert_table_conclusion_percentage(
            doc, "{{TOTALS_TABLE}}", compliance_counts, general_percentage
        )
        variables_to_change["{{TOTAL_PERCENTAGE}}"] = str(general_percentage)

        compliance_level = "NINGUNO"
        if general_percentage < 50:
            compliance_level = "BAJO"
        elif general_percentage >= 50 and general_percentage < 80:
            compliance_level = "MEDIO"
        elif general_percentage > 80:
            compliance_level = "ALTO"

        variables_to_change["{{COMPLIANCE_LEVEL}}"] = compliance_level
        # insert_image_after_placeholder(
        #     doc, "{{GRAPHIC_BAR}}", create_bar_chart(datas_by_cycle)
        # )
        insert_image_after_placeholder(
            doc, "{{GRAPHIC_RADAR }}", create_radar_chart(datas_by_cycle)
        )
        # Definir el orden deseado para los ciclos
        orden_ciclos = ["P", "H", "V", "A"]
        recomendaciones_agrupadas = (
            Recomendation.objects.select_related("requirement")
            .values("requirement__cycle", "name")
            .annotate(
                ciclo_order=Case(
                    *[
                        When(requirement__cycle=ciclo, then=Value(i))
                        for i, ciclo in enumerate(orden_ciclos)
                    ],
                    output_field=CharField(),
                )
            )
            .order_by("ciclo_order")
        )

        # Crear un diccionario para almacenar las recomendaciones agrupadas por cycle
        recomendaciones_por_cycle = defaultdict(list)

        for item in recomendaciones_agrupadas:
            cycle = item["requirement__cycle"]
            nombre_recomendacion = item["name"]
            recomendaciones_por_cycle[cycle].append(nombre_recomendacion)

        resultado_final = [
            {"cycle": cycle, "recomendations": recomendaciones}
            for cycle, recomendaciones in recomendaciones_por_cycle.items()
        ]

        insert_table_recomendations(doc, "{{RECOMENDATIONS}}", resultado_final)
        replace_placeholders_in_document(doc, variables_to_change)

        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        encoded_file = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return Response({"file": encoded_file}, status=status.HTTP_200_OK)
    except Exception as ex:
        tb_str = traceback.format_exc()  # Formatear la traza del error
        return Response(
            {"error": str(ex), "traceback": tb_str},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def uploadsRecomendations(request: Request):
    data = request.data.get("diagnosis_recomendations")
    if not data:
        return Response(
            {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Decodificar el base64
        decoded_file = base64.b64decode(data)
        excel_file = BytesIO(decoded_file)

        # Leer el archivo Excel y limpiar las filas con celdas vacías en la columna "RECOMENDACIÓN FRECUENTE"
        df = pd.read_excel(excel_file)
        df = df.dropna(subset=["RECOMENDACIÓN FRECUENTE"])

        # Filtrar filas con valores NaN en la columna "PASO"
        df = df[df["PASO"].notna()]

        # Procesar recomendaciones por paso
        recomendaciones_por_paso = {}
        for index, row in df.iterrows():
            paso = row["PASO"]
            recomendacion = row["RECOMENDACIÓN FRECUENTE"]

            # Extraer solo el texto principal eliminando viñetas y espacios en blanco al inicio y final
            recomendacion_texto = str(recomendacion).strip()

            # Verificar si la recomendación está vacía después de limpiar viñetas y espacios
            if not recomendacion_texto:
                continue

            # Eliminar viñetas como asteriscos (*) al inicio del texto
            if recomendacion_texto.startswith("·") or recomendacion_texto.startswith(
                "*"
            ):
                recomendacion_texto = re.sub(
                    r"^\s*[\*\-]\s*", "", recomendacion_texto
                ).strip()

            if paso not in recomendaciones_por_paso:
                recomendaciones_por_paso[paso] = []
            recomendaciones_por_paso[paso].append(recomendacion_texto)

        # Procesar cada paso y almacenar las recomendaciones en la base de datos
        processed_data = []
        with transaction.atomic():
            for paso, recomendaciones in recomendaciones_por_paso.items():
                try:
                    requisito = Diagnosis_Requirement.objects.get(step=paso)
                except ObjectDoesNotExist:
                    return Response(
                        {
                            "error": f"El requisito con paso '{paso}' no fue encontrado en la base de datos."
                        },
                        status=status.HTTP_404_NOT_FOUND,
                    )

                for recomendacion in recomendaciones:
                    recomendation_data = {
                        "requirement": requisito.id,
                        "name": recomendacion,
                    }
                    serializer = Recomendation_Serializer(data=recomendation_data)

                    if serializer.is_valid():
                        serializer.save()
                        processed_data.append(serializer.data)
                    else:
                        errors = {
                            field: f"at row {index + 1}, column '{field.upper()}' - {error}"
                            for field, error in serializer.errors.items()
                        }
                        return Response(errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(recomendaciones_por_paso, status=status.HTTP_201_CREATED)
