from apps.diagnosis_requirement.application.interfaces import (
    DiagnosisRequirementRepositoryInterface,
)
from apps.diagnosis_requirement.core.models import Diagnosis_Requirement
from ..application.interfaces import *


class DiagnosisRequirementRepository(DiagnosisRequirementRepositoryInterface):
    def get_by_basic(self):
        return Diagnosis_Requirement.objects.filter(basic=True)

    def get_by_standard(self):
        return Diagnosis_Requirement.objects.filter(standard=True)

    def get_by_advanced(self):
        return Diagnosis_Requirement.objects.filter(advanced=True)
