from rest_framework import serializers
from ..core.models import *


class Diagnosis_RequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diagnosis_Requirement
        fields = ["id", "name", "cycle", "step"]


class Recomendation_Serializer(serializers.ModelSerializer):
    requirement = serializers.PrimaryKeyRelatedField(
        queryset=Diagnosis_Requirement.objects.all(), write_only=True
    )
    requirement_detail = Diagnosis_RequirementSerializer(
        source="requirement", read_only=True
    )

    class Meta:
        model = Recomendation
        fields = ["id", "name", "requirement", "requirement_detail"]
