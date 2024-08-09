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


class Ciiu(SoftDeletes, Timestampable):
    name = models.CharField(null=True, blank=False, max_length=250)
    code = models.CharField(unique=True, null=True, blank=False, max_length=10)


# Create your models here.
class Company(SoftDeletes, Timestampable):
    name = models.CharField(max_length=100, unique=True, null=False)
    nit = models.CharField(max_length=20, unique=True, null=False)
    segment = models.ForeignKey(Segments, on_delete=models.SET_NULL, null=True)
    dependant = models.CharField(max_length=200, null=True)
    dependant_position = models.CharField(max_length=200, null=True)
    dependant_phone = models.CharField(max_length=20, null=True)
    email = models.CharField(max_length=200, null=True)
    acquired_certification = models.CharField(max_length=255, null=True)
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, null=True)
    arl = models.ForeignKey(Arl, on_delete=models.SET_NULL, null=True, blank=False)
    size = models.ForeignKey(
        CompanySize, on_delete=models.SET_NULL, null=True, blank=False
    )  # Añadido
    ciius = models.ManyToManyField(Ciiu, related_name="companies")
