from django.db import models
from timestamps.models import SoftDeletes, Timestampable
from apps.sign.models import User


# Create your models here.
class Diagnosis_Requirement(SoftDeletes, Timestampable):
    name = models.CharField(max_length=250, null=True, blank=False, unique=True)
