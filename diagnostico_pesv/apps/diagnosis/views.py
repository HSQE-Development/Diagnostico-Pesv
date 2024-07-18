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
from apps.company.models import Company
from utils.functionUtils import eliminar_tildes, blank_to_null
from django.db import transaction
from docx import Document
from io import BytesIO
import os
from django.conf import settings
from .helper import *


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def findQuestionsByCompanySize(request: Request):
    try:
        companId = request.query_params.get("company")
        group_by_step = (
            request.query_params.get("group_by_step", "false").lower() == "true"
        )
        company: Company = Company.objects.get(pk=companId)
        size_name = eliminar_tildes(company.company_size.name)
        diagnosis_type = Diagnosis_Type.objects.filter(name=size_name).first()
        if group_by_step:
            # Fetch and group questions by step including requirement.name
            diagnosis_questions = Diagnosis_Questions.objects.filter(
                diagnosis_type=diagnosis_type
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

            grouped_questions_list = [
                {
                    "step": group_data["step"],
                    "requirement_name": group_data["requirement_name"],
                    "questions": Diagnosis_QuestionsSerializer(
                        group_data["questions"], many=True, context={"request": request}
                    ).data,
                }
                for group_data in grouped_questions.values()
            ]

            return Response(grouped_questions_list, status=status.HTTP_200_OK)
        else:

            size_name = eliminar_tildes(company.company_size.name)
            diagnosis_types = Diagnosis_Type.objects.filter(name=size_name).first()
            diagnosisQuestions = Diagnosis_Questions.objects.filter(
                diagnosis_type=diagnosis_types
            ).order_by("step")
            serialized_questions = Diagnosis_QuestionsSerializer(
                diagnosisQuestions, many=True
            )
            return Response(serialized_questions.data, status=status.HTTP_200_OK)
    except Exception as ex:
        return Response(
            {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


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

    for idx, row in df.iterrows():
        try:
            requisito_name = row["REQUISITO"]
            requisito = Diagnosis_Requirement.objects.get(
                name=str(requisito_name).strip()
            )
        except Diagnosis_Requirement.DoesNotExist:
            return Response(
                {
                    "error": f"Requisito '{requisito_name}' not found at row {idx + 1}, column 'REQUISITO'"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            compliance_name = row["NIVEL"]
            compliance = Diagnosis_Type.objects.get(name=compliance_name)
        except Diagnosis_Type.DoesNotExist:
            return Response(
                {
                    "error": f"Type '{compliance_name}' not found at row {idx + 1}, column 'NIVEL'"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        question_data = {
            "cycle": row["CICLO"],
            "step": row["PASO PESV"],
            "requirement": requisito.id,
            "name": str(row["CRITERIO DE VERIFICACIÓN"]).strip(),
            "diagnosis_type": compliance.id,
            "variable_value": 50,
        }

        # Verificar si ya existe una entrada con los mismos valores
        existing_question = Diagnosis_Questions.objects.filter(
            cycle=question_data["cycle"],
            step=question_data["step"],
            requirement=question_data["requirement"],
            name=question_data["name"],
            diagnosis_type=question_data["diagnosis_type"],
        ).first()

        if existing_question:
            # Opcional: puedes actualizar el registro existente si es necesario
            serializer = Diagnosis_QuestionsSerializer(
                existing_question, data=question_data
            )
        else:
            serializer = Diagnosis_QuestionsSerializer(data=question_data)

        if serializer.is_valid():
            serializer.save()
            processed_data.append(serializer.data)
        else:
            errors = {
                field: f"at row {idx + 1}, column '{field.upper()}' - {error}"
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

        template_path = os.path.join(
            settings.MEDIA_ROOT, "templates/DIAGNÓSTICO_BOLIVAR.docx"
        )
        doc = Document(template_path)
        month, year = get_current_month_and_year()
        variables_to_change = {
            "{{CRONOGRAMA}}": "CRONOGRAMA AUTO",
            "{{SECUENCIA}}": "SECUENCIA AUTO",
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
        }

        # Datos de la tabla
        fecha = "01-01-2024"
        empresa = company.name
        nit = format_nit(company.nit)
        actividades = "Ejemplo Actividades"
        flotas = [
            {"nombre": "Flota 1", "cant1": 5, "cant2": 10},
            {"nombre": "Flota 2", "cant1": 7, "cant2": 15},
        ]

        insert_table_after_placeholder(
            doc, "{{TABLA_DIAGNOSTICO}}", fecha, empresa, nit, actividades, flotas
        )

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
