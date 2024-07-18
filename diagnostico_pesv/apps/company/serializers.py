from rest_framework import serializers
from .models import (
    Company,
    Segments,
    Dedication,
    CompanySize,
    VehicleQuestions,
    Driver,
    Fleet,
    DriverQuestion,
)
from apps.sign.models import User
from apps.sign.serializers import UserDetailSerializer
from apps.arl.models import Arl
from apps.arl.serializers import ArlSerializer


class DedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dedication
        fields = ["id", "name"]


class CompanySizeSerializer(serializers.ModelSerializer):
    dedication = serializers.PrimaryKeyRelatedField(
        queryset=Dedication.objects.all(), write_only=True
    )
    dedication_detail = DedicationSerializer(source="dedication", read_only=True)

    class Meta:
        model = CompanySize
        fields = ["id", "name", "description", "dedication", "dedication_detail"]


class SegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Segments
        fields = ["id", "name"]


class CompanySerializer(serializers.ModelSerializer):
    segment = serializers.PrimaryKeyRelatedField(
        queryset=Segments.objects.all(), write_only=True
    )
    segment_detail = SegmentSerializer(source="segment", read_only=True)

    consultor = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True
    )
    consultor_detail = UserDetailSerializer(source="consultor", read_only=True)

    dedication = serializers.PrimaryKeyRelatedField(
        queryset=Dedication.objects.all(), write_only=True
    )
    dedication_detail = DedicationSerializer(source="dedication", read_only=True)

    company_size = serializers.PrimaryKeyRelatedField(
        queryset=CompanySize.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    company_size_detail = CompanySizeSerializer(
        source="company_size", required=False, read_only=True, allow_null=True
    )
    arl = serializers.PrimaryKeyRelatedField(
        queryset=Arl.objects.all(), write_only=True
    )
    arl_detail = ArlSerializer(source="arl", read_only=True)

    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "nit",
            "segment",
            "segment_detail",
            "dependant",
            "dependant_phone",
            "activities_ciiu",
            "email",
            "acquired_certification",
            "diagnosis",
            "consultor",
            "consultor_detail",
            "dedication",
            "dedication_detail",
            "company_size",
            "company_size_detail",
            "diagnosis_step",
            "arl",
            "arl_detail",
        ]

    def validate(self, data):
        # Si 'company_size' puede ser null, entonces no es obligatorio
        if "company_size" not in data:
            data["company_size"] = None
        return data


class VehicleQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleQuestions
        fields = [
            "id",
            "name",
        ]


class FleetSerializer(serializers.ModelSerializer):
    vehicle_question = serializers.PrimaryKeyRelatedField(
        queryset=VehicleQuestions.objects.all(), write_only=True
    )
    vehicle_question_detail = VehicleQuestionSerializer(
        source="vehicle_question", read_only=True
    )

    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(), write_only=True
    )
    company_detail = CompanySerializer(source="company", read_only=True)

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
            "vehicle_question_detail",
            "company",
            "company_detail",
        ]

    def create(self, validated_data):
        vehicle_question = validated_data.pop("vehicle_question")
        company = validated_data.pop("company")

        fleet_instance = Fleet.objects.create(
            vehicle_question=vehicle_question, company=company, **validated_data
        )

        return fleet_instance


class DriverQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverQuestion
        fields = [
            "id",
            "name",
        ]


class DriverSerializer(serializers.ModelSerializer):
    driver_question = serializers.PrimaryKeyRelatedField(
        queryset=DriverQuestion.objects.all(), write_only=True
    )
    driver_question_detail = DriverQuestionSerializer(
        source="driver_question", read_only=True
    )
    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(), write_only=True
    )
    company_detail = CompanySerializer(source="company", read_only=True)

    class Meta:
        model = Driver
        fields = [
            "id",
            "quantity",
            "driver_question",
            "driver_question_detail",
            "company",
            "company_detail",
        ]

    def create(self, validated_data):
        driver_question = validated_data.pop("driver_question")
        company = validated_data.pop("company")

        driver_instance = Driver.objects.create(
            driver_question=driver_question, company=company, **validated_data
        )

        return driver_instance
