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
    Notification,
)
from .serializers import (
    Diagnosis_QuestionsSerializer,
    DiagnosisSerializer,
    NotificationSerializer,
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
from collections import defaultdict
from .services import DiagnosisService, GenerateReport
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
from django.db.models import Prefetch, OuterRef, Subquery, Q, Sum, Count
from apps.sign.models import User, QueryLog
from utils.constants import ComplianceIds
from collections import OrderedDict
from apps.corporate_group.repositories import CorporateGroupRepository
from django.core.mail import EmailMessage
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


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
                print(questions)
                for question in questions:
                    CheckList.objects.filter(
                        question=question.id, diagnosis=diagnosis_id
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
                    # if not CheckList.objects.filter(diagnosis=diagnosis).exists():

                    for requirement_id in missing_requirements:
                        Checklist_Requirement.objects.create(
                            diagnosis=diagnosis,
                            requirement_id=requirement_id,
                            compliance=compliance,  # Ajusta el valor según sea necesario
                            observation=None,  # Ajusta el valor según sea necesario
                        )
                        questions = Diagnosis_Questions.objects.filter(
                            requirement=requirement_id
                        )
                        for question in questions:
                            if not CheckList.objects.filter(
                                diagnosis=diagnosis, question=question
                            ).exists():
                                checklist = CheckList(
                                    question=question,
                                    compliance=compliance,
                                    diagnosis=diagnosis,
                                    obtained_value=0,
                                )
                                checklist.save()

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

            if not diagnosis:
                return Response(
                    {"error": "No se ha realizado el conteo de las empresas."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            max_size_subquery = (
                Diagnosis_Counter.objects.filter(diagnosis=OuterRef("diagnosis"))
                .order_by("-size")
                .values("size")[:1]
            )
            record_with_max_size = Diagnosis_Counter.objects.filter(
                diagnosis=diagnosis.id, size=Subquery(max_size_subquery)
            ).first()

            corporate_group.nit = record_with_max_size.company.nit
            diagnosis.type = record_with_max_size.size

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
        user = request.user
        ip_address = request.META.get("REMOTE_ADDR", "0.0.0.0")
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        consultor_id = request.data.get("consultor")
        external_count_complete = request.data.get("external_count_complete")
        company_id = request.data.get("company")
        vehicle_data = request.data.get("vehicleData", [])
        driver_data = request.data.get("driverData", [])
        diagnosis_data = {
            "company": company_id,
            "date_elabored": None,
            "consultor": consultor_id if consultor_id > 0 else None,
        }
        diagnosis_serializer = DiagnosisSerializer(data=diagnosis_data)
        consultor = None
        if diagnosis_serializer.is_valid():
            try:
                with transaction.atomic():
                    company = self.company_service.get_company(company_id)
                    if consultor_id > 0:
                        consultor = User.objects.get(id=consultor_id)

                    get_use_case = GetUseCases(self.diagnosis_repository)
                    # existing_diagnosis = get_use_case.get_diagnosis_by_date_elabored(today)
                    existing_diagnosis = (
                        get_use_case.get_unfinalized_diagnosis_for_company(company.id)
                    )
                    # Se debe finalizar cuando se cree un nuevo diagnostico no cuando se responda!!!
                    if existing_diagnosis:
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
                    diagnosis.in_progress = True
                    if external_count_complete:
                        userInstance = User.objects.get(id=user.id)
                        userInstance.external_step = 2
                        userInstance.save()
                        diagnosis.external_count_complete = True
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

                    channel_layer = get_channel_layer()
                    notification = Notification.objects.create(
                        user=None,
                        message=f"Se ha Completado el conteo de la flota vehicular.",
                        created_at=datetime.now(),
                        diagnosis=diagnosis,
                    )
                    async_to_sync(channel_layer.group_send)(
                        "diagnosis",  # Nombre del grupo al que enviar el mensaje
                        {
                            "type": "external_notification",  # Tipo de mensaje
                            "notification_data": NotificationSerializer(
                                notification
                            ).data,
                        },
                    )
                    async_to_sync(channel_layer.group_send)(
                        "diagnosis",  # Nombre del grupo al que enviar el mensaje
                        {
                            "type": "external_count",  # Tipo de mensaje
                            "diagnosis_data": DiagnosisSerializer(diagnosis).data,
                        },
                    )

                    QueryLog.objects.create(
                        user=request.user if request.user.is_authenticated else None,
                        ip_address=ip_address,
                        action="saveAnswerCuestions",
                        http_method=request.method,
                        query_params=dict(request.query_params),
                        user_agent=user_agent,
                    )
                    return self.diagnosis_service.build_success_response(
                        vehicle_data, driver_data, diagnosis
                    )

            except Company.DoesNotExist:
                return Response(
                    {"error": "Company not found."}, status=status.HTTP_404_NOT_FOUND
                )
            except Exception as ex:
                QueryLog.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    ip_address=ip_address,
                    action=f"saveAnswerCuestions -error:  {str(ex)}",
                    http_method=request.method,
                    query_params=dict(request.query_params),
                    user_agent=user_agent,
                )
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
            ejecution = diagnosis_data["mode_ejecution"]

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
                diagnosis.mode_ejecution = ejecution
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
            generate_report = GenerateReport(
                company=company,
                diagnosis=diagnosis,
                schedule=schedule,
                sequence=sequence,
            )
            encoded_file, file_content = generate_report.generate_report(format_to_save)

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
    def count_diagnosis_by_consultors(self, request: Request):
        data = (
            Diagnosis.objects.all()
            .values("consultor__id", "consultor__username")
            .annotate(total=Count("id"))
        )
        return Response(data)

    @action(detail=False)
    def count_diagnosis_by_consultor_by_mode_ejecution(self, request: Request):
        consultor_id = request.query_params.get("consultor")
        if consultor_id:
            data = (
                Diagnosis.objects.filter(consultor__id=consultor_id)
                .values("consultor__id", "consultor__username", "mode_ejecution")
                .annotate(total=Count("id"))
            )
        else:
            data = (
                Diagnosis.objects.all()
                .values("consultor__id", "consultor__username", "mode_ejecution")
                .annotate(total=Count("id"))
            )
        return Response(data)

    @action(detail=False)
    def compliance_trend(self, request: Request):
        diagnosis = Diagnosis.objects.all()
        # Agrupar por fecha y calcular porcentaje de cumplimiento
        trend_data = (
            diagnosis.values("date_elabored")
            .annotate(
                total_count=Count("id"),
                fulfilled_count=Count("id"),
            )
            .order_by("date_elabored")
        )

        # Formatear los datos para el gráfico
        formatted_data = [
            {
                "date": record["date_elabored"],
                "fulfilled_percentage": record["total_count"],
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

    @action(detail=False, methods=[HTTPMethod.POST])
    def send_report(self, request: Request):
        get_use_case = GetUseCases(self.diagnosis_repository)
        email_to = request.data.get("email_to")
        diagnosis_id = int(request.data.get("diagnosis"))
        company_id = request.data.get("company")
        schedule = request.query_params.get("schedule")
        sequence = request.query_params.get("sequence")
        company = None
        if int(company_id) > 0:
            try:
                company = self.company_service.get_company(company_id)
            except Company.DoesNotExist:
                return Response(
                    {"error": "Empresa no encontrada."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        if not email_to:
            return Response(
                {"error": "El id del grupo empresarial es obligatiorio"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if int(diagnosis_id) > 0:
            diagnosis = get_use_case.get_by_id(diagnosis_id)
        else:
            return Response(
                {"error": "El id del diagnostico es obligatiorio"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        variable_for_email = {"subject": "", "body": ""}
        if diagnosis.is_for_corporate_group:
            variable_for_email["subject"] = (
                f"Informe Diagnostico PESV - {diagnosis.corporate_group.name.upper()}"
            )
            variable_for_email["body"] = (
                f"Buenos dias se adjunta informe de diagnostico Pesv para el grupo empresarial: {diagnosis.corporate_group.name.upper()}, con NIT: {diagnosis.corporate_group.nit}"
            )
        else:
            variable_for_email["subject"] = (
                f"Informe Diagnostico PESV - {diagnosis.company.name.upper()}"
            )
            variable_for_email["body"] = (
                f"Buenos dias se adjunta informe de diagnostico Pesv para la empresa: {diagnosis.company.name.upper()}, con NIT: {diagnosis.company.nit}"
            )

        generate_report = GenerateReport(
            company=company,
            diagnosis=diagnosis,
            schedule=schedule,
            sequence=sequence,
        )
        encoded_file, file_content = generate_report.generate_report("pdf")

        email = EmailMessage(
            subject=variable_for_email["subject"],
            body=variable_for_email["body"],
            from_email="soporte@consultoriaycapacitacionhseq.com",
            to=[email_to],
        )
        email.attach("Diagnostico_PESV.pdf", file_content, "application/pdf")
        try:
            email.send()
            return Response(
                {"message": "Correo enviado con éxito"}, status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False)
    def find_notifications_by_user(self, request: Request):
        user_id = request.query_params.get("user")
        user = None
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "Usuario no existe o esta inactivo"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            notifications = Notification.objects.filter(
                Q(user=user) | Q(user__isnull=True)
            ).order_by("-created_at")
            serializer = NotificationSerializer(notifications, many=True)
            return Response(serializer.data)
        except Exception as ex:
            return Response(
                {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=[HTTPMethod.PATCH])
    def read_notifications(self, request: Request):
        try:
            notifications_ids = request.data.get("notifications", [])
            notifications = Notification.objects.filter(id__in=notifications_ids)
            for notify in notifications:
                notify.read = True

            Notification.objects.bulk_update(notifications, ["read"])
            return Response({"message": True})
        except Exception as ex:
            return Response(
                {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
