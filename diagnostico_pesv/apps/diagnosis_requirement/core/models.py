from django.db import models
from timestamps.models import SoftDeletes, Timestampable
from apps.sign.models import User
from apps.company.models import CompanySize


# Create your models here.
class Diagnosis_Requirement(SoftDeletes, Timestampable):
    name = models.CharField(max_length=250, null=True, blank=False, unique=True)
    basic = models.BooleanField(default=False, null=False, blank=False)
    standard = models.BooleanField(default=False, null=False, blank=False)
    advanced = models.BooleanField(default=False, null=False, blank=False)
    step = models.IntegerField(default=None, null=True, blank=False)
    cycle = models.CharField(default=None, null=True, blank=False, max_length=2)


class Recomendation(SoftDeletes, Timestampable):
    name = models.TextField(null=True, blank=False)
    requirement = models.ForeignKey(
        Diagnosis_Requirement, on_delete=models.SET_NULL, null=True
    )
    basic = models.BooleanField(default=False, null=False, blank=False)
    standard = models.BooleanField(default=False, null=False, blank=False)
    advanced = models.BooleanField(default=False, null=False, blank=False)
    all = models.BooleanField(default=False, null=False, blank=False)


class WorkPlan_Recomendation(SoftDeletes, Timestampable):
    name = models.TextField(null=True, blank=False)
    requirement = models.ForeignKey(
        Diagnosis_Requirement, on_delete=models.SET_NULL, null=True
    )
