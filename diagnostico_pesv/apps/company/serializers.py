from rest_framework import serializers
from .models import (
    Company,
    Segments,
    Mission,
    CompanySize,
    SizeCriteria,
    MisionalitySizeCriteria,
    Ciiu,
)
from apps.arl.models import Arl
from apps.arl.serializers import ArlSerializer
from apps.diagnosis.models import Diagnosis
from apps.sign.models import User
from apps.sign.serializers import UserDetailSerializer


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


class CiiuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ciiu
        fields = ["id", "name", "code"]


class DiagnosisInCompanySerializer(serializers.ModelSerializer):
    type = serializers.PrimaryKeyRelatedField(
        queryset=CompanySize.objects.all(), write_only=True, required=False
    )
    type_detail = CompanySizeSerializer(source="type", read_only=True)
    consultor = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, required=False, allow_null=True
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
            "in_progress",
            "external_count_complete",
            "is_for_corporate_group",
            "corporate_group",
        ]


class CompanySerializer(serializers.ModelSerializer):
    segment = serializers.PrimaryKeyRelatedField(
        queryset=Segments.objects.all(), write_only=True
    )
    segment_detail = SegmentSerializer(source="segment", read_only=True)

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
    ciius = serializers.PrimaryKeyRelatedField(
        queryset=Ciiu.objects.all(), many=True, required=False
    )
    ciius_detail = CiiuSerializer(source="ciius", read_only=True, many=True)

    company_diagnosis = DiagnosisInCompanySerializer(many=True, read_only=True)

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
            "dependant_position",
            "email",
            "acquired_certification",
            "mission",
            "mission_detail",
            "arl",
            "arl_detail",
            "misionality_size_criteria",
            "size",
            "size_detail",
            "ciius",
            "ciius_detail",
            "company_diagnosis",
            "enable_for_counting",
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
