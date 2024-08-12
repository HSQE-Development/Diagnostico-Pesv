import traceback
import re
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
import base64
import pandas as pd
from apps.diagnosis_requirement.core.models import Diagnosis_Requirement, Recomendation
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
    FleetSerializer,
    DriverSerializer,
    DiagnosisSerializer,
)
from apps.company.models import Company
from apps.diagnosis.models import Fleet, Driver
from utils.functionUtils import blank_to_null
from django.db import transaction
from docx import Document
from io import BytesIO
import os
from django.conf import settings
from .helper import *
from django.db.models import Sum, Count
from collections import defaultdict
from enum import Enum
from django.db.models import Value, Case, CharField, When
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
import traceback
from django.db.models import Prefetch
from apps.sign.models import User


class CompanySizeEnum(Enum):
    AVANZADO = 3
    ESTANDAR = 2
    BASICO = 1


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

    @action(detail=False)
    def findFleetsByCompanyId(self, request: Request):
        company_id = request.query_params.get("company")
        diagnosis_id = int(request.query_params.get("diagnosis", 0))
        try:
            use_case = GetUseCases(self.diagnosis_repository)
            if diagnosis_id > 0:
                diagnosis = use_case.get_by_id(diagnosis_id)
            else:
                diagnosis = use_case.get_unfinalized_diagnosis_for_company(company_id)
            fleets = Fleet.objects.filter(deleted_at=None, diagnosis=diagnosis)
            serializer = FleetSerializer(fleets, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response(
                {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False)
    def findDriversByCompanyId(self, request: Request):
        company_id = request.query_params.get("company")
        diagnosis_id = int(request.query_params.get("diagnosis", 0))
        try:
            use_case = GetUseCases(self.diagnosis_repository)
            if diagnosis_id > 0:
                diagnosis = use_case.get_by_id(diagnosis_id)
            else:
                diagnosis = use_case.get_unfinalized_diagnosis_for_company(company_id)
            drivers = Driver.objects.filter(deleted_at=None, diagnosis=diagnosis)
            serializer = DriverSerializer(drivers, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response(
                {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False)
    def findQuestionsByCompanySize(self, request: Request):
        try:
            company_id = request.query_params.get("company")
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
    def saveAnswerCuestions(self, request: Request):
        consultor_id = request.data.get("consultor")
        company_id = request.data.get("company")
        vehicle_data = request.data.get("vehicleData", [])
        driver_data = request.data.get("driverData", [])
        diagnosis_data = {"company": company_id, "date_elabored": None}
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

                    total_vehicles, vehicle_errors = (
                        self.diagnosis_service.process_vehicle_data(
                            diagnosis.id, vehicle_data
                        )
                    )
                    total_drivers, driver_errors = (
                        self.diagnosis_service.process_driver_data(
                            diagnosis.id, driver_data
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

            try:
                company = self.company_service.get_company(company_id)
                consultor = User.objects.get(pk=consultor_id)
            except Company.DoesNotExist:
                return Response(
                    {"error": "Empresa no encontrada."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            except User.DoesNotExist:
                return Response(
                    {"error": "Consultor no encontrada."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            with transaction.atomic():
                get_use_case = GetUseCases(self.diagnosis_repository)
                diagnosis = get_use_case.get_unfinalized_diagnosis_for_company(
                    company.id
                )
                questions_to_create = []
                questions_to_update = []
                for diagnosis_questions in diagnosisDto:
                    # print(diagnosis)
                    with transaction.atomic():
                        question_id = diagnosis_questions["question"]

                        get_question = GetQuestionById(
                            self.diagnosis_question, question_id
                        )
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

                        newObservation = blank_to_null(
                            diagnosis_questions["observation"]
                        )
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
                            existing_checklist_by_question_and_diagnosis.obtained_value = diagnosis_questions[
                                "obtained_value"
                            ]
                            existing_checklist_by_question_and_diagnosis.is_articuled = diagnosis_questions[
                                "is_articuled"
                            ]
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
                    with transaction.atomic():
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

                if checklists_to_create:
                    massive_create = CheckListRequirementMassiveCreate(
                        self.checklist_requirement_repository, checklists_to_create
                    )
                    massive_create.execute()

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
            diagnosis_id = int(request.query_params.get("diagnosis"))
            format_to_save = request.query_params.get(
                "format_to_save"
            )  # Default to 'word'
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
            vehicle_questions = VehicleQuestions.objects.all()
            driver_questions = DriverQuestion.objects.all()
            fleet_data = Fleet.objects.filter(diagnosis=diagnosis.id)
            driver_data = Driver.objects.filter(diagnosis=diagnosis.id)

            totals_vehicles = Fleet.objects.filter(diagnosis=diagnosis.id).aggregate(
                total_owned=Sum("quantity_owned"),
                total_third_party=Sum("quantity_third_party"),
                total_arrended=Sum("quantity_arrended"),
                total_contractors=Sum("quantity_contractors"),
                total_intermediation=Sum("quantity_intermediation"),
                total_leasing=Sum("quantity_leasing"),
                total_renting=Sum("quantity_renting"),
            )
            total_quantity_driver = (
                Driver.objects.filter(diagnosis=diagnosis.id).aggregate(
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
                "{{CONSULTOR_NOMBRE}}": f"{diagnosis.consultor.first_name.upper()} {diagnosis.consultor.last_name.upper()}",
                "{{LICENCIA_SST}}": (
                    diagnosis.consultor.licensia_sst
                    if diagnosis.consultor.licensia_sst is not None
                    else "SIN LICENCIA"
                ),
                "{{TABLA_DIAGNOSTICO}}": "",
                "{{PLANEAR_TABLE}}": "",
                "{{HACER_TABLE}}": "",
                "{{VERIFICAR_TABLE}}": "",
                "{{ACTUAR_TABLE}}": "",
                "{{MISIONALIDAD_ID}}": str(company.mission.id),
                "{{MISIONALIDAD_NAME}}": company.mission.name.upper(),
                "{{NIVEL_PESV}}": diagnosis.type.name.upper(),
                "{{QUANTITY_VEHICLES}}": str(total_general_vehicles),
                "{{QUANTITY_DRIVERS}}": str(total_quantity_driver),
                "{{CONCLUSIONES_TABLE}}": "",
                "{{GRAPHIC_BAR}}": "",
                "{{TOTALS_TABLE}}": "",
                "{{GRAPHIC_RADAR}}": "",
                "{{RECOMENDATIONS}}": "",
                "{{PERCENTAGE_TOTAL}}": "",
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
                diagnosis.type.name.upper(),
                str(company.segment.name),
                f"{company.dependant} - {company.dependant_position}".upper(),
                company.acquired_certification or "",
            )

            datas_by_cycle = DiagnosisService.calculate_completion_percentage(
                diagnosis.id
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
            compliance_counts = (
                CheckList.objects.filter(diagnosis=diagnosis.id)
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

            variables_to_change["{{PERCENTAGE_TOTAL}}"] = str(general_percentage)
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

    @action(detail=False)
    def radarChart(self, request: Request):
        company_id = request.query_params.get("company_id")
        diagnosis_id = int(request.query_params.get("diagnosis"))
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
            diagnosis = get_use_case.get_unfinalized_diagnosis_for_company(company.id)

        datas_by_cycle = DiagnosisService.calculate_completion_percentage(diagnosis.id)
        return Response(datas_by_cycle, status=status.HTTP_200_OK)

    @action(detail=False)
    def tableReportTotal(self, request: Request):
        company_id = request.query_params.get("company_id")
        diagnosis_id = int(request.query_params.get("diagnosis"))
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
            diagnosis = get_use_case.get_unfinalized_diagnosis_for_company(company.id)

        datas_by_cycle = DiagnosisService.calculate_completion_percentage(diagnosis.id)

        compliance_counts = (
            CheckList.objects.filter(diagnosis=diagnosis.id)
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

        return Response(
            {"counts": compliance_counts, "general": general_percentage},
            status=status.HTTP_200_OK,
        )

    def get_queryset(self):
        diagnosis_id = self.request.query_params.get("diagnosis")
        if diagnosis_id is not None:
            return Diagnosis.objects.filter(pk=diagnosis_id)
        return Diagnosis.objects.all()


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
