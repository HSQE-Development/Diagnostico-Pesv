from django.db import models
from apps.company.models import Company
from apps.diagnosis.models import Diagnosis
from timestamps.models import SoftDeletes, Timestampable


# Create your models here.
class Corporate(SoftDeletes, Timestampable):
    name = models.CharField(max_length=200, null=True)


class Corporate_Company_Diagnosis(SoftDeletes, Timestampable):
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True)
    diagnosis = models.ForeignKey(Diagnosis, on_delete=models.SET_NULL, null=True)
    corporate = models.ForeignKey(
        Corporate,
        on_delete=models.SET_NULL,
        null=True,
        related_name="company_diagnoses_corporate",
    )
