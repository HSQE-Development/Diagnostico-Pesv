from django.db import models
from timestamps.models import SoftDeletes, Timestampable
from apps.diagnosis_requirement.core.models import Diagnosis_Requirement
from apps.company.models import Company, CompanySize
from apps.sign.models import User


class VehicleQuestions(SoftDeletes, Timestampable):  # Cuestionario del diagnostico
    name = models.CharField(max_length=255, unique=True, null=None)


class DriverQuestion(SoftDeletes, Timestampable):
    name = models.CharField(max_length=255)


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


class Diagnosis(SoftDeletes, Timestampable):
    MODOS = [
        ("presencial", "Presencial"),
        ("virtual", "Virtual"),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        related_name="company_diagnosis",
    )
    type = models.ForeignKey(
        CompanySize,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        related_name="diagnosis_type",
    )
    date_elabored = models.DateField(null=False, blank=False)
    is_finalized = models.BooleanField(default=False, null=False)
    in_progress = models.BooleanField(default=False, null=True)
    schedule = models.CharField(null=True, blank=False, max_length=100)
    sequence = models.CharField(null=True, blank=False, max_length=100)
    diagnosis_step = models.IntegerField(null=False, default=0)
    consultor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    mode_ejecution = models.CharField(
        max_length=100, choices=MODOS, default="presencial"
    )
    observation = models.TextField(blank=False, null=True)


class CheckList(SoftDeletes, Timestampable):
    question = models.ForeignKey(
        Diagnosis_Questions, on_delete=models.SET_NULL, null=True, blank=False
    )
    diagnosis = models.ForeignKey(
        Diagnosis, on_delete=models.CASCADE, null=True, blank=False
    )
    compliance = models.ForeignKey(
        Compliance, on_delete=models.SET_NULL, null=True, blank=False
    )
    # obtained_value = models.IntegerField(default=0, null=False, blank=False)
    obtained_value = models.FloatField(default=0, null=False, blank=False)
    verify_document = models.TextField(null=True, default=None, blank=False)
    observation = models.TextField(null=False, default="SIN OBSERVACIONES", blank=False)
    is_articuled = models.BooleanField(default=True)


class Checklist_Requirement(SoftDeletes, Timestampable):
    diagnosis = models.ForeignKey(Diagnosis, on_delete=models.CASCADE)
    requirement = models.ForeignKey(
        Diagnosis_Requirement, on_delete=models.SET_NULL, null=True
    )
    compliance = models.ForeignKey(
        Compliance, on_delete=models.SET_NULL, null=True, blank=False
    )
    observation = models.TextField(blank=False, null=True)
