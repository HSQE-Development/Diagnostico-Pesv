from apps.diagnosis.models import Diagnosis, Checklist_Requirement, Compliance
from apps.diagnosis.interfaces import (
    DiagnosisRepositoryInterface,
    CheckListRepositoryInterface,
    CheckListRequirementRepositoryInterface,
    IComplianceRepository,
    IDiagnosisQuestionRepository,
)
from datetime import datetime
from typing import List, Dict


class CreateDiagnosis:
    def __init__(self, repository: DiagnosisRepositoryInterface, diagnosis_data: dict):
        self.repository = repository
        self.diagnosis_data = diagnosis_data

    def execute(self) -> Diagnosis:
        """
        Ejecuta la creación de un diagnóstico.

        :return: Instancia del diagnóstico creado.
        """
        today = datetime.now().date()
        self.diagnosis_data["date_elabored"] = today
        # Pasar los datos del diccionario al repositorio
        return self.repository.save(self.diagnosis_data)


class GetUseCases:
    def __init__(self, repository: DiagnosisRepositoryInterface):
        self.repository = repository

    def get_diagnosis_by_date_elabored(self, date) -> Diagnosis | None:
        return self.repository.get_by_date_elabored(date)

    def get_unfinalized_diagnosis_for_company(self, company_id):
        return self.repository.get_unfinalized_diagnosis_for_company(company_id)


class CreateChecklistRequirement:
    def __init__(
        self, repository: CheckListRequirementRepositoryInterface, diagnosis_data: dict
    ):
        self.repository = repository
        self.diagnosis_data = diagnosis_data

    def execute(self) -> Checklist_Requirement:
        # Pasar los datos del diccionario al repositorio
        return self.repository.save(self.diagnosis_data)


class GetComplianceById:
    def __init__(self, repository: IComplianceRepository, id: int):
        self.repository = repository
        self.id = id

    def execute(self) -> Compliance:
        # Pasar los datos del diccionario al repositorio
        return self.repository.get_compliance_by_id(self.id)


class GetRequirementById:
    def __init__(self, repository: CheckListRequirementRepositoryInterface, id: int):
        self.repository = repository
        self.id = id

    def execute(self):
        # Pasar los datos del diccionario al repositorio
        return self.repository.get_requirement_by_id(self.id)


class GetCheckListByQuestionIdAndDiagnosisId:
    def __init__(
        self,
        repository: CheckListRepositoryInterface,
        question_id: int,
        diagnosis_id: int,
    ):
        self.repository = repository
        self.question_id = question_id
        self.diagnosis_id = diagnosis_id

    def execute(self):
        # Pasar los datos del diccionario al repositorio
        return self.repository.get_checklists_by_question_id_and_diagnosis_id(
            self.question_id, self.diagnosis_id
        )


class GetQuestionById:
    def __init__(self, repository: IDiagnosisQuestionRepository, id: int):
        self.repository = repository
        self.id = id

    def execute(self):
        # Pasar los datos del diccionario al repositorio
        return self.repository.get_by_id(self.id)


class CheckListMassiveCreate:
    def __init__(self, repository: CheckListRepositoryInterface, data_to_save):
        self.repository = repository
        self.data_to_save = data_to_save

    def execute(self):
        # Pasar los datos del diccionario al repositorio
        return self.repository.massive_save(self.data_to_save)


class CheckListMassiveUpdate:
    def __init__(self, repository: CheckListRepositoryInterface, data_to_save):
        self.repository = repository
        self.data_to_save = data_to_save

    def execute(self):
        # Pasar los datos del diccionario al repositorio
        return self.repository.massive_update(self.data_to_save)


class GetCheckListRequirementByDiagnosisId:
    def __init__(self, repository: CheckListRequirementRepositoryInterface, id: int):
        self.repository = repository
        self.id = id

    def execute(self):
        # Pasar los datos del diccionario al repositorio
        return self.repository.get_checklists_requirement_by_diagnosis_id(self.id)


class GetCheckListRequirementByIdAndDiagnosisId:
    def __init__(
        self,
        repository: CheckListRequirementRepositoryInterface,
        id: int,
        diagnosis_id: int,
    ):
        self.repository = repository
        self.id = id
        self.diagnosis_id = diagnosis_id

    def execute(self):
        # Pasar los datos del diccionario al repositorio
        return self.repository.get_checklist_requirement_by_id_and_diagnosis_id(
            self.id, self.diagnosis_id
        )


class CheckListRequirementMassiveCreate:
    def __init__(
        self, repository: CheckListRequirementRepositoryInterface, data_to_save
    ):
        self.repository = repository
        self.data_to_save = data_to_save

    def execute(self):
        # Pasar los datos del diccionario al repositorio
        return self.repository.massive_save(self.data_to_save)


class CheckListRequirementMassiveUpdate:
    def __init__(
        self, repository: CheckListRequirementRepositoryInterface, data_to_save
    ):
        self.repository = repository
        self.data_to_save = data_to_save

    def execute(self):
        # Pasar los datos del diccionario al repositorio
        return self.repository.massive_update(self.data_to_save)


class UpdateDiagnosis:
    def __init__(
        self, repository: DiagnosisRepositoryInterface, data_to_save: Diagnosis
    ):
        self.repository = repository
        self.data_to_save = data_to_save

    def execute(self):
        # Pasar los datos del diccionario al repositorio
        return self.repository.update(self.data_to_save)


class CalculateCompletionPercentage:
    def __init__(self, repository: CheckListRepositoryInterface):
        self.repository = repository

    def execute(self, company_id: int) -> List[Dict]:
        checklists = self.repository.get_checklists_by_company(company_id)
        result = []
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
