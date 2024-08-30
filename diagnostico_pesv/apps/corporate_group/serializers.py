from rest_framework import serializers
from .models import *
from apps.company.models import Company
from apps.company.serializers import CompanySerializer


class CorporateGroupSerializer(serializers.ModelSerializer):
    company_diagnoses_corporate = serializers.SerializerMethodField()

    class Meta:
        model = Corporate
        fields = [
            "id",
            "name",
            "nit",
            "company_diagnoses_corporate",
        ]

    def get_company_diagnoses_corporate(self, obj):
        # Obtén las instancias relacionadas de Corporate_Company_Diagnosis
        diagnoses = Corporate_Company_Diagnosis.objects.filter(corporate=obj)
        return CorporateCompanyDiagnosisSerializer(diagnoses, many=True).data


class CorporateCompanyDiagnosisSerializer(serializers.ModelSerializer):
    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(), write_only=True
    )
    company_detail = CompanySerializer(source="company", read_only=True)

    class Meta:
        model = Corporate_Company_Diagnosis
        fields = [
            "id",
            "company",
            "company_detail",
        ]
