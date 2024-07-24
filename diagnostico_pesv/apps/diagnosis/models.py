from django.db import models
from timestamps.models import SoftDeletes, Timestampable
from apps.diagnosis_requirement.models import Diagnosis_Requirement
from apps.company.models import Company


class Diagnosis_Type(SoftDeletes, Timestampable):
    name = models.CharField(max_length=250, null=True, blank=True, unique=True)


# Create your views here.
class Diagnosis_Questions(SoftDeletes, Timestampable):
    name = models.TextField(null=True, blank=False, default=None)
    requirement = models.ForeignKey(
        Diagnosis_Requirement,
        related_name="requirements",
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
    )
    variable_value = models.IntegerField(default=0, null=False, blank=False)


class Compliance(SoftDeletes, Timestampable):
    name = models.CharField(max_length=250, null=True, blank=True, unique=True)


class CheckList(SoftDeletes, Timestampable):
    question = models.ForeignKey(
        Diagnosis_Questions, on_delete=models.SET_NULL, null=True, blank=False
    )
    company = models.ForeignKey(
        Company, on_delete=models.SET_NULL, null=True, blank=False
    )
    compliance = models.ForeignKey(
        Compliance, on_delete=models.SET_NULL, null=True, blank=False
    )
    # obtained_value = models.IntegerField(default=0, null=False, blank=False)
    obtained_value = models.FloatField(default=0, null=False, blank=False)
    verify_document = models.TextField(null=True, default=None, blank=False)
    observation = models.TextField(null=False, default="SIN OBSERVACIONES", blank=False)
    is_articuled = models.BooleanField(default=True)
