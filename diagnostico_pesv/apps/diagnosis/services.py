from .models import *
from .serializers import *
from utils import functionUtils
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from collections import defaultdict
from apps.diagnosis_counter.models import Fleet, Driver, Diagnosis_Counter
from apps.diagnosis_counter.serializers import FleetSerializer, DriverSerializer
from django.db import transaction
from django.conf import settings
import os
from docx import Document
from apps.sign.models import User
from utils.constants import ComplianceIds
from utils.functionUtils import blank_to_null
from .helper import *
from django.db.models import Prefetch, OuterRef, Subquery, Q, Sum, Count
from apps.diagnosis_requirement.core.models import (
    Recomendation,
)
import platform


class DiagnosisService:
    diagnosis_model = Diagnosis
    company = Company
    date_elabored = None

    @staticmethod
    def calculate_total_variable_value(checklists):
        total = 0
        for checklist in checklists:
            total += checklist.question.variable_value
        return total

    @staticmethod
    def calculate_total_obtained_value(checklists):
        total = 0
        for checklist in checklists:
            total += checklist.obtained_value
        return total

    @staticmethod
    def calculate_completion_percentage_data(diagnosis_id):
        service_instance = DiagnosisService()
        # Obtén los CheckList relacionados con el diagnostico
        checklists_questions = CheckList.objects.filter(diagnosis=diagnosis_id)

        total_value_variable = service_instance.calculate_total_variable_value(
            checklists_questions
        )
        total_obtained_value = service_instance.calculate_total_obtained_value(
            checklists_questions
        )

        percentage = round((total_obtained_value / total_value_variable) * 100, 2)
        return percentage

    @staticmethod
    def calculate_completion_percentage(diagnosis_id):
        # Obtén los CheckList relacionados con el diagnostico
        checklists = CheckList.objects.filter(diagnosis=diagnosis_id).select_related(
            "question__requirement"
        )

        # Estructura para el resultado final
        result = []

        # Agrupar CheckLists por ciclo y paso
        checklists_by_cycle = {}
        for checklist in checklists:
            requirement = checklist.question.requirement
            step = requirement.step
            cycle = requirement.cycle

            if cycle not in checklists_by_cycle:
                checklists_by_cycle[cycle] = {}

            if step not in checklists_by_cycle[cycle]:
                checklists_by_cycle[cycle][step] = []

            checklists_by_cycle[cycle][step].append(checklist)

        # Calcular porcentajes y estructurar datos
        for cycle, steps in checklists_by_cycle.items():
            cycle_data = {"cycle": cycle, "steps": [], "cycle_percentage": 0.0}
            total_cycle_percentage = 0.0
            num_steps = len(steps)

            for step, checklists in steps.items():
                step_data = {"step": step, "requirements": [], "percentage": 0.0}

                total_variable_value = 0
                total_obtained_value = 0

                # Agrupar por requerimiento
                requirements_by_name = {}
                for checklist in checklists:
                    requirement = checklist.question.requirement
                    requirement_name = requirement.name
                    if requirement_name not in requirements_by_name:
                        requirements_by_name[requirement_name] = {
                            "requirement_name": requirement_name,
                            "questions": [],
                            "percentage": 0.0,
                        }

                    # Ajustar el valor obtenido basado en `is_articuled`
                    if checklist.is_articuled:
                        obtained_value = checklist.obtained_value
                    else:
                        obtained_value = (
                            checklist.question.variable_value
                        )  # Considerar 100%

                    requirements_by_name[requirement_name]["questions"].append(
                        {
                            "question_name": checklist.question.name,
                            "variable_value": checklist.question.variable_value,
                            "obtained_value": obtained_value,
                            "compliance": checklist.compliance.name.upper(),
                        }
                    )
                    total_variable_value += checklist.question.variable_value
                    total_obtained_value += obtained_value

                # Calcular porcentaje del paso
                if total_variable_value > 0:
                    step_data["percentage"] = (
                        total_obtained_value / total_variable_value
                    ) * 100

                # Añadir requerimientos al paso
                step_data["requirements"] = list(requirements_by_name.values())
                cycle_data["steps"].append(step_data)
                total_cycle_percentage += step_data["percentage"]

            if num_steps > 0:
                cycle_data["cycle_percentage"] = total_cycle_percentage / num_steps
            # Añadir el ciclo a la lista de resultados
            result.append(cycle_data)

        return result

    @staticmethod
    def group_questions_by_step(
        checklist_requirements,
        requirements,
        checklist_questions=None,
        include_compliance=False,
    ):

        requirements_dict = defaultdict(list)
        for requirement in requirements:
            requirements_dict[requirement.id] = list(requirement.requirements.all())

        result = []

        if include_compliance and checklist_questions is not None:
            question_compliance_dict = {
                q.question_id: q.compliance for q in checklist_questions
            }
        else:
            question_compliance_dict = {}

        for cr in checklist_requirements:
            requirement = cr.requirement
            compliance = cr.compliance
            questions = requirements_dict.get(requirement.id, [])
            # Incluye el cumplimiento de las preguntas si corresponde
            if include_compliance:
                questions_with_compliance = [
                    {
                        **question.__dict__,  # Incluye los atributos de la pregunta
                        "compliance": {
                            "id": (
                                question_compliance_dict.get(question.id, None).id
                                if question_compliance_dict.get(question.id)
                                else None
                            ),
                            "name": (
                                question_compliance_dict.get(question.id, None).name
                                if question_compliance_dict.get(question.id)
                                else None
                            ),
                        },
                        "requirement": question.requirement,
                    }
                    for question in questions
                ]
                result.append(
                    {
                        "id": cr.id,
                        "step": requirement.step,
                        "cycle": requirement.cycle,
                        "observation": cr.observation,
                        "requirement_name": requirement.name,
                        "compliance": {
                            "id": compliance.id,
                            "name": compliance.name,
                        },
                        "questions": Diagnosis_QuestionsChecklistSerializer(
                            questions_with_compliance, many=True
                        ).data,
                    }
                )
            else:
                questions_with_compliance = questions
                result.append(
                    {
                        "id": cr.id,
                        "step": requirement.step,
                        "cycle": requirement.cycle,
                        "observation": cr.observation,
                        "requirement_name": requirement.name,
                        "compliance": {
                            "id": compliance.id,
                            "name": compliance.name,
                        },
                        "questions": Diagnosis_QuestionsSerializer(
                            questions_with_compliance, many=True
                        ).data,
                    }
                )
        return result

    @staticmethod
    def process_vehicle_data(diagnosis_count_id, vehicle_data):
        vehicle_errors = []
        with transaction.atomic():
            total_vehicles = (
                functionUtils.calculate_total_vehicles_quantities_for_company(
                    vehicle_data
                )
            )
            for vehicle in vehicle_data:
                vehicle["diagnosis_counter"] = diagnosis_count_id
                fleet_instance = Fleet.objects.filter(
                    diagnosis_counter=diagnosis_count_id,
                    vehicle_question=vehicle.get("vehicle_question"),
                ).first()
                serializer_fleet = FleetSerializer(
                    instance=fleet_instance, data=vehicle
                )
                if serializer_fleet.is_valid():
                    serializer_fleet.save()
                else:
                    vehicle_errors.append(serializer_fleet.errors)
            return total_vehicles, vehicle_errors

    @staticmethod
    def process_driver_data(diagnosis_count_id, driver_data):
        driver_errors = []
        with transaction.atomic():
            total_drivers = (
                functionUtils.calculate_total_drivers_quantities_for_company(
                    driver_data
                )
            )
            for driver in driver_data:
                driver["diagnosis_counter"] = diagnosis_count_id
                driver_instance = Driver.objects.filter(
                    diagnosis_counter=diagnosis_count_id,
                    driver_question=driver.get("driver_question"),
                ).first()
                serializer_driver = DriverSerializer(
                    instance=driver_instance, data=driver
                )
                if serializer_driver.is_valid():
                    serializer_driver.save()
                else:
                    driver_errors.append(serializer_driver.errors)
            return total_drivers, driver_errors

    @staticmethod
    def build_error_response(vehicle_errors, driver_errors):
        return Response(
            {"vehicleErrors": vehicle_errors, "driverErrors": driver_errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @staticmethod
    def build_success_response(vehicle_data, driver_data, diagnosis):
        return Response(
            {
                "vehicleData": vehicle_data,
                "driverData": driver_data,
                "diagnosis": diagnosis.id,
            },
            status=status.HTTP_201_CREATED,
        )

    @classmethod
    def create_diagnosis(cls, company_id, **diagnosis_data) -> Diagnosis:
        """
        Crea una nueva instancia del modelo Diagnosis usando los datos proporcionados.

        :param diagnosis_data: Datos adicionales para crear el diagnóstico.
        :return: La instancia creada del modelo Diagnosis.
        """
        today = datetime.now().date()
        company_instance = cls.company.objects.get(pk=company_id)

        # Agregar la compañía y la fecha a los datos del diagnóstico
        diagnosis_data.update({"company": company_instance, "date_elabored": today})

        new_diagnosis = cls.diagnosis_model.objects.create(**diagnosis_data)

        return new_diagnosis


class GenerateReport:
    company = None
    diagnosis = None
    sequence = str
    schedule = str

    def __init__(
        self,
        company: Company | None,
        diagnosis: Diagnosis | None,
        sequence: str,
        schedule: str,
    ) -> None:
        self.company = company
        self.diagnosis = diagnosis
        self.sequence = sequence
        self.schedule = schedule
        # Solo intenta importar pythoncom si el sistema operativo es Windows
        if platform.system() == "Windows":
            try:
                import pythoncom

                pythoncom.CoInitialize()
            except Exception as e:
                print(f"Error al inicializar COM: {e}")

    def generate_report(self, format_to_save: str):
        vehicle_questions = VehicleQuestions.objects.all()
        driver_questions = DriverQuestion.objects.all()
        template_path = os.path.join(
            settings.MEDIA_ROOT, "templates/DIAGNÓSTICO_BOLIVAR.docx"
        )

        doc = Document(template_path)
        self.diagnosis.sequence = self.sequence
        self.diagnosis.schedule = self.schedule
        month, year = get_current_month_and_year()
        # Datos de la tabla
        now = datetime.now()
        formatted_date = now.strftime("%d-%m-%Y")
        fecha = str(formatted_date)
        variables_to_change = {
            "{{CRONOGRAMA}}": self.diagnosis.schedule,
            "{{SECUENCIA}}": self.diagnosis.sequence,
            "{{MES_ANNO}}": f"{month.upper()} {year}",
            "{{CONSULTOR_NOMBRE}}": f"{self.diagnosis.consultor.first_name.upper()} {self.diagnosis.consultor.last_name.upper()}",
            "{{LICENCIA_SST}}": (
                self.diagnosis.consultor.licensia_sst
                if self.diagnosis.consultor.licensia_sst is not None
                else "SIN LICENCIA"
            ),
            "{{MODE_PESV}}": self.diagnosis.mode_ejecution,
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

        if self.diagnosis.is_for_corporate_group:
            diagnosis_counter = Diagnosis_Counter.objects.filter(
                diagnosis=self.diagnosis
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
                    self.diagnosis.corporate_group.name.upper()
                )
                variables_to_change["{{NIT}}"] = format_nit(
                    self.diagnosis.corporate_group.nit
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
                    diagnosis=self.diagnosis,
                )
        else:
            diagnosis_counter = Diagnosis_Counter.objects.filter(
                diagnosis=self.diagnosis, company=self.company
            ).first()

            fleet_data = Fleet.objects.filter(diagnosis_counter=diagnosis_counter.id)
            driver_data = Driver.objects.filter(diagnosis_counter=diagnosis_counter.id)

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
                Driver.objects.filter(diagnosis_counter=diagnosis_counter.id).aggregate(
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

            nit = format_nit(self.company.nit)
            summary = f"De acuerdo con la información anterior, se identifica que la empresa se encuentra en misionalidad {self.company.mission.id} | {self.company.mission.name.upper()} y que cuenta con {total_general_vehicles} vehículos propiedad de la empresa y {total_quantity_driver} personas con rol de conductor, por lo tanto, se define que debe diseñar e implementar un plan estratégico de seguridad vial “{self.diagnosis.type.name.upper()}”."

            variables_to_change["{{COMPANY_NAME}}"] = self.company.name.upper()
            variables_to_change["{{NIT}}"] = nit
            variables_to_change["{{SUMMARY_NOT_IN_CORPORATE_GROUPS}}"] = summary

            empresa = self.company.name
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
                self.diagnosis.type.name.upper(),
                str(self.company.segment.name),
                f"{self.company.dependant} - {self.company.dependant_position}".upper(),
                self.company.acquired_certification or "",
                self.company.ciius,
            )

        datas_by_cycle = DiagnosisService.calculate_completion_percentage(
            self.diagnosis.id
        )

        data_completion_percentage = (
            DiagnosisService.calculate_completion_percentage_data(self.diagnosis.id)
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
            self.diagnosis.type.name.upper(),
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
                    diagnosis=self.diagnosis.id, compliance_id=OuterRef("pk")
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

        # Filtrar Checklist_Requirements por diagnosis_id
        checklist_requirements = Checklist_Requirement.objects.filter(
            diagnosis=self.diagnosis.id,
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
        if self.diagnosis.type.id == 1:  # Supongamos que 1 es 'basic'
            filtro_tipo = Q(basic=True)
        elif self.diagnosis.type.id == 2:  # Supongamos que 2 es 'standard'
            filtro_tipo = Q(standard=True)
        elif self.diagnosis.type.id == 3:  # Supongamos que 3 es 'advanced'
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
        variables_to_change["{{PERCENTAGE_TOTAL}}"] = str(data_completion_percentage)
        insert_table_recomendations(doc, "{{RECOMENDATIONS}}", resultado_final)

        replace_placeholders_in_document(doc, variables_to_change)

        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        word_file_content = buffer.getvalue()
        encoded_file = None
        if format_to_save == "pdf":
            pdf_file_content, pdf_byte = convert_docx_to_pdf_base64(word_file_content)
            encoded_file = pdf_file_content
            file_content = pdf_byte
        else:  # Default to Word
            file_content = word_file_content
            encoded_file = base64.b64encode(file_content).decode("utf-8")

        return encoded_file, file_content
