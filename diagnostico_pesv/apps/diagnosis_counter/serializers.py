from rest_framework import serializers
from apps.company.models import Company
from apps.company.serializers import CompanySerializer
from apps.diagnosis.models import Diagnosis, VehicleQuestions, DriverQuestion
from apps.diagnosis.serializers import (
    VehicleQuestionSerializer,
    DiagnosisSerializer,
    DriverQuestionSerializer,
)
from .models import Fleet, Driver, Diagnosis_Counter


class DiagnosisCounterSerializer(serializers.ModelSerializer):

    diagnosis = serializers.PrimaryKeyRelatedField(
        queryset=Diagnosis.objects.all(), write_only=True
    )
    diagnosis_detail = DiagnosisSerializer(source="diagnosis", read_only=True)

    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(), write_only=True
    )
    company_detail = CompanySerializer(source="company", read_only=True)

    class Meta:
        model = Diagnosis_Counter
        fields = [
            "id",
            "company",
            "company_detail",
            "diagnosis",
            "diagnosis_detail",
        ]


class FleetSerializer(serializers.ModelSerializer):
    vehicle_question = serializers.PrimaryKeyRelatedField(
        queryset=VehicleQuestions.objects.all(), write_only=True
    )
    vehicle_question_detail = VehicleQuestionSerializer(
        source="vehicle_question", read_only=True
    )

    diagnosis_counter = serializers.PrimaryKeyRelatedField(
        queryset=Diagnosis_Counter.objects.all(), write_only=True
    )
    diagnosis_counter_detail = DiagnosisCounterSerializer(
        source="diagnosis_counter", read_only=True
    )

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
            "diagnosis_counter",
            "diagnosis_counter_detail",
        ]

    def create(self, validated_data):
        vehicle_question = validated_data.pop("vehicle_question")
        diagnosis_counter = validated_data.pop("diagnosis_counter")

        fleet_instance = Fleet.objects.create(
            vehicle_question=vehicle_question,
            diagnosis_counter=diagnosis_counter,
            **validated_data
        )

        return fleet_instance


class DriverSerializer(serializers.ModelSerializer):
    driver_question = serializers.PrimaryKeyRelatedField(
        queryset=DriverQuestion.objects.all(), write_only=True
    )
    driver_question_detail = DriverQuestionSerializer(
        source="driver_question", read_only=True
    )
    diagnosis_counter = serializers.PrimaryKeyRelatedField(
        queryset=Diagnosis_Counter.objects.all(), write_only=True
    )
    diagnosis_counter_detail = DiagnosisCounterSerializer(
        source="diagnosis_counter", read_only=True
    )

    class Meta:
        model = Driver
        fields = [
            "id",
            "quantity",
            "driver_question",
            "driver_question_detail",
            "diagnosis_counter",
            "diagnosis_counter_detail",
        ]

    def create(self, validated_data):
        driver_question = validated_data.pop("driver_question")
        diagnosis_counter = validated_data.pop("diagnosis_counter")

        driver_instance = Driver.objects.create(
            driver_question=driver_question,
            diagnosis_counter=diagnosis_counter,
            **validated_data
        )

        return driver_instance
