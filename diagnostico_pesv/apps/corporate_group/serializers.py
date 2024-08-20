from rest_framework import serializers
from .models import *
from apps.diagnosis.models import Diagnosis
from apps.diagnosis.serializers import DiagnosisSerializer
from apps.company.models import Company
from apps.company.serializers import CompanySerializer


class CorporateGroupSerializer(serializers.ModelSerializer):
    company_diagnoses_corporate = serializers.SerializerMethodField()

    class Meta:
        model = Corporate
        fields = [
            "id",
            "name",
            "company_diagnoses_corporate",
        ]

    def get_company_diagnoses_corporate(self, obj):
        # Obtén las instancias relacionadas de Corporate_Company_Diagnosis
        diagnoses = Corporate_Company_Diagnosis.objects.filter(corporate=obj)
        return CorporateCompanyDiagnosisSerializer(diagnoses, many=True).data


class CorporateCompanyDiagnosisSerializer(serializers.ModelSerializer):
    diagnosis = serializers.PrimaryKeyRelatedField(
        queryset=Diagnosis.objects.all(), write_only=True
    )
    diagnosis_detail = DiagnosisSerializer(source="diagnosis", read_only=True)
    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(), write_only=True
    )
    company_detail = CompanySerializer(source="company", read_only=True)

    class Meta:
        model = Corporate
        fields = [
            "id",
            "company",
            "company_detail",
            "diagnosis",
            "diagnosis_detail",
        ]
