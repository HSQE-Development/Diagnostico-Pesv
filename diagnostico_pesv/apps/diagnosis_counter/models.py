from django.db import models
from timestamps.models import SoftDeletes, Timestampable
from apps.company.models import Company, CompanySize
from apps.diagnosis.models import Diagnosis, VehicleQuestions, DriverQuestion


class Diagnosis_Counter(SoftDeletes, Timestampable):
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        related_name="company_counter",
    )
    diagnosis = models.ForeignKey(Diagnosis, on_delete=models.CASCADE)
    size = models.ForeignKey(
        CompanySize, on_delete=models.SET_NULL, null=True, blank=False
    )  # Añadido
    observation = models.TextField(null=True, default=None, blank=False)


class Fleet(SoftDeletes, Timestampable):
    diagnosis_counter = models.ForeignKey(
        Diagnosis_Counter, on_delete=models.SET_NULL, null=True, default=None
    )
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
    diagnosis_counter = models.ForeignKey(
        Diagnosis_Counter, on_delete=models.SET_NULL, null=True, default=None
    )
    driver_question = models.ForeignKey(
        DriverQuestion, on_delete=models.SET_NULL, null=True
    )
    quantity = models.IntegerField(default=0, null=False)
