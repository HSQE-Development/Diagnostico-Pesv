from django.db import models
from timestamps.models import SoftDeletes, Timestampable


# Create your models here.
class Arl(SoftDeletes, Timestampable):
    name = models.CharField(null=False, unique=True, blank=False, max_length=255)
