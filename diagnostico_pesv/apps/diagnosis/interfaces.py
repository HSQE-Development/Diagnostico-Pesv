from abc import ABC, abstractmethod
from apps.diagnosis.models import (
    Diagnosis,
    Checklist_Requirement,
    Compliance,
    CheckList,
    Diagnosis_Questions,
)
from typing import List
from apps.diagnosis_requirement.core.models import Diagnosis_Requirement


class DiagnosisRepositoryInterface(ABC):
    @abstractmethod
    def save(self, diagnosis_data: dict) -> Diagnosis:
        pass

    @abstractmethod
    def get_by_id(self, diagnosis_id: int) -> Diagnosis:
        pass

    @abstractmethod
    def get_all(self):
        pass

    @abstractmethod
    def get_unfinalized_diagnosis_for_company(self, company_id: int) -> Diagnosis:
        pass

    @abstractmethod
    def get_by_id(self, diagnosis_id: int) -> Diagnosis:
        pass

    @abstractmethod
    def get_by_date_elabored(self, date_elabored) -> Diagnosis:
        pass

    @abstractmethod
    def update(self, data_to_save: Diagnosis) -> Diagnosis:
        pass


class IDiagnosisQuestionRepository(ABC):
    @abstractmethod
    def get_by_id(self, id: int) -> Diagnosis_Questions | None:
        pass


class CheckListRepositoryInterface(ABC):
    @abstractmethod
    def get_checklists_by_company(self, company_id: int):
        pass

    @abstractmethod
    def get_checklists_by_question_id_and_diagnosis_id(
        self, question_id: int, diagnosis_id: int
    ) -> CheckList | None:
        pass

    @abstractmethod
    def massive_save(self, data_to_save):
        pass

    @abstractmethod
    def massive_update(self, data_to_save):
        pass


class CheckListRequirementRepositoryInterface(ABC):
    @abstractmethod
    def save(self, checklist_requirement_data: dict) -> Checklist_Requirement:
        pass

    @abstractmethod
    def get_checklists_requirement_by_diagnosis_id(self, id):
        """Obtiene una lista de Checklist_Requirement basada en el ID de diagnóstico."""
        pass

    @abstractmethod
    def get_checklist_requirement_by_id_and_diagnosis_id(
        self, id, diagnosis_id
    ) -> Checklist_Requirement | None:
        pass

    @abstractmethod
    def get_requirement_by_id(self, id) -> Diagnosis_Requirement:
        pass

    @abstractmethod
    def massive_save(self, data_to_save):
        pass

    @abstractmethod
    def massive_delete(self, ids_to_delete):
        pass

    @abstractmethod
    def massive_update(self, data_to_save):
        pass


class IComplianceRepository(ABC):
    @abstractmethod
    def get_compliance_by_id(self, id) -> Compliance:
        pass
