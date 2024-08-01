from apps.diagnosis_requirement.application.interfaces import (
    DiagnosisRequirementRepositoryInterface,
)
from apps.company.application.enums import *
from typing import List
from ..core.models import *


class DiagnosisRequirementUseCases:
    def __init__(self, repository: DiagnosisRequirementRepositoryInterface):
        self.repository = repository

    def get_diagnosis_requirements_by_company_size(
        self, size_id
    ) -> List[Diagnosis_Requirement]:
        if size_id == CompanySizeEnum.BASICO.value:
            return self.repository.get_by_basic()
        elif size_id == CompanySizeEnum.ESTANDAR.value:
            return self.repository.get_by_standard()
        elif size_id == CompanySizeEnum.AVANZADO.value:
            return self.repository.get_by_advanced()
        else:
            raise ValueError("Tamaño de empresa no válido.")
