from rest_framework import serializers
from .models import *
from apps.diagnosis_requirement.models import Diagnosis_Requirement
from apps.diagnosis_requirement.serializers import Diagnosis_RequirementSerializer


class Diagnosis_TypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diagnosis_Type
        fields = ["id", "name"]


class Diagnosis_QuestionsSerializer(serializers.ModelSerializer):

    requirement = serializers.PrimaryKeyRelatedField(
        queryset=Diagnosis_Requirement.objects.all(), write_only=True
    )
    requirement_detail = Diagnosis_RequirementSerializer(
        source="requirement", read_only=True
    )
    diagnosis_type = serializers.PrimaryKeyRelatedField(
        queryset=Diagnosis_Type.objects.all(), write_only=True
    )
    diagnosis_type_detail = Diagnosis_TypeSerializer(
        source="diagnosis_type", read_only=True
    )

    class Meta:
        model = Diagnosis_Questions
        fields = [
            "id",
            "name",
            "cycle",
            "step",
            "variable_value",
            "requirement",
            "requirement_detail",
            "diagnosis_type",
            "diagnosis_type_detail",
        ]
