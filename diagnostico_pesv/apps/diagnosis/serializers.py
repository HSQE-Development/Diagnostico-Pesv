from rest_framework import serializers
from .models import *
from apps.diagnosis_requirement.core.models import (
    Diagnosis_Requirement,
)
from apps.diagnosis_requirement.infraestructure.serializers import (
    Diagnosis_RequirementSerializer,
)
from apps.sign.serializers import UserDetailSerializer


class VehicleQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleQuestions
        fields = [
            "id",
            "name",
        ]


class DriverQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverQuestion
        fields = [
            "id",
            "name",
        ]


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


class Diagnosis_QuestionsChecklistSerializer(serializers.ModelSerializer):

    compliance = serializers.PrimaryKeyRelatedField(
        queryset=Compliance.objects.all(), write_only=True
    )
    compliance_detail = ComplianceSerializer(source="compliance", read_only=True)
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
            "compliance_detail",
            "compliance",
        ]


class CompanySizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanySize
        fields = ["id", "name"]


class DiagnosisSerializer(serializers.ModelSerializer):

    type = serializers.PrimaryKeyRelatedField(
        queryset=CompanySize.objects.all(), write_only=True
    )
    type_detail = CompanySizeSerializer(source="type", read_only=True)
    # company = serializers.PrimaryKeyRelatedField(
    #     queryset=Company.objects.all(), write_only=True
    # )
    # company_detail = CompanySerializer(source="company", read_only=True)
    consultor = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True
    )
    consultor_detail = UserDetailSerializer(source="consultor", read_only=True)

    class Meta:
        model = Diagnosis
        fields = [
            "id",
            "company",
            "date_elabored",
            "is_finalized",
            "diagnosis_step",
            "type",
            "type_detail",
            "consultor",
            "consultor_detail",
            "mode_ejecution",
            "schedule",
            "sequence",
            "observation",
        ]
        extra_kwargs = {"date_elabored": {"allow_null": True, "required": False}}


class CheckListSerializer(serializers.ModelSerializer):
    compliance = serializers.PrimaryKeyRelatedField(
        queryset=Compliance.objects.all(), write_only=True
    )
    compliance_detail = ComplianceSerializer(source="compliance", read_only=True)
    diagnosis = serializers.PrimaryKeyRelatedField(
        queryset=Diagnosis.objects.all(), write_only=True
    )
    diagnosis_detail = DiagnosisSerializer(source="diagnosis", read_only=True)

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
            "diagnosis",
            "diagnosis_detail",
            "question",
            "question_detail",
            "compliance",
            "compliance_detail",
            "observation",
            "is_articuled",
        ]

    def create(self, validated_data):
        question = validated_data.pop("question")
        diagnosis = validated_data.pop("diagnosis")
        compliance = validated_data.pop("compliance")

        fleet_instance = CheckList.objects.create(
            question=question,
            diagnosis=diagnosis,
            compliance=compliance,
            **validated_data
        )

        return fleet_instance


class FleetSerializer(serializers.ModelSerializer):
    vehicle_question = serializers.PrimaryKeyRelatedField(
        queryset=VehicleQuestions.objects.all(), write_only=True
    )
    vehicle_question_detail = VehicleQuestionSerializer(
        source="vehicle_question", read_only=True
    )

    diagnosis = serializers.PrimaryKeyRelatedField(
        queryset=Diagnosis.objects.all(), write_only=True
    )
    diagnosis_detail = DiagnosisSerializer(source="diagnosis", read_only=True)

    class Meta:
        model = Fleet
        fields = [
            "id",
            "quantity_owned",
            "quantity_third_party",
            "quantity_arrended",
            "quantity_contractors",
            "quantity_intermediation",
            "quantity_leasing",
            "quantity_renting",
            "vehicle_question",
            "quantity_employees",
            "vehicle_question_detail",
            "diagnosis",
            "diagnosis_detail",
        ]

    def create(self, validated_data):
        vehicle_question = validated_data.pop("vehicle_question")
        diagnosis = validated_data.pop("diagnosis")

        fleet_instance = Fleet.objects.create(
            vehicle_question=vehicle_question, diagnosis=diagnosis, **validated_data
        )

        return fleet_instance


class DriverSerializer(serializers.ModelSerializer):
    driver_question = serializers.PrimaryKeyRelatedField(
        queryset=DriverQuestion.objects.all(), write_only=True
    )
    driver_question_detail = DriverQuestionSerializer(
        source="driver_question", read_only=True
    )
    diagnosis = serializers.PrimaryKeyRelatedField(
        queryset=Diagnosis.objects.all(), write_only=True
    )
    diagnosis_detail = DiagnosisSerializer(source="diagnosis", read_only=True)

    class Meta:
        model = Driver
        fields = [
            "id",
            "quantity",
            "driver_question",
            "driver_question_detail",
            "diagnosis",
            "diagnosis_detail",
        ]

    def create(self, validated_data):
        driver_question = validated_data.pop("driver_question")
        diagnosis = validated_data.pop("diagnosis")

        driver_instance = Driver.objects.create(
            driver_question=driver_question, diagnosis=diagnosis, **validated_data
        )

        return driver_instance
