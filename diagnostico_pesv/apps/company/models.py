from django.db import models
from timestamps.models import SoftDeletes, Timestampable
from apps.sign.models import User
from apps.arl.models import Arl


class Mission(SoftDeletes, Timestampable):
    name = models.CharField(max_length=250, null=True, blank=True)


class CompanySize(SoftDeletes, Timestampable):
    name = models.CharField(max_length=255)


class SizeCriteria(SoftDeletes, Timestampable):
    name = models.TextField()
    vehicle_min = models.IntegerField(default=0, null=False)
    vehicle_max = models.IntegerField(
        default=0, null=True, db_comment="El valor NULL representa sin Limite"
    )
    driver_min = models.IntegerField(default=0, null=False)
    driver_max = models.IntegerField(
        default=0, null=True, db_comment="El valor NULL representa sin Limite"
    )


class MisionalitySizeCriteria(SoftDeletes, Timestampable):
    mission = models.ForeignKey(
        Mission, related_name="misionalidad_criteria", on_delete=models.CASCADE
    )
    size = models.ForeignKey(CompanySize, on_delete=models.CASCADE)
    criteria = models.ForeignKey(SizeCriteria, on_delete=models.CASCADE)


class Segments(SoftDeletes, Timestampable):
    name = models.CharField(max_length=100, unique=True, null=None)


# Create your models here.
class Company(SoftDeletes, Timestampable):
    name = models.CharField(max_length=100, unique=True, null=False)
    nit = models.CharField(max_length=20, unique=True, null=False)
    segment = models.ForeignKey(Segments, on_delete=models.SET_NULL, null=True)
    dependant = models.CharField(max_length=200, null=True)
    dependant_position = models.CharField(max_length=200, null=True)
    dependant_phone = models.CharField(max_length=20, null=True)
    activities_ciiu = models.CharField(max_length=255, null=True)
    email = models.CharField(max_length=200, null=True)
    acquired_certification = models.CharField(max_length=255, null=True)
    diagnosis = models.CharField(max_length=255, null=True)
    consultor = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, unique=True
    )
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, null=True)
    diagnosis_step = models.IntegerField(null=False, default=0)
    arl = models.ForeignKey(Arl, on_delete=models.SET_NULL, null=True, blank=False)
    size = models.ForeignKey(
        CompanySize, on_delete=models.SET_NULL, null=True, blank=False
    )  # Añadido


class VehicleQuestions(SoftDeletes, Timestampable):  # Cuestionario del diagnostico
    name = models.CharField(max_length=255, unique=True, null=None)


class Fleet(SoftDeletes, Timestampable):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    vehicle_question = models.ForeignKey(VehicleQuestions, on_delete=models.CASCADE)
    quantity_owned = models.IntegerField(default=0, null=False)
    quantity_third_party = models.IntegerField(default=0, null=False)
    quantity_arrended = models.IntegerField(default=0, null=False)
    quantity_contractors = models.IntegerField(default=0, null=False)
    quantity_intermediation = models.IntegerField(default=0, null=False)
    quantity_leasing = models.IntegerField(default=0, null=False)
    quantity_renting = models.IntegerField(default=0, null=False)


class DriverQuestion(SoftDeletes, Timestampable):
    name = models.CharField(max_length=255)


class Driver(SoftDeletes, Timestampable):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    driver_question = models.ForeignKey(DriverQuestion, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0, null=False)
