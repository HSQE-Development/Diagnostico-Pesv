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
    name = models.CharField(max_length=100, unique=True, null=None)
    nit = models.CharField(max_length=20, unique=True, null=None)
    size = models.IntegerField()
    segment = models.ForeignKey(Segments, on_delete=models.SET_NULL, null=True)
    dependant = models.CharField(max_length=200, null=True)
    dependant_phone = models.CharField(max_length=20, null=True)
    activities_ciiu = models.CharField(max_length=255, null=True)
    email = models.CharField(max_length=200, null=True)
    acquired_certification = models.CharField(max_length=255, null=True)
    diagnosis = models.CharField(max_length=255, null=True)
    consultor = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, unique=True
    )
    dedication = models.ForeignKey(Dedication, on_delete=models.CASCADE, null=True)
    company_size = models.ForeignKey(CompanySize, on_delete=models.CASCADE, null=True)
