import traceback
from django.shortcuts import render
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from apps.sign.permissions import IsSuperAdmin, IsConsultor, IsAdmin
import logging
import base64
import pandas as pd
from io import BytesIO
from apps.diagnosis_requirement.models import Diagnosis_Requirement
from .models import Diagnosis_Questions, Diagnosis_Type, CheckList
from .serializers import Diagnosis_QuestionsSerializer, CheckListSerializer
from apps.company.models import (
    Company,
    VehicleQuestions,
    DriverQuestion,
    Fleet,
    Driver,
    Segments,
)
from utils.functionUtils import eliminar_tildes, blank_to_null
from django.db import transaction
from docx import Document
from io import BytesIO
import os
from django.conf import settings
from .helper import *
from django.db.models import Sum, F, FloatField, ExpressionWrapper, Count
import openpyxl
from openpyxl.chart import BarChart, Reference
from openpyxl.drawing.image import Image
from PIL import Image as PILImage
import matplotlib.pyplot as plt
from collections import defaultdict
from enum import Enum


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
                "step": step,
                "cycle": question.requirement.cycle,
                "requirement_name": question.requirement.name,
                "questions": [],
            }
        grouped_questions[step]["questions"].append(question)

    grouped_questions_list = [
        {
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
            "{{MISIONALIDAD_ID}}": str(company.dedication.id),
            "{{MISIONALIDAD_NAME}}": company.dedication.name.upper(),
            "{{NIVEL_PESV}}": company.company_size.name.upper(),
            "{{QUANTITY_VEHICLES}}": str(total_general_vehicles),
            "{{QUANTITY_DRIVERS}}": str(total_quantity_driver),
            "{{CONCLUSIONES_TABLE}}": "",
            "{{TOTALS_TABLE}}": "",
            "{{GRAPHIC_RADAR}}": "",
        }

        # Datos de la tabla

        fecha = "01-01-2024"
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
            company.company_size.name.upper(),
            str(company.segment.name),
            f"{company.dependant} - {company.dependant_position}".upper(),
            company.acquired_certification or "",
        )
        checklist_data = CheckList.objects.filter(company=company_id)
        size_name = eliminar_tildes(company.company_size.name)
        diagnosis_type = Diagnosis_Type.objects.filter(name=size_name).first()

        cycles = ["P", "H", "V", "A"]
        for cycle in cycles:
            diagnosis_questions = Diagnosis_Questions.objects.filter(
                diagnosis_type=diagnosis_type, cycle__iexact=cycle
            ).order_by("step")
            grouped_questions = {}
            for question in diagnosis_questions:
                if question.step not in grouped_questions:
                    grouped_questions[question.step] = {
                        "step": question.step,
                        "requirement_name": question.requirement.name,
                        "questions": [],
                    }
                grouped_questions[question.step]["questions"].append(question)

            # Define el placeholder para cada ciclo
            placeholders = {
                "P": "{{PLANEAR_TABLE}}",
                "H": "{{HACER_TABLE}}",
                "V": "{{VERIFICAR_TABLE}}",
                "A": "{{ACTUAR_TABLE}}",
            }
            insert_table_results(
                doc, placeholders[cycle], checklist_data, grouped_questions
            )

        diagnosis_questions = (
            Diagnosis_Questions.objects.filter(
                diagnosis_type=diagnosis_type, checklist__company_id=company_id
            )
            .values(
                "cycle",
                "step",
                "requirement__name",
            )
            .annotate(
                requirementName=F("requirement__name"),
                companyName=F("checklist__company__name"),
                sumatoria=Sum("checklist__obtained_value"),
                variable=Sum("variable_value"),
                percentage=ExpressionWrapper(
                    F("sumatoria") * 100.0 / F("variable"), output_field=FloatField()
                ),
            )
            .order_by("step")
        )
        insert_table_conclusion(doc, "{{CONCLUSIONES_TABLE}}", diagnosis_questions)

        # Agrupar por ciclo y calcular el porcentaje de cada fase
        grouped_by_cycle = {}
        sumatorias_by_cycle = {}
        for item in diagnosis_questions:
            cycle = item["cycle"].upper()
            if cycle not in grouped_by_cycle:
                grouped_by_cycle[cycle] = []
                sumatorias_by_cycle[cycle] = {"sumatoria": 0, "variable": 0}
            grouped_by_cycle[cycle].append(item)
            sumatorias_by_cycle[cycle]["sumatoria"] += item["sumatoria"]
            sumatorias_by_cycle[cycle]["variable"] += item["variable"]
        # Calcular el porcentaje de cada fase
        phase_percentages = []
        for cycle, items in grouped_by_cycle.items():
            total_sumatoria = sumatorias_by_cycle[cycle]["sumatoria"]
            total_variable = sumatorias_by_cycle[cycle]["variable"]
            phase_percentage = (
                round((total_sumatoria / total_variable) * 100)
                if total_variable > 0
                else 0
            )
            phase_percentages.append(phase_percentage)

        # Calcular el porcentaje general de las fases
        num_fases = len(phase_percentages)
        general_percentage = (
            round(sum(phase_percentages) / num_fases, 2) if num_fases > 0 else 0
        )
        compliance_counts = (
            CheckList.objects.filter(company=3)
            .values("compliance_id")  # Agrupa por compliance_id
            .annotate(
                count=Count("id")
            )  # Cuenta la cantidad de registros en cada grupo
            .order_by("compliance_id")  # Ordena por compliance_id
        )
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
        # Crear un archivo de Excel
        wb = openpyxl.Workbook()
        ws = wb.active
        # Agregar datos
        diagnosis_questions_list = list(diagnosis_questions)
        # Inicializa una lista para almacenar los datos
        data = [["Paso PESV", "Porcentage"]]

        # Recorre la lista y agrega cada step y su porcentaje a los datos
        for item in diagnosis_questions_list:
            step = item["step"]
            percentage = item["percentage"]
            data.append([step, percentage])

        for row in data:
            ws.append(row)

        # Crear un gráfico
        chart = BarChart()
        chart.title = "NIVEL DEL CUMPLIMIENTO DEL PESV"
        chart.x_axis.title = "Paso PESV"
        chart.y_axis.title = "Porcentage"

        data = Reference(ws, min_col=2, min_row=1, max_col=2, max_row=len(data))
        categories = Reference(ws, min_col=1, min_row=2, max_row=len(data))
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(categories)

        ws.add_chart(chart, "E5")

        # Guardar el archivo de Excel con el gráfico
        excel_file = "chart.xlsx"
        wb.save(excel_file)

        df = pd.read_excel(excel_file)
        # Crear un gráfico con matplotlib
        fig, ax = plt.subplots()
        df.plot(kind="bar", x="Paso PESV", y="Porcentage", ax=ax)
        ax.set_title("NIVEL DEL CUMPLIMIENTO DEL PESV")
        ax.set_xlabel("Paso PESV")
        ax.set_ylabel("Porcentage")
        # Guardar el gráfico como una imagen
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format="png")
        img_buffer.seek(0)

        # Guardar la imagen
        image_file = "chart.png"
        with open(image_file, "wb") as f:
            f.write(img_buffer.getvalue())

        labels = [
            "Paso 1",
            "Paso 1",
            "Paso 2",
            "Paso 3",
            "Paso 4",
            "Paso 4",
            "Paso 4",
            "Paso 4",
            "Paso 4",
            "Paso 4",
            "Paso 4",
            "Paso 4",
            "Paso 4",
            "Paso 4",
            "Paso 4",
            "Paso 4",
            "Paso 4",
            "Paso 4",
            "Paso 4",
            "Paso 4",
            "Paso 4",
            "Paso 4",
            "Paso 4",
            "Paso 4",
        ]  # Reemplaza con las etiquetas correctas
        values = [
            item["percentage"] for item in diagnosis_questions
        ]  # Asegúrate de tener los porcentajes

        radar_chart_img_buffer = create_radar_chart(
            values, labels, title="Nivel del Cumplimiento del PESV"
        )
        # Guarda el gráfico como archivo temporal
        radar_chart_image_file = "radar_chart.png"
        with open(radar_chart_image_file, "wb") as f:
            f.write(radar_chart_img_buffer.getvalue())

        insert_image_after_placeholder(doc, "{{GRAPHIC_BAR}}", image_file)
        insert_image_after_placeholder(doc, "{{GRAPHIC_RADAR}}", radar_chart_image_file)
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
