from django.db import models
from timestamps.models import SoftDeletes, Timestampable
from apps.diagnosis_requirement.core.models import Diagnosis_Requirement
from apps.company.models import Company


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
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        related_name="company_diagnosis",
    )
    date_elabored = models.DateField(null=False, blank=False, unique=True)
    is_finalized = models.BooleanField(default=False, null=False)
    schedule = models.CharField(null=True, blank=False, max_length=100)
    sequence = models.CharField(null=True, blank=False, max_length=100)


class CheckList(SoftDeletes, Timestampable):
    question = models.ForeignKey(
        Diagnosis_Questions, on_delete=models.SET_NULL, null=True, blank=False
    )
    diagnosis = models.ForeignKey(
        Diagnosis, on_delete=models.SET_NULL, null=True, blank=False
    )
    compliance = models.ForeignKey(
        Compliance, on_delete=models.SET_NULL, null=True, blank=False
    )
    # obtained_value = models.IntegerField(default=0, null=False, blank=False)
    obtained_value = models.FloatField(default=0, null=False, blank=False)
    verify_document = models.TextField(null=True, default=None, blank=False)
    observation = models.TextField(null=False, default="SIN OBSERVACIONES", blank=False)
    is_articuled = models.BooleanField(default=True)


class Fleet(SoftDeletes, Timestampable):
    diagnosis = models.ForeignKey(Diagnosis, on_delete=models.CASCADE)
    vehicle_question = models.ForeignKey(VehicleQuestions, on_delete=models.CASCADE)
    quantity_owned = models.IntegerField(default=0, null=False)
    quantity_third_party = models.IntegerField(default=0, null=False)
    quantity_arrended = models.IntegerField(default=0, null=False)
    quantity_contractors = models.IntegerField(default=0, null=False)
    quantity_intermediation = models.IntegerField(default=0, null=False)
    quantity_leasing = models.IntegerField(default=0, null=False)
    quantity_renting = models.IntegerField(default=0, null=False)
    quantity_employees = models.IntegerField(default=0, null=False)


class Driver(SoftDeletes, Timestampable):
    diagnosis = models.ForeignKey(Diagnosis, on_delete=models.CASCADE)
    driver_question = models.ForeignKey(DriverQuestion, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0, null=False)


class Checklist_Requirement(SoftDeletes, Timestampable):
    diagnosis = models.ForeignKey(Diagnosis, on_delete=models.CASCADE)
    requirement = models.ForeignKey(
        Diagnosis_Requirement, on_delete=models.SET_NULL, null=True
    )
    compliance = models.ForeignKey(
        Compliance, on_delete=models.SET_NULL, null=True, blank=False
    )
    observation = models.TextField(blank=False, null=True)
