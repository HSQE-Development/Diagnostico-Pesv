from .models import *


class DiagnosisService:
    @staticmethod
    def calculate_completion_percentage(companyId):
        # Obtén los CheckList relacionados con la compañía
        checklists = CheckList.objects.filter(company_id=companyId).select_related(
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
            cycle_data = {"cycle": cycle, "steps": []}

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

            # Añadir el ciclo a la lista de resultados
            result.append(cycle_data)

        return result
