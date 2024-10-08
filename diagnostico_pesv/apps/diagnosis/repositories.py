from apps.diagnosis.models import (
    Diagnosis,
    CheckList,
    Checklist_Requirement,
    Diagnosis_Questions,
    Compliance,
    Diagnosis_Questions,
)
from apps.diagnosis_requirement.core.models import Diagnosis_Requirement
from apps.diagnosis.interfaces import (
    DiagnosisRepositoryInterface,
    CheckListRepositoryInterface,
    CheckListRequirementRepositoryInterface,
    IComplianceRepository,
    IDiagnosisQuestionRepository,
)


class DiagnosisQuestionRepository(IDiagnosisQuestionRepository):
    def get_by_id(self, id: int):
        return Diagnosis_Questions.objects.filter(pk=id).first()


class DiagnosisRepository(DiagnosisRepositoryInterface):
    def save(self, diagnosis_data: dict):
        # Crear una instancia del modelo a partir de los datos del diccionario
        diagnosis = Diagnosis(**diagnosis_data)
        diagnosis.save()  # Guardar en la base de datos
        return diagnosis

    def get_by_id(self, diagnosis_id):
        return Diagnosis.objects.get(id=diagnosis_id)

    def get_by_corporate(self, corporate_id):
        return Diagnosis.objects.filter(
            is_for_corporate_group=True, corporate_group=corporate_id
        ).first()

    def get_all(self):
        return Diagnosis.objects.all()

    def get_unfinalized_diagnosis_for_company(self, company_id: int) -> Diagnosis:
        # Implementa la lógica específica aquí
        return Diagnosis.objects.filter(company=company_id, is_finalized=False).first()

    def get_by_date_elabored(self, date_elabored) -> Diagnosis:
        # Buscar diagnóstico existente por date_elabored
        return Diagnosis.objects.filter(date_elabored=date_elabored).first()

    def update(self, data_to_save: Diagnosis) -> Diagnosis:
        data_to_save.save()
        return data_to_save

    def get_by_diagnosis_and_requirement(self, diagnosis, requirement):
        return Checklist_Requirement.objects.filter(
            diagnosis=diagnosis, requirement=requirement
        ).first()


class CheckListRepository(CheckListRepositoryInterface):
    def get_checklists_by_company(self, company_id: int):
        return CheckList.objects.filter(company_id=company_id).select_related(
            "question__requirement"
        )

    def get_checklists_by_question_id_and_diagnosis_id(
        self, question_id: int, diagnosis_id: int
    ):
        return CheckList.objects.filter(
            question=question_id, diagnosis=diagnosis_id
        ).first()

    def massive_save(self, data_to_save):
        return CheckList.objects.bulk_create(data_to_save)

    def massive_update(self, data_to_save):
        return CheckList.objects.bulk_update(
            data_to_save,
            [
                "observation",
                "compliance",
                "is_articuled",
                "obtained_value",
                "verify_document",
            ],
        )


class CheckListRequirementRepository(CheckListRequirementRepositoryInterface):
    def save(self, checklist_requirement_data):

        checklist_requirement = Checklist_Requirement(**checklist_requirement_data)
        checklist_requirement.save()
        return checklist_requirement

    def save_or_update(self, checklist_requirement_data):
        diagnosis = checklist_requirement_data.get("diagnosis")
        requirement = checklist_requirement_data.get("requirement")
        compliance = checklist_requirement_data.get("compliance")

        checklist_requirement = Checklist_Requirement.objects.filter(
            diagnosis=diagnosis, requirement=requirement, compliance=compliance
        ).first()
        if checklist_requirement:
            # Si el registro ya existía, actualizar los campos con los nuevos datos
            for key, value in checklist_requirement_data.items():
                setattr(checklist_requirement, key, value)
        else:
            # Si no existe, crear uno nuevo
            checklist_requirement = Checklist_Requirement(**checklist_requirement_data)
        checklist_requirement.save()
        return checklist_requirement

    def get_checklists_requirement_by_diagnosis_id(self, id):
        return (
            Checklist_Requirement.objects.filter(diagnosis=id)
            .select_related("requirement", "compliance")
            .order_by("requirement__step")
        )

    def get_checklist_requirement_by_id_and_diagnosis_id(self, id, diagnosis_id):

        return Checklist_Requirement.objects.filter(
            pk=id, diagnosis=diagnosis_id
        ).first()

    def get_checklist_requirement_by_diagnosis_id(self, diagnosis_id):
        return Checklist_Requirement.objects.filter(diagnosis=diagnosis_id).first()

    def massive_delete(self, ids_to_delete):
        return Checklist_Requirement.objects.filter(id__in=ids_to_delete).delete(
            hard=True
        )

    def massive_save(self, data_to_save):
        return Checklist_Requirement.objects.bulk_create(data_to_save)

    def massive_update(self, data_to_save):
        return Checklist_Requirement.objects.bulk_update(
            data_to_save, ["observation", "compliance"]
        )

    def get_requirement_by_id(self, id):
        return Diagnosis_Requirement.objects.filter(pk=id).first()


class ComplianceRepository(IComplianceRepository):
    def get_compliance_by_id(self, id) -> Compliance:
        return Compliance.objects.get(pk=id)
