from .models import *
from ..infraestructure.serializers import *
from utils import functionUtils
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from collections import defaultdict


class DiagnosisService:
    diagnosis_model = Diagnosis
    company = Company
    date_elabored = None

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
    def group_questions_by_step(checklist_requirements, requirements):
        requirements_dict = defaultdict(list)
        for requirement in requirements:
            requirements_dict[requirement.id] = list(requirement.requirements.all())
        result = []
        for cr in checklist_requirements:
            requirement = cr.requirement
            compliance = cr.compliance
            questions = requirements_dict.get(requirement.id, [])

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
                        questions, many=True
                    ).data,
                }
            )
        return result

    @staticmethod
    def process_vehicle_data(diagnosis_id, vehicle_data):
        vehicle_errors = []
        total_vehicles = functionUtils.calculate_total_vehicles_quantities_for_company(
            vehicle_data
        )
        for vehicle in vehicle_data:
            vehicle["diagnosis"] = diagnosis_id
            fleet_instance = Fleet.objects.filter(
                diagnosis=diagnosis_id, vehicle_question=vehicle.get("vehicle_question")
            ).first()
            serializer_fleet = FleetSerializer(instance=fleet_instance, data=vehicle)
            if serializer_fleet.is_valid():
                serializer_fleet.save()
            else:
                vehicle_errors.append(serializer_fleet.errors)
        return total_vehicles, vehicle_errors

    @staticmethod
    def process_driver_data(diagnosis_id, driver_data):
        driver_errors = []
        total_drivers = functionUtils.calculate_total_drivers_quantities_for_company(
            driver_data
        )
        for driver in driver_data:
            driver["diagnosis"] = diagnosis_id
            driver_instance = Driver.objects.filter(
                diagnosis=diagnosis_id, driver_question=driver.get("driver_question")
            ).first()
            serializer_driver = DriverSerializer(instance=driver_instance, data=driver)
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
    def build_success_response(vehicle_data, driver_data):
        return Response(
            {"vehicleData": vehicle_data, "driverData": driver_data},
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
