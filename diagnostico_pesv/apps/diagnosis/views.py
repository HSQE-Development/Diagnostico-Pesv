import platform
import traceback
import re
import base64
import pandas as pd
import os
import traceback
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    action,
)
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from apps.diagnosis_requirement.core.models import (
    Diagnosis_Requirement,
    Recomendation,
    WorkPlan_Recomendation,
)
from apps.diagnosis_requirement.infraestructure.serializers import (
    Recomendation_Serializer,
)
from .models import (
    Diagnosis_Questions,
    CheckList,
    Diagnosis,
    Checklist_Requirement,
    VehicleQuestions,
    DriverQuestion,
)
from .serializers import (
    Diagnosis_QuestionsSerializer,
    DiagnosisSerializer,
)
from apps.diagnosis_counter.serializers import FleetSerializer, DriverSerializer
from apps.company.models import Company, CompanySize
from apps.diagnosis_counter.models import Fleet, Driver, Diagnosis_Counter
from utils.functionUtils import blank_to_null
from django.db import transaction
from docx import Document
from io import BytesIO
from django.conf import settings
from .helper import *
from django.db.models import Sum, Count
from collections import defaultdict
from .services import DiagnosisService
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status, viewsets
from http import HTTPMethod
from apps.company.service import CompanyService
from .repositories import *
from .use_cases import *
from apps.diagnosis_requirement.application.use_cases import (
    DiagnosisRequirementUseCases,
)
from apps.diagnosis_requirement.infraestructure.repositories import (
    DiagnosisRequirementRepository,
)
from django.db.models import (
    Prefetch,
    OuterRef,
    Subquery,
    Q,
    Case,
    When,
    CharField,
    Value,
    F,
)
from apps.sign.models import User
from utils.constants import ComplianceIds
from collections import OrderedDict
from apps.corporate_group.repositories import CorporateGroupRepository
from rest_framework.exceptions import NotFound


def remove_invalid_requirements(diagnosis_id, valid_requirements):
    try:
        # Determinar el campo de Diagnosis_Requirement basado en type_id

        # Obtener los IDs de los requisitos válidos según el tipo
        valid_requirement_ids = set(valid_requirements.values_list("id", flat=True))
        # Obtener los IDs de los requisitos que están en Checklist_Requirement para el diagnóstico específico
        checklist_requirements_ids = Checklist_Requirement.objects.filter(
            diagnosis_id=diagnosis_id
        ).values_list("requirement_id", flat=True)
        # Identificar los requisitos en Checklist_Requirement que no son válidos según el tipo actual
        invalid_requirements = set(checklist_requirements_ids) - valid_requirement_ids
        # Eliminar los requisitos inválidos
        if invalid_requirements:
            with transaction.atomic():
                Checklist_Requirement.objects.filter(
                    diagnosis=diagnosis_id, requirement_id__in=invalid_requirements
                ).delete(hard=True)
                questions = Diagnosis_Questions.objects.filter(
                    requirement_id__in=invalid_requirements
                )
                for question in questions:
                    CheckList.objects.filter(
                        question_id=question.id, diagnosis=diagnosis_id
                    ).delete(hard=True)

    except CompanySize.DoesNotExist:
        print("CompanySize no encontrado.")
    except Exception as e:
        print(f"Ocurrió un error: {e}")


