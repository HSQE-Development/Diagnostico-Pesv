from rest_framework import serializers
from .models import (
    Company,
    Segments,
    Mission,
    CompanySize,
    VehicleQuestions,
    Driver,
    Fleet,
    DriverQuestion,
    SizeCriteria,
    MisionalitySizeCriteria,
)
from apps.sign.models import User
from apps.sign.serializers import UserDetailSerializer
from apps.arl.models import Arl
from apps.arl.serializers import ArlSerializer


class MissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mission
        fields = ["id", "name"]


class CompanySizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanySize
        fields = ["id", "name"]


class SizeCriteriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SizeCriteria
        fields = [
            "id",
            "name",
            "vehicle_min",
            "vehicle_max",
            "driver_min",
            "driver_max",
        ]


class MisionalitySizeCriteriaSerializer(serializers.ModelSerializer):
    mission = serializers.PrimaryKeyRelatedField(
        queryset=Mission.objects.all(), write_only=True
    )
    mission_detail = MissionSerializer(source="mission", read_only=True)

    size = serializers.PrimaryKeyRelatedField(
        queryset=CompanySize.objects.all(), write_only=True
    )
    size_detail = CompanySizeSerializer(source="size", read_only=True)

    criteria = serializers.PrimaryKeyRelatedField(
        queryset=SizeCriteria.objects.all(), write_only=True
    )
    criteria_detail = SizeCriteriaSerializer(source="criteria", read_only=True)

    class Meta:
        model = MisionalitySizeCriteria
        fields = [
            "id",
            "mission",
            "mission_detail",
            "size",
            "size_detail",
            "criteria",
            "criteria_detail",
        ]


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

    mission = serializers.PrimaryKeyRelatedField(
        queryset=Mission.objects.all(), write_only=True
    )
    mission_detail = MissionSerializer(source="mission", read_only=True)
    arl = serializers.PrimaryKeyRelatedField(
        queryset=Arl.objects.all(), write_only=True
    )
    arl_detail = ArlSerializer(source="arl", read_only=True)
    misionality_size_criteria = serializers.SerializerMethodField()
    size = serializers.PrimaryKeyRelatedField(
        queryset=CompanySize.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    size_detail = CompanySizeSerializer(source="size", read_only=True)

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
            "mission",
            "mission_detail",
            "diagnosis_step",
            "arl",
            "arl_detail",
            "misionality_size_criteria",
            "size",
            "size_detail",
        ]

    def get_misionality_size_criteria(self, obj):
        # Get the related MisionalitySizeCriteria objects for this company
        misionality_size_criteria = MisionalitySizeCriteria.objects.filter(
            mission=obj.mission, size=obj.size
        )
        serializer = MisionalitySizeCriteriaSerializer(
            misionality_size_criteria, many=True
        )
        return serializer.data


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
