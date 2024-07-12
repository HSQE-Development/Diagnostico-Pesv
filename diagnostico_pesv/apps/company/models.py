from django.db import models
from timestamps.models import SoftDeletes, Timestampable
from apps.sign.models import User


class Dedication(SoftDeletes, Timestampable):
    name = models.CharField(max_length=250, null=True, blank=True)


class CompanySize(SoftDeletes, Timestampable):
    dedication = models.ForeignKey(
        Dedication, related_name="sizes", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    description = models.TextField()


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
    dedication = models.ForeignKey(Dedication, on_delete=models.CASCADE, null=True)
    company_size = models.ForeignKey(
        CompanySize, on_delete=models.SET_NULL, null=True, blank=True, default=None
    )


class VehicleQuestions(SoftDeletes, Timestampable):  # Cuestionario del diagnostico
    name = models.CharField(max_length=255, unique=True, null=None)


class Fleet(SoftDeletes, Timestampable):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    vehicle_question = models.ForeignKey(VehicleQuestions, on_delete=models.CASCADE)
    quantity_owned = models.IntegerField(default=0, null=None)
    quantity_third_party = models.IntegerField(default=0, null=None)
    quantity_arrended = models.IntegerField(default=0, null=None)
    quantity_contractors = models.IntegerField(default=0, null=None)
    quantity_intermediation = models.IntegerField(default=0, null=None)
    quantity_leasing = models.IntegerField(default=0, null=None)
    quantity_renting= models.IntegerField(default=0, null=None)


class DriverQuestion(SoftDeletes, Timestampable):
    name = models.CharField(max_length=255)


class Driver(SoftDeletes, Timestampable):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    driver_question = models.ForeignKey(DriverQuestion, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0, null=None)
