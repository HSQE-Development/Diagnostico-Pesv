from rest_framework import serializers
from .models import Company, Segments, Dedication, CompanySize
from apps.sign.models import User
from apps.sign.serializers import UserDetailSerializer


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
        queryset=CompanySize.objects.all(), write_only=True
    )
    company_size_detail = CompanySizeSerializer(source="company_size", read_only=True)

    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "nit",
            "size",
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
        ]
