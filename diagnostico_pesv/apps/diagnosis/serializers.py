from rest_framework import serializers
from .models import *
from apps.diagnosis_requirement.models import Diagnosis_Requirement
from apps.diagnosis_requirement.serializers import Diagnosis_RequirementSerializer
from apps.company.serializers import CompanySerializer


class Diagnosis_TypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diagnosis_Type
        fields = ["id", "name"]


class ComplianceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Compliance
        fields = ["id", "name"]


class Diagnosis_QuestionsSerializer(serializers.ModelSerializer):

    requirement = serializers.PrimaryKeyRelatedField(
        queryset=Diagnosis_Requirement.objects.all(), write_only=True
    )
    requirement_detail = Diagnosis_RequirementSerializer(
        source="requirement", read_only=True
    )

    class Meta:
        model = Diagnosis_Questions
        fields = [
            "id",
            "name",
            "variable_value",
            "requirement",
            "requirement_detail",
        ]


class CheckListSerializer(serializers.ModelSerializer):
    compliance = serializers.PrimaryKeyRelatedField(
        queryset=Compliance.objects.all(), write_only=True
    )
    compliance_detail = ComplianceSerializer(source="compliance", read_only=True)
    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(), write_only=True
    )
    company_detail = CompanySerializer(source="company", read_only=True)

    question = serializers.PrimaryKeyRelatedField(
        queryset=Diagnosis_Questions.objects.all(), write_only=True
    )
    question_detail = Diagnosis_QuestionsSerializer(source="question", read_only=True)

    class Meta:
        model = CheckList
        fields = [
            "id",
            "obtained_value",
            "verify_document",
            "company",
            "company_detail",
            "question",
            "question_detail",
            "compliance",
            "compliance_detail",
            "observation",
            "is_articuled",
        ]

    def create(self, validated_data):
        question = validated_data.pop("question")
        company = validated_data.pop("company")
        compliance = validated_data.pop("compliance")

        fleet_instance = CheckList.objects.create(
            question=question, company=company, compliance=compliance, **validated_data
        )

        return fleet_instance
