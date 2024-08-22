from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status, viewsets
from .models import *
from .serializers import *
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import (
    action,
)
from django.db import transaction
from http import HTTPMethod


class CustomPagination(PageNumberPagination):
    page_size = 2  # Tamaño de página por defecto
    page_size_query_param = "page_size"
    max_page_size = 100


# Create your views here.
class CorporateGroupViewSet(viewsets.ModelViewSet):
    queryset = Corporate.objects.all()
    serializer_class = CorporateGroupSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        # Ordenar el queryset por el campo 'id' (o cualquier campo adecuado)
        return Corporate.objects.all().order_by("id")

    def create(self, request: Request, *args, **kwargs):
        try:
            with transaction.atomic():
                companies_ids = request.data.get("companies", [])
                diagnosis_ids = request.data.get("diagnosis")
                name = request.data.get("name", "")
                corporate = Corporate(name=name)
                corporate.save()

                companies = Company.objects.filter(id__in=companies_ids)
                corporate.companies.set(companies)
                if diagnosis_ids:
                    dagnosis = Diagnosis.objects.filter(id__in=diagnosis_ids)
                    corporate.diagnoses.set(dagnosis)
                else:
                    corporate.diagnoses.set([])

                serializer = self.get_serializer(corporate)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as ex:
            return Response(
                {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False)
    def companies_not_in_corporate(self, request: Request):
        from apps.company.serializers import (
            CompanySerializer,
        )  # Para evitar dependencias circulares

        corporate_id = request.query_params.get("corporate", 0)
        try:
            corporate = Corporate.objects.get(id=corporate_id)
        except Corporate.DoesNotExist:
            return Response(
                {"error": "El grupo empresarial no existe"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

            # Obtener todas las compañías que no están asociadas a este Corporate
        companies_not_in_corporate = Company.objects.exclude(
            id__in=Corporate_Company_Diagnosis.objects.filter(
                corporate=corporate
            ).values_list("company_id", flat=True)
        ).distinct()  # Usar distinct() para evitar duplicados

        # Aplicar paginación
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(companies_not_in_corporate, request)
        if page is not None:
            serializer = CompanySerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        # Si no hay paginación, devolver todos los datos
        serializer = CompanySerializer(companies_not_in_corporate, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=[HTTPMethod.POST])
    def add_or_remove_company_of_group_by_group_id(self, request: Request):
        action = request.data.get("action")
        corporate_id = request.data.get("group")
        company_id = request.data.get("company")

        if not action or action not in ["add", "delete"]:
            return Response(
                {"error": "Acción inválida. Use 'add' o 'delete'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                company = Company.objects.get(id=company_id)
                corporate = Corporate.objects.get(id=corporate_id)

                if action == "add":
                    corporate.companies.add(company)
                elif action == "delete":
                    corporate.companies.remove(company)

                corporate.save()
                serializer = CompanySerializer(company)
                return Response(serializer.data, status=status.HTTP_200_OK)
        except Company.DoesNotExist:
            return Response(
                {"error": "La empresa no existe"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Corporate.DoesNotExist:
            return Response(
                {"error": "El grupo empresarial no existe"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as ex:
            return Response(
                {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
