from typing import List
from apps.diagnosis_requirement.core.models import Diagnosis_Requirement
from abc import ABC, abstractmethod
from apps.diagnosis.models import Checklist_Requirement


class DiagnosisRequirementRepositoryInterface(ABC):
    @abstractmethod
    def get_by_basic(self) -> List[Diagnosis_Requirement]:
        pass

    @abstractmethod
    def get_by_standard(self) -> List[Diagnosis_Requirement]:
        pass

    @abstractmethod
    def get_by_advanced(self) -> List[Diagnosis_Requirement]:
        pass