class DiagnosisViewSet(viewsets.ModelViewSet):
    queryset = Diagnosis.objects.all()
    serializer_class = DiagnosisSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    diagnosis_service = DiagnosisService
    company_service = CompanyService
    diagnosis_repository = DiagnosisRepository()
    diagnosis_requirement_repository = DiagnosisRequirementRepository()
    checklist_requirement_repository = CheckListRequirementRepository()
    checklist_repository = CheckListRepository()
    compliance_repository = ComplianceRepository()
    diagnosis_question = DiagnosisQuestionRepository()
    corporate_group_repository = CorporateGroupRepository()

    @action(detail=False)
    def findFleetsByCompanyId(self, request: Request):
        company_id = request.query_params.get("company")
        diagnosis_id = int(request.query_params.get("diagnosis", 0))
        corporate_group_id = request.query_params.get("corporate_group")

        # Validar y convertir el company_id y diagnosis_id
        if not company_id:
            return Response(
                {"error": "Company ID is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        if int(company_id) > 0:
            try:
                company = self.company_service.get_company(company_id)
            except Company.DoesNotExist:
                return Response(
                    {"error": "Company not found"}, status=status.HTTP_400_BAD_REQUEST
                )

        diagnosis = None
        try:
            if corporate_group_id:
                corporate_group = self.corporate_group_repository.get_by_id(
                    corporate_group_id
                )
            else:
                corporate_group = None

            use_case = GetUseCases(self.diagnosis_repository)

            if diagnosis_id > 0:
                diagnosis = use_case.get_by_id(diagnosis_id)
            else:
                if corporate_group:
                    diagnosis = use_case.get_by_corporate(corporate_group.id)
                else:
                    diagnosis = use_case.get_unfinalized_diagnosis_for_company(
                        company.id
                    )
            if diagnosis is not None:
                if int(company_id) > 0:
                    diagnosis_counter = Diagnosis_Counter.objects.filter(
                        diagnosis=diagnosis.id, company=company.id
                    ).first()

                    if diagnosis_counter:
                        fleets = Fleet.objects.filter(
                            diagnosis_counter=diagnosis_counter.id
                        )
                        serializer = FleetSerializer(fleets, many=True)
                    else:
                        serializer = FleetSerializer([], many=True)
                else:
                    serializer = FleetSerializer([], many=True)
            else:
                serializer = FleetSerializer([], many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response(
                {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False)
    def findDriversByCompanyId(self, request: Request):
        company_id = request.query_params.get("company")
        diagnosis_id = int(request.query_params.get("diagnosis", 0))
        corporate_group_id = request.query_params.get("corporate_group")
        # Validar y convertir el company_id y diagnosis_id
        if not company_id:
            return Response(
                {"error": "Company ID is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        if int(company_id) > 0:
            try:
                company = self.company_service.get_company(company_id)
            except Company.DoesNotExist:
                return Response(
                    {"error": "Company not found"}, status=status.HTTP_400_BAD_REQUEST
                )

        diagnosis = None
        try:
            if corporate_group_id:
                corporate_group = self.corporate_group_repository.get_by_id(
                    corporate_group_id
                )
            else:
                corporate_group = None

            use_case = GetUseCases(self.diagnosis_repository)
            if diagnosis_id > 0:
                diagnosis = use_case.get_by_id(diagnosis_id)
            else:
                if corporate_group:
                    diagnosis = use_case.get_by_corporate(corporate_group.id)
                else:
                    diagnosis = use_case.get_unfinalized_diagnosis_for_company(
                        company.id
                    )
            if diagnosis is not None:
                if int(company_id) > 0:
                    diagnosis_counter = Diagnosis_Counter.objects.filter(
                        diagnosis=diagnosis.id, company=company.id
                    ).first()
                    if diagnosis_counter:
                        drivers = Driver.objects.filter(
                            deleted_at=None, diagnosis_counter=diagnosis_counter.id
                        )
                        serializer = DriverSerializer(drivers, many=True)
                    else:
                        serializer = DriverSerializer([], many=True)
                else:
                    serializer = DriverSerializer([], many=True)
            else:
                serializer = DriverSerializer([], many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as ex:
            tb_str = traceback.format_exc()
            return Response(
                {"error": str(ex), "traceback": tb_str},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False)
    def findQuestionsByCompanySize(self, request: Request):
        try:
            company_id = request.query_params.get("company")
            get_use_case = GetUseCases(self.diagnosis_repository)

            group_by_step = (
                request.query_params.get("group_by_step", "false").lower() == "true"
            )
            diagnosis_id = int(request.query_params.get("diagnosis"))
            # Validar parámetro company_id
            if not company_id:
                return Response(
                    {"error": "El parámetro 'company' es requerido."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if diagnosis_id > 0:
                diagnosis = get_use_case.get_by_id(diagnosis_id)

                checklist_questions = CheckList.objects.filter(
                    diagnosis_id=diagnosis.id
                ).select_related("question", "compliance")
                if not checklist_questions:
                    questions_queryset = Diagnosis_Questions.objects.all()
                else:
                    question_ids = checklist_questions.values_list(
                        "question_id", flat=True
                    )
                    questions_queryset = Diagnosis_Questions.objects.filter(
                        id__in=question_ids
                    )
                # questions_queryset = CheckList.objects.filter(diagnosis_id=diagnosis_id)
            else:
                try:
                    company = self.company_service.get_company(company_id)
                except Company.DoesNotExist:
                    return Response(
                        {"error": "Empresa no encontrada."},
                        status=status.HTTP_404_NOT_FOUND,
                    )
                diagnosis = get_use_case.get_unfinalized_diagnosis_for_company(
                    company.id
                )
                questions_queryset = Diagnosis_Questions.objects.all()

            use_case_get_check_list = GetCheckListRequirementByDiagnosisId(
                self.checklist_requirement_repository, diagnosis.id
            )
            diagnosis_requirements = use_case_get_check_list.execute()

            # Obtener preguntas de diagnóstico
            requirements = Diagnosis_Requirement.objects.filter(
                id__in=diagnosis_requirements.values_list("requirement", flat=True)
            ).prefetch_related(Prefetch("requirements", queryset=questions_queryset))
            # diagnosis_questions = (
            #     Diagnosis_Questions.objects.filter(
            #         requirement__in=diagnosis_requirements.values_list(
            #             "requirement", flat=True
            #         )
            #     )
            #     .select_related("requirement")
            #     .order_by("requirement__step")
            # )

            if group_by_step:
                if diagnosis_id > 0:
                    grouped_questions = DiagnosisService.group_questions_by_step(
                        diagnosis_requirements,
                        requirements,
                        checklist_questions=checklist_questions,
                        include_compliance=True,
                    )
                else:
                    grouped_questions = DiagnosisService.group_questions_by_step(
                        diagnosis_requirements, requirements
                    )

                return Response(grouped_questions, status=status.HTTP_200_OK)
            # else:
            #     serialized_questions = Diagnosis_QuestionsSerializer(
            #         diagnosis_questions, many=True
            #     )
            #     return Response(serialized_questions.data, status=status.HTTP_200_OK)

        except Exception as ex:
            # logger.error(f"Error en findQuestionsByCompanySize: {str(ex)}")
            tb_str = traceback.format_exc()
            return Response(
                {"error": str(ex), "traceback": tb_str},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=[HTTPMethod.PATCH])
    def update_diagnosis(self, request: Request):
        diagnosis_id = request.query_params.get("diagnosis")
        type_id = request.data.get("type")
        observation = request.data.get("observation")
        try:
            with transaction.atomic():
                get_use_case = GetUseCases(self.diagnosis_repository)
                diagnosis = get_use_case.get_by_id(diagnosis_id)

                if type_id:
                    typeObject = CompanySize.objects.get(pk=type_id)
                    diagnosis.type = typeObject
                    # Determinar el campo de Diagnosis_Requirement basado en type_id
                    if typeObject.id == 1:
                        requirements = Diagnosis_Requirement.objects.filter(basic=True)
                    elif typeObject.id == 2:
                        requirements = Diagnosis_Requirement.objects.filter(
                            standard=True
                        )
                    elif typeObject.id == 3:
                        requirements = Diagnosis_Requirement.objects.filter(
                            advanced=True
                        )
                    else:
                        raise ValueError("Invalid type_id provided.")

                    checklist_requirements_ids = Checklist_Requirement.objects.filter(
                        diagnosis=diagnosis.id
                    ).values_list("requirement_id", flat=True)

                    existing_requirement_ids = set(
                        requirements.values_list("id", flat=True)
                    )
                    checklist_requirement_ids = set(checklist_requirements_ids)
                    missing_requirements = (
                        existing_requirement_ids - checklist_requirement_ids
                    )
                    get_compliance = GetComplianceById(self.compliance_repository, 2)
                    compliance = get_compliance.execute()

                    remove_invalid_requirements(
                        diagnosis_id=diagnosis.id, valid_requirements=requirements
                    )

                    for requirement_id in missing_requirements:
                        Checklist_Requirement.objects.create(
                            diagnosis=diagnosis,
                            requirement_id=requirement_id,
                            compliance=compliance,  # Ajusta el valor según sea necesario
                            observation=None,  # Ajusta el valor según sea necesario
                        )

                        questions = Diagnosis_Questions.objects.filter(
                            requirement_id=requirement_id
                        )
                        for question in questions:
                            CheckList.objects.create(
                                question=question,
                                compliance=compliance,
                                diagnosis=diagnosis,
                                obtained_value=0,
                            )
                    diagnosis.diagnosis_step = 1

                if observation:
                    diagnosis.observation = observation

                diagnosis.save()

                serializer = DiagnosisSerializer(diagnosis)
                return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response(
                {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=[HTTPMethod.POST])
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

    @action(detail=False, methods=[HTTPMethod.POST])
    def save_count_for_company_in_corporate(self, request: Request):
        company_id = request.data.get("company")
        corporate_id = request.data.get("corporate")
        vehicle_data = request.data.get("vehicleData", [])
        driver_data = request.data.get("driverData", [])
        diagnosis_data = {
            "company": None,
            "date_elabored": None,
            "consultor": None,
            "corporate_group": corporate_id,
            "is_for_corporate_group": True,
        }
        diagnosis_serializer = DiagnosisSerializer(data=diagnosis_data)
        if diagnosis_serializer.is_valid():
            try:
                with transaction.atomic():
                    company = self.company_service.get_company(company_id)
                    existing_diagnosis = Diagnosis.objects.filter(
                        corporate_group=corporate_id, is_finalized=False
                    ).first()
                    diagnosis_counter = None

                    if existing_diagnosis:
                        diagnosis = existing_diagnosis
                    else:
                        create_diagnosis = CreateDiagnosis(
                            self.diagnosis_repository,
                            diagnosis_serializer.validated_data,
                            consultor=None,
                        )
                        diagnosis = create_diagnosis.execute()
                        diagnosis.in_progress = True

                    exist_counter = Diagnosis_Counter.objects.filter(
                        company=company, diagnosis=diagnosis
                    ).first()
                    if exist_counter:
                        diagnosis_counter = exist_counter
                    else:
                        diagnosis_counter = Diagnosis_Counter(
                            company=company, diagnosis=diagnosis
                        )
                        diagnosis_counter.save()

                    total_vehicles, vehicle_errors = (
                        self.diagnosis_service.process_vehicle_data(
                            diagnosis_counter.id, vehicle_data
                        )
                    )
                    total_drivers, driver_errors = (
                        self.diagnosis_service.process_driver_data(
                            diagnosis_counter.id, driver_data
                        )
                    )
                    size_and_type = self.company_service.update_company_size(
                        company, total_vehicles, total_drivers
                    )
                    diagnosis_counter.size = size_and_type
                    diagnosis.type = None
                    diagnosis.diagnosis_step = 1
                    diagnosis.save()
                    diagnosis_counter.save()

                    return self.diagnosis_service.build_success_response(
                        vehicle_data, driver_data, diagnosis
                    )

            except Company.DoesNotExist:
                return Response(
                    {"error": "Company not found."}, status=status.HTTP_404_NOT_FOUND
                )
            except Exception as ex:
                tb_str = traceback.format_exc()
                return Response(
                    {"error": str(ex), "traceback": tb_str},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        return Response(diagnosis_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=[HTTPMethod.POST])
    def init_diagnosis_corporate(self, request: Request):
        try:
            use_case = GetUseCases(self.diagnosis_repository)
            corporate_id = request.data.get("corporate")
            if not corporate_id:
                return Response(
                    {"error": "El id del grupo empresarial es obligatiorio"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            corporate_group = self.corporate_group_repository.get_by_id(corporate_id)
            if not corporate_group:
                return Response(
                    {"error": "El grupo empresarial no existe"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            diagnosis = use_case.get_by_corporate(corporate_group.id)

            company_totals = (
                Diagnosis_Counter.objects.filter(diagnosis=diagnosis.id)
                .values("company")
                .annotate(
                    total_vehicles=Sum(
                        F("fleet__quantity_owned")
                        + F("fleet__quantity_third_party")
                        + F("fleet__quantity_arrended")
                        + F("fleet__quantity_contractors")
                        + F("fleet__quantity_intermediation")
                        + F("fleet__quantity_leasing")
                        + F("fleet__quantity_renting")
                        + F("fleet__quantity_employees")
                    ),
                    total_drivers=Sum("driver__quantity"),
                )
            )
            highest_company = None
            highest_size = None
            for company_total in company_totals:
                company_id = company_total["company"]
                company = Company.objects.get(id=company_id)
                total_vehicles = company_total["total_vehicles"] or 0
                total_drivers = company_total["total_drivers"] or 0
                size_and_type = self.company_service.update_company_size(
                    company, total_vehicles, total_drivers
                )
                # Comparar con el tamaño más alto encontrado hasta ahora
                if highest_size is None or size_and_type.id > highest_size:
                    highest_size = size_and_type.id
                    highest_company = company

            corporate_group.nit = highest_company.nit
            company_size = CompanySize.objects.get(id=highest_size)
            diagnosis.type = company_size

            diagnosis_requirement_use_case = DiagnosisRequirementUseCases(
                self.diagnosis_requirement_repository
            )
            requirements = diagnosis_requirement_use_case.get_diagnosis_requirements_by_company_size(
                diagnosis.type.id
            )

            get_compliance = GetComplianceById(self.compliance_repository, 2)
            compliance_default = get_compliance.execute()

            for requirement in requirements:
                existing_checklist_requirement = (
                    use_case.get_by_diagnosis_and_requirement(diagnosis, requirement)
                )
                compliance = (
                    existing_checklist_requirement.compliance
                    if existing_checklist_requirement
                    else compliance_default
                )
                data = {
                    "diagnosis": diagnosis,
                    "compliance": compliance,
                    "requirement": requirement,
                }
                create = CreateOrUpdateChecklistRequirement(
                    self.checklist_requirement_repository, data
                )
                create.execute()

            corporate_group.save()
            diagnosis.save()
            serializer = DiagnosisSerializer(diagnosis)
            return Response(serializer.data)
        except Exception as ex:
            return Response(
                {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=[HTTPMethod.POST])
    def saveAnswerCuestions(self, request: Request):
        consultor_id = request.data.get("consultor")
        company_id = request.data.get("company")
        vehicle_data = request.data.get("vehicleData", [])
        driver_data = request.data.get("driverData", [])
        diagnosis_data = {
            "company": company_id,
            "date_elabored": None,
            "consultor": consultor_id,
        }
        diagnosis_serializer = DiagnosisSerializer(data=diagnosis_data)

        if diagnosis_serializer.is_valid():
            try:
                with transaction.atomic():
                    company = self.company_service.get_company(company_id)
                    consultor = User.objects.get(id=consultor_id)
                    get_use_case = GetUseCases(self.diagnosis_repository)
                    # existing_diagnosis = get_use_case.get_diagnosis_by_date_elabored(today)
                    existing_diagnosis = (
                        get_use_case.get_unfinalized_diagnosis_for_company(company.id)
                    )
                    # Se debe finalizar cuando se cree un nuevo diagnostico no cuando se responda!!!
                    existing_diagnosis.is_finalized = True
                    update_diagnosis_use_case = UpdateDiagnosis(
                        self.diagnosis_repository, existing_diagnosis
                    )
                    update_diagnosis_use_case.execute()

                    create_diagnosis = CreateDiagnosis(
                        self.diagnosis_repository,
                        diagnosis_serializer.validated_data,
                        consultor,
                    )
                    diagnosis = create_diagnosis.execute()

                    new_diagnosis_count = Diagnosis_Counter(
                        company=company, diagnosis=diagnosis
                    )
                    new_diagnosis_count.save()

                    total_vehicles, vehicle_errors = (
                        self.diagnosis_service.process_vehicle_data(
                            new_diagnosis_count.id, vehicle_data
                        )
                    )
                    total_drivers, driver_errors = (
                        self.diagnosis_service.process_driver_data(
                            new_diagnosis_count.id, driver_data
                        )
                    )
                    size_and_type = self.company_service.update_company_size(
                        company, total_vehicles, total_drivers
                    )
                    company.size = size_and_type
                    diagnosis.type = size_and_type
                    diagnosis.diagnosis_step = 1
                    diagnosis.save()

                    diagnosis_requirement_use_case = DiagnosisRequirementUseCases(
                        self.diagnosis_requirement_repository
                    )
                    requirements = diagnosis_requirement_use_case.get_diagnosis_requirements_by_company_size(
                        diagnosis.type.id
                    )
                    get_compliance = GetComplianceById(self.compliance_repository, 2)
                    compliance = get_compliance.execute()
                    for requirement in requirements:
                        data = {
                            "diagnosis": diagnosis,
                            "compliance": compliance,
                            "requirement": requirement,
                        }
                        create = CreateChecklistRequirement(
                            self.checklist_requirement_repository, data
                        )
                        create.execute()

                    if vehicle_errors or driver_errors:
                        return self.diagnosis_service.build_error_response(
                            vehicle_errors, driver_errors
                        )

                    return self.diagnosis_service.build_success_response(
                        vehicle_data, driver_data, diagnosis
                    )

            except Company.DoesNotExist:
                return Response(
                    {"error": "Company not found."}, status=status.HTTP_404_NOT_FOUND
                )
            except Exception as ex:
                tb_str = traceback.format_exc()
                return Response(
                    {"error": str(ex), "traceback": tb_str},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        return Response(diagnosis_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=[HTTPMethod.POST])
    def saveDiagnosis(self, request: Request):
        try:
            diagnosis_data = request.data.get("diagnosis_data")
            diagnosisDto = diagnosis_data["diagnosisDto"]
            diagnosisRequirementDto = diagnosis_data["diagnosisRequirementDto"]
            company_id = diagnosis_data["company"]
            consultor_id = diagnosis_data["consultor"]
            diagnosis_id = int(request.query_params.get("diagnosis"))

            try:
                consultor = User.objects.get(pk=consultor_id)
            except User.DoesNotExist:
                return Response(
                    {"error": "Consultor no encontrada."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            get_use_case = GetUseCases(self.diagnosis_repository)
            if diagnosis_id > 0:
                diagnosis = get_use_case.get_by_id(diagnosis_id)
            else:
                try:
                    company = self.company_service.get_company(company_id)
                except Company.DoesNotExist:
                    return Response(
                        {"error": "Empresa no encontrada."},
                        status=status.HTTP_404_NOT_FOUND,
                    )
                diagnosis = get_use_case.get_unfinalized_diagnosis_for_company(
                    company.id
                )
            with transaction.atomic():
                questions_to_create = []
                questions_to_update = []

                if not diagnosis.consultor:
                    diagnosis.consultor = consultor
                    diagnosis.save()
                for diagnosis_questions in diagnosisDto:
                    question_id = diagnosis_questions["question"]

                    get_question = GetQuestionById(self.diagnosis_question, question_id)
                    question = get_question.execute()
                    get_checklist_by_question_and_diagnosis = (
                        GetCheckListByQuestionIdAndDiagnosisId(
                            self.checklist_repository, question.id, diagnosis.id
                        )
                    )
                    existing_checklist_by_question_and_diagnosis = (
                        get_checklist_by_question_and_diagnosis.execute()
                    )

                    get_compliance = GetComplianceById(
                        self.compliance_repository,
                        diagnosis_questions["compliance"],
                    )
                    compliance = get_compliance.execute()

                    newObservation = blank_to_null(diagnosis_questions["observation"])
                    if newObservation is None:
                        newObservation = "SIN OBSERVACIONES"
                    newVerifyDocs = blank_to_null(
                        diagnosis_questions["verify_document"]
                    )

                    if existing_checklist_by_question_and_diagnosis:
                        existing_checklist_by_question_and_diagnosis.compliance = (
                            compliance
                        )
                        existing_checklist_by_question_and_diagnosis.observation = (
                            newObservation
                        )
                        existing_checklist_by_question_and_diagnosis.obtained_value = (
                            diagnosis_questions["obtained_value"]
                        )
                        existing_checklist_by_question_and_diagnosis.is_articuled = (
                            diagnosis_questions["is_articuled"]
                        )
                        existing_checklist_by_question_and_diagnosis.verify_document = (
                            newVerifyDocs
                        )
                        questions_to_update.append(
                            existing_checklist_by_question_and_diagnosis
                        )

                    else:
                        new_Check_list = CheckList(
                            compliance=compliance,
                            observation=newObservation,
                            obtained_value=diagnosis_questions["obtained_value"],
                            is_articuled=diagnosis_questions["is_articuled"],
                            verify_document=diagnosis_questions["verify_document"],
                            diagnosis=diagnosis,
                            question=question,
                        )
                        questions_to_create.append(new_Check_list)

                checklists_to_create = []
                checklists_to_update = []
                for diagnosis_requirement in diagnosisRequirementDto:
                    req_id = diagnosis_requirement["requirement"]

                    get_cheklist_req_by_id_and_diagnosis = (
                        GetCheckListRequirementByIdAndDiagnosisId(
                            self.checklist_requirement_repository,
                            int(req_id),
                            diagnosis.id,
                        )
                    )
                    existing_cheklist_req_by_id_and_diagnosis = (
                        get_cheklist_req_by_id_and_diagnosis.execute()
                    )
                    get_compliance = GetComplianceById(
                        self.compliance_repository,
                        diagnosis_requirement["compliance"],
                    )
                    compliance = get_compliance.execute()

                    use_case_get_requirement = GetRequirementById(
                        self.checklist_requirement_repository, int(req_id)
                    )
                    requirement = use_case_get_requirement.execute()

                    if existing_cheklist_req_by_id_and_diagnosis:
                        existing_cheklist_req_by_id_and_diagnosis.observation = (
                            diagnosis_requirement["observation"]
                        )
                        existing_cheklist_req_by_id_and_diagnosis.compliance = (
                            compliance
                        )
                        checklists_to_update.append(
                            existing_cheklist_req_by_id_and_diagnosis
                        )
                    else:
                        new_checklist = Checklist_Requirement(
                            diagnosis=diagnosis,
                            compliance=compliance,
                            requirement=requirement,
                            # Rellenar otros campos según sea necesario
                        )
                        checklists_to_create.append(new_checklist)

                # Actualizar los requerimientos
                if checklists_to_update:
                    massive_update = CheckListRequirementMassiveUpdate(
                        self.checklist_requirement_repository, checklists_to_update
                    )
                    massive_update.execute()

                # if checklists_to_create:
                #     massive_create = CheckListRequirementMassiveCreate(
                #         self.checklist_requirement_repository, checklists_to_create
                #     )
                #     massive_create.execute()

                # Actualizar las preguntas
                if questions_to_update:
                    massive_update = CheckListMassiveUpdate(
                        self.checklist_repository, questions_to_update
                    )
                    massive_update.execute()

                if questions_to_create:
                    massive_create = CheckListMassiveCreate(
                        self.checklist_repository, questions_to_create
                    )
                    massive_create.execute()

                if not diagnosis.diagnosis_step == 2:
                    diagnosis.diagnosis_step = 2
                if consultor.id != diagnosis.consultor.id:
                    diagnosis.consultor = consultor
                diagnosis.in_progress = False
                diagnosis.save()

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

    @action(detail=False, methods=[HTTPMethod.POST])
    def generateReport(self, request: Request):

        # Solo intenta importar pythoncom si el sistema operativo es Windows
        if platform.system() == "Windows":
            try:
                import pythoncom

                pythoncom.CoInitialize()
            except Exception as e:
                print(f"Error al inicializar COM: {e}")
        try:
            company_id = request.query_params.get("company")
            schedule = request.query_params.get("schedule")
            sequence = request.query_params.get("sequence")
            diagnosis_id = int(request.query_params.get("diagnosis"))
            format_to_save = request.query_params.get(
                "format_to_save"
            )  # Default to 'word'
            company = None

            if int(company_id) > 0:
                try:
                    company = self.company_service.get_company(company_id)
                except Company.DoesNotExist:
                    return Response(
                        {"error": "Empresa no encontrada."},
                        status=status.HTTP_404_NOT_FOUND,
                    )

            get_use_case = GetUseCases(self.diagnosis_repository)
            if int(diagnosis_id) > 0:
                diagnosis = get_use_case.get_by_id(diagnosis_id)
            else:
                diagnosis = get_use_case.get_unfinalized_diagnosis_for_company(
                    company.id
                )

            diagnosis.schedule = schedule
            diagnosis.sequence = sequence
            diagnosis.save()
            vehicle_questions = VehicleQuestions.objects.all()
            driver_questions = DriverQuestion.objects.all()

            template_path = os.path.join(
                settings.MEDIA_ROOT, "templates/DIAGNÓSTICO_BOLIVAR.docx"
            )
            doc = Document(template_path)
            month, year = get_current_month_and_year()
            # Datos de la tabla
            now = datetime.now()
            formatted_date = now.strftime("%d-%m-%Y")
            fecha = str(formatted_date)

            variables_to_change = {
                "{{CRONOGRAMA}}": diagnosis.schedule,
                "{{SECUENCIA}}": diagnosis.sequence,
                "{{MES_ANNO}}": f"{month.upper()} {year}",
                "{{CONSULTOR_NOMBRE}}": f"{diagnosis.consultor.first_name.upper()} {diagnosis.consultor.last_name.upper()}",
                "{{LICENCIA_SST}}": (
                    diagnosis.consultor.licensia_sst
                    if diagnosis.consultor.licensia_sst is not None
                    else "SIN LICENCIA"
                ),
                "{{MODE_PESV}}": diagnosis.mode_ejecution,
                "{{TABLA_DIAGNOSTICO}}": "",
                "{{SUMMARY_NOT_IN_CORPORATE_GROUPS}}": "",
                "{{PLANEAR_TABLE}}": "",
                "{{HACER_TABLE}}": "",
                "{{VERIFICAR_TABLE}}": "",
                "{{ACTUAR_TABLE}}": "",
                # "{{MISIONALIDAD_ID}}": str(company.mission.id),
                # "{{MISIONALIDAD_NAME}}": company.mission.name.upper(),
                # "{{NIVEL_PESV}}": diagnosis.type.name.upper(),
                # "{{QUANTITY_VEHICLES}}": str(total_general_vehicles),
                # "{{QUANTITY_DRIVERS}}": str(total_quantity_driver),
                "{{CONCLUSIONES_TABLE}}": "",
                "{{GRAPHIC_BAR}}": "",
                "{{TOTALS_TABLE}}": "",
                "{{GRAPHIC_RADAR}}": "",
                "{{RECOMENDATIONS}}": "",
                "{{PERCENTAGE_TOTAL}}": "",
                "{{ARTICULED_TABLE}}": "",
                "{{TOTALS_ARTICULED}}": "",
            }

            if diagnosis.is_for_corporate_group:
                diagnosis_counter = Diagnosis_Counter.objects.filter(
                    diagnosis=diagnosis
                )
                counter_ids = diagnosis_counter.values_list("id", flat=True)
                fleet_totals_by_company = (
                    Fleet.objects.filter(diagnosis_counter__in=counter_ids)
                    .select_related("diagnosis_counter__company")
                    .annotate(
                        total_owned=Sum("quantity_owned"),
                        total_third_party=Sum("quantity_third_party"),
                        total_arrended=Sum("quantity_arrended"),
                        total_contractors=Sum("quantity_contractors"),
                        total_intermediation=Sum("quantity_intermediation"),
                        total_leasing=Sum("quantity_leasing"),
                        total_renting=Sum("quantity_renting"),
                    )
                    .order_by("diagnosis_counter__company")
                )
                # Agrupar los datos de Driver por empresa
                driver_totals_by_company = (
                    Driver.objects.filter(diagnosis_counter__in=counter_ids)
                    .select_related("diagnosis_counter__company")
                    .annotate(total_quantity=Sum("quantity"))
                    .order_by("diagnosis_counter__company")
                )
                processed_companies = set()
                company_totals = []

                for fleet_totals in fleet_totals_by_company:
                    company = fleet_totals.diagnosis_counter.company
                    if company in processed_companies:
                        continue
                    count_size = fleet_totals.diagnosis_counter.size
                    driver_totals = next(
                        (
                            d
                            for d in driver_totals_by_company
                            if d.diagnosis_counter.company == company
                        ),
                        None,
                    )

                    # Extraer y manejar casos en los que no haya registros
                    total_owned = fleet_totals.total_owned or 0
                    total_third_party = fleet_totals.total_third_party or 0
                    total_arrended = fleet_totals.total_arrended or 0
                    total_contractors = fleet_totals.total_contractors or 0
                    total_intermediation = fleet_totals.total_intermediation or 0
                    total_leasing = fleet_totals.total_leasing or 0
                    total_renting = fleet_totals.total_renting or 0
                    total_quantity_driver = (
                        driver_totals.total_quantity if driver_totals else 0
                    )

                    # Calcular el total general de vehículos para la empresa
                    total_general_vehicles = (
                        total_owned
                        + total_third_party
                        + total_arrended
                        + total_contractors
                        + total_intermediation
                        + total_leasing
                        + total_renting
                    )

                    # Agregar la información completa de la empresa y los totales a la lista de resultados agrupados
                    company_totals.append(
                        {
                            "company": company,  # Aquí accedes a todos los campos de Company
                            "count_size": count_size,  # Aquí accedes a todos los campos de Company
                            "total_owned": total_owned,
                            "total_third_party": total_third_party,
                            "total_arrended": total_arrended,
                            "total_contractors": total_contractors,
                            "total_intermediation": total_intermediation,
                            "total_leasing": total_leasing,
                            "total_renting": total_renting,
                            "total_general_vehicles": total_general_vehicles,
                            "total_quantity_driver": total_quantity_driver,
                        }
                    )
                    processed_companies.add(company)

                variables_to_change["{{COMPANY_NAME}}"] = (
                    diagnosis.corporate_group.name.upper()
                )
                variables_to_change["{{NIT}}"] = format_nit(
                    diagnosis.corporate_group.nit
                )
                insert_tables_for_companies(
                    doc,
                    "{{TABLA_DIAGNOSTICO}}",
                    company_totals,
                    fecha,
                    vehicle_questions,
                    driver_questions,
                    Fleet=Fleet,
                    Driver=Driver,
                    diagnosis=diagnosis,
                )
            else:

                diagnosis_counter = Diagnosis_Counter.objects.filter(
                    diagnosis=diagnosis, company=company
                ).first()

                fleet_data = Fleet.objects.filter(
                    diagnosis_counter=diagnosis_counter.id
                )
                driver_data = Driver.objects.filter(
                    diagnosis_counter=diagnosis_counter.id
                )

                totals_vehicles = Fleet.objects.filter(
                    diagnosis_counter=diagnosis_counter.id
                ).aggregate(
                    total_owned=Sum("quantity_owned"),
                    total_third_party=Sum("quantity_third_party"),
                    total_arrended=Sum("quantity_arrended"),
                    total_contractors=Sum("quantity_contractors"),
                    total_intermediation=Sum("quantity_intermediation"),
                    total_leasing=Sum("quantity_leasing"),
                    total_renting=Sum("quantity_renting"),
                )
                total_quantity_driver = (
                    Driver.objects.filter(
                        diagnosis_counter=diagnosis_counter.id
                    ).aggregate(total_quantity=Sum("quantity"))["total_quantity"]
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

                nit = format_nit(company.nit)
                summary = f"De acuerdo con la información anterior, se identifica que la empresa se encuentra en misionalidad {company.mission.id} | {company.mission.name.upper()} y que cuenta con {total_general_vehicles} vehículos propiedad de la empresa y {total_quantity_driver} personas con rol de conductor, por lo tanto, se define que debe diseñar e implementar un plan estratégico de seguridad vial “{diagnosis.type.name.upper()}”."

                variables_to_change["{{COMPANY_NAME}}"] = company.name.upper()
                variables_to_change["{{NIT}}"] = nit
                variables_to_change["{{SUMMARY_NOT_IN_CORPORATE_GROUPS}}"] = summary

                empresa = company.name
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
                    diagnosis.type.name.upper(),
                    str(company.segment.name),
                    f"{company.dependant} - {company.dependant_position}".upper(),
                    company.acquired_certification or "",
                )

            # De aqui para adelante todo sera igual para el informe ya que se maneja directamente el id del diagnostico
            datas_by_cycle = DiagnosisService.calculate_completion_percentage(
                diagnosis.id
            )

            data_completion_percentage = (
                DiagnosisService.calculate_completion_percentage_data(diagnosis.id)
            )
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
                doc,
                "{{CONCLUSIONES_TABLE}}",
                datas_by_cycle,
                diagnosis.type.name.upper(),
            )
            # insert_table_conclusion_articulated(
            #     doc, "{{ARTICULED_TABLE}}", datas_by_cycle, company.size.name.upper()
            # )
            insert_table_conclusion_percentage_articuled(
                doc, "{{TOTALS_ARTICULED}}", datas_by_cycle
            )
            compliance_counts = Compliance.objects.annotate(
                count=Subquery(
                    CheckList.objects.filter(
                        diagnosis=diagnosis.id, compliance_id=OuterRef("pk")
                    )
                    .values("compliance_id")
                    .annotate(count=Count("id"))
                    .values("count")
                )
            ).order_by(
                "id"
            )  # Ordena por compliance_id

            insert_table_conclusion_percentage(
                doc,
                "{{TOTALS_TABLE}}",
                compliance_counts,
                data_completion_percentage,
            )

            compliance_level = "NINGUNO"
            if data_completion_percentage < 50:
                compliance_level = "BAJO"
            elif data_completion_percentage >= 50 and data_completion_percentage < 80:
                compliance_level = "MEDIO"
            elif data_completion_percentage > 80:
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

            # Filtrar Checklist_Requirements por diagnosis_id
            checklist_requirements = Checklist_Requirement.objects.filter(
                diagnosis=diagnosis.id,
                compliance__in=[
                    ComplianceIds.NO_CUMPLE.value,
                    ComplianceIds.NO_APLICA.value,
                ],
            ).select_related("requirement")

            requirement_ids = checklist_requirements.values_list(
                "requirement_id", flat=True
            )

            observaciones_por_requirement = {
                checklist.requirement_id: f"PASO {checklist.requirement.step}: {checklist.observation}"
                for checklist in checklist_requirements
                if checklist.compliance.id == ComplianceIds.NO_APLICA.value
            }
            # Construir la condición para las recomendaciones basadas en el tipo de diagnóstico
            if diagnosis.type.id == 1:  # Supongamos que 1 es 'basic'
                filtro_tipo = Q(basic=True)
            elif diagnosis.type.id == 2:  # Supongamos que 2 es 'standard'
                filtro_tipo = Q(standard=True)
            elif diagnosis.type.id == 3:  # Supongamos que 3 es 'advanced'
                filtro_tipo = Q(advanced=True)
            else:
                filtro_tipo = Q()  # Manejo de error o tipo desconocido

            # Obtener observaciones y recomendaciones asociadas a los requirements de esos Checklist_Requirements
            recomendaciones = Recomendation.objects.filter(
                (filtro_tipo | Q(all=True)) & Q(requirement_id__in=requirement_ids)
            ).select_related("requirement")

            # Crear un diccionario para almacenar las recomendaciones agrupadas por cycle
            resultados_por_cycle = defaultdict(list)
            for recomendacion in recomendaciones:
                if recomendacion.name != None:
                    cycle = recomendacion.requirement.cycle
                    nombre_recomendacion = (
                        f"PASO {recomendacion.requirement.step} - {recomendacion.name}"
                    )

                    # Crear una clave única para evitar duplicados
                    observation = observaciones_por_requirement.get(
                        recomendacion.requirement_id, ""
                    )

                    resultados_por_cycle[cycle].append(
                        {
                            "recomendacion": nombre_recomendacion,
                            "observation": observation,
                        }
                    )

            # Convertir los resultados agrupados en una lista final
            resultado_final = [
                {"cycle": cycle, "recomendations": recomendacion}
                for cycle, recomendacion in resultados_por_cycle.items()
            ]
            variables_to_change["{{PERCENTAGE_TOTAL}}"] = str(
                data_completion_percentage
            )
            insert_table_recomendations(doc, "{{RECOMENDATIONS}}", resultado_final)

            replace_placeholders_in_document(doc, variables_to_change)

            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            word_file_content = buffer.getvalue()
            if format_to_save == "pdf":
                pdf_file_content = convert_docx_to_pdf_base64(word_file_content)
                encoded_file = pdf_file_content
            else:  # Default to Word
                file_content = word_file_content
                encoded_file = base64.b64encode(file_content).decode("utf-8")

            return Response({"file": encoded_file}, status=status.HTTP_200_OK)
        except Exception as ex:
            tb_str = traceback.format_exc()  # Formatear la traza del error
            return Response(
                {"error": str(ex), "traceback": tb_str},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=[HTTPMethod.POST])
    def generateWorkPlan(self, request: Request):
        if platform.system() == "Windows":
            try:
                import pythoncom

                pythoncom.CoInitialize()
            except Exception as e:
                print(f"Error al inicializar COM: {e}")

        try:
            company_id = request.query_params.get("company")
            diagnosis_id = int(request.query_params.get("diagnosis"))
            format_to_save = request.query_params.get(
                "format_to_save"
            )  # Default to 'word'

            company = None

            if int(company_id) > 0:
                try:
                    company = self.company_service.get_company(company_id)
                except Company.DoesNotExist:
                    return Response(
                        {"error": "Empresa no encontrada."},
                        status=status.HTTP_404_NOT_FOUND,
                    )
            get_use_case = GetUseCases(self.diagnosis_repository)
            if diagnosis_id > 0:
                diagnosis = get_use_case.get_by_id(diagnosis_id)
            else:
                diagnosis = get_use_case.get_unfinalized_diagnosis_for_company(
                    company.id
                )

            template_path = os.path.join(
                settings.MEDIA_ROOT, "templates/PLAN_DE_TRABAJO_BOLIVAR.docx"
            )
            doc = Document(template_path)
            month, year = get_current_month_and_year()

            variables_to_change = {
                "{{COMPANY_NAME}}": "",
                "{{COMPANY_NIT}}": "",
                "{{DATE_ELABORED}}": f"{month.upper()} {year}",
                "{{CONSULTOR_NAME}}": f"{diagnosis.consultor.first_name.upper()} {diagnosis.consultor.last_name.upper()}",
                "{{SST_LICENSE}}": (
                    diagnosis.consultor.licensia_sst
                    if diagnosis.consultor.licensia_sst is not None
                    else "SIN LICENCIA"
                ),
                "{{NIVEL_PESV}}": diagnosis.type.name.upper(),
                "{{GENERAL_TABLE}}": "",
            }
            if diagnosis.is_for_corporate_group:
                variables_to_change["{{COMPANY_NAME}}"] = (
                    diagnosis.corporate_group.name.upper()
                )
                variables_to_change["{{COMPANY_NIT}}"] = format_nit(
                    diagnosis.corporate_group.nit
                )
            else:
                variables_to_change["{{COMPANY_NAME}}"] = company.name.upper()
                variables_to_change["{{COMPANY_NIT}}"] = format_nit(company.nit)

            # Filtrar los Checklist_Requirement que tienen compliance con ID 2
            checklist_requirements = Checklist_Requirement.objects.filter(
                compliance__id=2, diagnosis=diagnosis.id
            )

            # Obtener los IDs de los requisitos asociados a los checklist_requirements
            requirement_ids = checklist_requirements.values_list(
                "requirement_id", flat=True
            ).distinct()

            requirements = Diagnosis_Requirement.objects.filter(
                id__in=requirement_ids
            ).distinct()

            # Filtrar los WorkPlan_Recomendation que tienen un requirement que está en checklist_requirements
            workplan_recommendations = WorkPlan_Recomendation.objects.filter(
                requirement__in=requirements
            )

            # Obtener las observaciones relacionadas con el nombre de WorkPlan_Recomendation
            observations = (
                Checklist_Requirement.objects.filter(
                    requirement__in=workplan_recommendations.values_list(
                        "requirement_id", flat=True
                    )
                )
                .select_related("requirement")
                .values(
                    "requirement__cycle",
                    "requirement__name",
                    "requirement__workplan_recomendation__name",
                )
                .distinct()  # Eliminar los duplicados
            )

            # Agrupar las observaciones por ciclo
            grouped_observations = OrderedDict()
            for obs in observations:
                cycle = obs["requirement__cycle"]
                if cycle not in grouped_observations:
                    grouped_observations[cycle] = []
                grouped_observations[cycle].append(
                    {
                        "requirement_name": obs["requirement__name"],
                        "recommendation_name": obs[
                            "requirement__workplan_recomendation__name"
                        ],
                    }
                )
            insert_table_work_plan(doc, "{{GENERAL_TABLE}}", grouped_observations)
            replace_placeholders_in_document(doc, variables_to_change)

            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            word_file_content = buffer.getvalue()
            if format_to_save == "pdf":
                pdf_file_content = convert_docx_to_pdf_base64(word_file_content)
                encoded_file = pdf_file_content
            else:  # Default to Word
                file_content = word_file_content
                encoded_file = base64.b64encode(file_content).decode("utf-8")

            return Response({"file": encoded_file}, status=status.HTTP_200_OK)
        except Exception as ex:
            tb_str = traceback.format_exc()  # Formatear la traza del error
            return Response(
                {"error": str(ex), "traceback": tb_str},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False)
    def radarChart(self, request: Request):
        company_id = request.query_params.get("company_id")
        diagnosis_id = int(request.query_params.get("diagnosis"))

        get_use_case = GetUseCases(self.diagnosis_repository)
        if diagnosis_id > 0:
            diagnosis = get_use_case.get_by_id(diagnosis_id)
        else:
            try:
                company = self.company_service.get_company(company_id)
            except Company.DoesNotExist:
                return Response(
                    {"error": "Empresa no encontrada."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            diagnosis = get_use_case.get_unfinalized_diagnosis_for_company(company.id)

        datas_by_cycle = DiagnosisService.calculate_completion_percentage(diagnosis.id)
        radar_data = [
            {
                "cycle": data["cycle"],
                "cycle_percentage": round(data["cycle_percentage"], 2),
            }
            for data in datas_by_cycle
        ]
        return Response(radar_data, status=status.HTTP_200_OK)

    @action(detail=False)
    def tableReport(self, request: Request):
        company_id = request.query_params.get("company_id")
        diagnosis_id = int(request.query_params.get("diagnosis"))

        get_use_case = GetUseCases(self.diagnosis_repository)
        if diagnosis_id > 0:
            diagnosis = get_use_case.get_by_id(diagnosis_id)
        else:
            try:
                company = self.company_service.get_company(company_id)
            except Company.DoesNotExist:
                return Response(
                    {"error": "Empresa no encontrada."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            diagnosis = get_use_case.get_unfinalized_diagnosis_for_company(company.id)

        datas_by_cycle = DiagnosisService.calculate_completion_percentage(diagnosis.id)
        return Response(datas_by_cycle, status=status.HTTP_200_OK)

    @action(detail=False)
    def tableReportTotal(self, request: Request):
        company_id = request.query_params.get("company_id")
        diagnosis_id = int(request.query_params.get("diagnosis"))

        get_use_case = GetUseCases(self.diagnosis_repository)
        if diagnosis_id > 0:
            diagnosis = get_use_case.get_by_id(diagnosis_id)
        else:
            try:
                company = self.company_service.get_company(company_id)
            except Company.DoesNotExist:
                return Response(
                    {"error": "Empresa no encontrada."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            diagnosis = get_use_case.get_unfinalized_diagnosis_for_company(company.id)

        percentage_success = DiagnosisService.calculate_completion_percentage_data(
            diagnosis.id
        )

        compliance_counts = (
            CheckList.objects.filter(diagnosis=diagnosis.id)
            .values("compliance_id")  # Agrupa por compliance_id
            .annotate(
                count=Count("id")
            )  # Cuenta la cantidad de registros en cada grupo
            .order_by("compliance_id")  # Ordena por compliance_id
        )

        return Response(
            {"counts": compliance_counts, "general": percentage_success},
            status=status.HTTP_200_OK,
        )

    @action(detail=False)
    def count_diagnosis_by_consultor(self, request: Request):
        consultor_id = request.query_params.get("consultor")
        data = (
            Diagnosis.objects.filter(consultor__id=consultor_id)
            .values("consultor__id", "consultor__username")
            .annotate(total=Count("id"))
        )
        return Response(data)

    @action(detail=False)
    def count_diagnosis_by_consultor_by_type(self, request: Request):
        consultor_id = request.query_params.get("consultor")
        data = (
            Diagnosis.objects.filter(consultor__id=consultor_id)
            .values("type__name")
            .annotate(total=Count("id"))
        )
        return Response(data)

    @action(detail=False)
    def count_diagnosis_by_consultor_by_mode_ejecution(self, request: Request):
        consultor_id = request.query_params.get("consultor")
        data = (
            Diagnosis.objects.filter(consultor__id=consultor_id)
            .values("consultor__id", "consultor__username", "mode_ejecution")
            .annotate(total=Count("id"))
        )
        return Response(data)

    @action(detail=False)
    def compliance_trend(self, request: Request):
        checklists = CheckList.objects.all()
        # Agrupar por fecha y calcular porcentaje de cumplimiento
        trend_data = (
            checklists.values("diagnosis__date_elabored")
            .annotate(
                total_count=Count("id"),
                fulfilled_count=Count("id", filter=Q(obtained_value__gt=0)),
            )
            .order_by("diagnosis__date_elabored")
        )

        # Formatear los datos para el gráfico
        formatted_data = [
            {
                "date": record["diagnosis__date_elabored"],
                "fulfilled_percentage": round(
                    (record["fulfilled_count"] / record["total_count"]) * 100, 2
                ),
            }
            for record in trend_data
        ]

        return Response(formatted_data, status=status.HTTP_200_OK)

    def get_queryset(self):
        diagnosis_id = self.request.data.get("diagnosis")
        if diagnosis_id is not None:
            return Diagnosis.objects.filter(pk=diagnosis_id)
        return Diagnosis.objects.all()

    def retrieve(self, request: Request, pk=None, *args, **kwargs):
        """
        Obtiene un diagnositco específica por su ID.
        """
        corporate_group_id = request.query_params.get("corporate_group")
        pk = self.kwargs.get("pk")
        use_case = GetUseCases(self.diagnosis_repository)
        try:
            if corporate_group_id:
                corporate_group = self.corporate_group_repository.get_by_id(
                    corporate_group_id
                )
            else:
                corporate_group = None

            if int(pk) > 0:
                # Obtener el objeto según el ID
                instance = self.get_object()
                # Devolver una respuesta con los datos serializados
            else:
                if corporate_group:
                    instance = use_case.get_by_corporate(corporate_group.id)
                else:
                    instance = self.get_object()

            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        except Diagnosis.DoesNotExist:
            # Manejar el caso en que la empresa no se encuentra
            return Response(
                {"error": "El diagnostico no existe."}, status=status.HTTP_404_NOT_FOUND
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
