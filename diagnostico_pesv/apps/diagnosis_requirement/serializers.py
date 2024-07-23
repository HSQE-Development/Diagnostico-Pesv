from rest_framework import serializers
from .models import *


class Diagnosis_RequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diagnosis_Requirement
        fields = ["id", "name", "cycle", "step"]
