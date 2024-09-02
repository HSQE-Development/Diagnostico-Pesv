import base64
import logging
import csv
from io import StringIO
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    CompanySerializer,
    SegmentSerializer,
    MissionSerializer,
    MisionalitySizeCriteriaSerializer,
    CiiuSerializer,
)
from .models import (
    Company,
    Segments,
    Mission,
    CompanySize,
    MisionalitySizeCriteria,
    Ciiu,
)
from apps.diagnosis.models import VehicleQuestions, DriverQuestion
from apps.diagnosis.serializers import (
    VehicleQuestionSerializer,
    DriverQuestionSerializer,
)
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from apps.sign.permissions import IsSuperAdmin, IsAdmin
from utils import functionUtils
from rest_framework.exceptions import ValidationError
from http import HTTPMethod
from .service import CompanyService
from django.db import transaction

logger = logging.getLogger(__name__)


# Create your views here.
class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        arlId = self.request.query_params.get("arlId")
        if arlId is not None:
            return Company.objects.filter(arl=arlId)
        if IsSuperAdmin.has_permission(
            user=self.request.user
        ) or IsAdmin.has_permission(user=self.request.user):
            return Company.objects_with_deleted
        return Company.objects.all()

    def create(self, request: Request, *args, **kwargs):
        try:
            # Prepare data for validation and perform validation
            transformed_data = self.prepare_data(request.data)

            # Deserialize and validate the data
            serializer = self.get_serializer(data=transformed_data)
            serializer.is_valid(raise_exception=True)

            # Validate using external service methods
            CompanyService.validate_nit(transformed_data.get("nit"))

            # Save the new Company instance
            self.perform_create(serializer)

            # Get the created Company instance
            company_instance = serializer.instance

            # Handle the many-to-many relationships
            ciuus_codes = transformed_data.get("ciius", [])
            ciuus_ids = [int(identifier) for identifier in ciuus_codes]

            # Find or create CIIU instances based on the provided codes
            ciius = Ciiu.objects.filter(pk__in=ciuus_ids)

            # Set the many-to-many relationship
            company_instance.ciius.set(ciius)
            headers = self.get_success_headers(serializer.data)

            return Response(
                serializer.data, status=status.HTTP_201_CREATED, headers=headers
            )
        except CompanyService.NitAlreadyExists as ex:
            return Response({"error": str(ex)}, status=status.HTTP_400_BAD_REQUEST)
        except CompanyService.ConsultorNotFound as ex:
            return Response({"error": str(ex)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            return Response(
                {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def prepare_data(self, data):
        """
        Transform data before validation.
        Converts empty strings to None.
        """
        dependant_phone = data.get("dependant_phone")
        dependant_position = data.get("dependant_position")

        # Convert empty strings to None
        data["dependant_phone"] = functionUtils.blank_to_null(dependant_phone)
        data["dependant_position"] = functionUtils.blank_to_null(dependant_position)

        return data

    def retrieve(self, request: Request, pk=None):
        """
        Obtiene una empresa específica por su ID.
        """
        try:
            # Obtener el objeto según el ID
            instance = self.get_object()
            # Serializar el objeto
            serializer = self.get_serializer(instance)
            # Devolver una respuesta con los datos serializados
            return Response(serializer.data)
        except Company.DoesNotExist:
            # Manejar el caso en que la empresa no se encuentra
            return Response(
                {"error": "La empresa no existe."}, status=status.HTTP_404_NOT_FOUND
            )

    def update(self, request: Request, *args, **kwargs):
        """
        Actualiza segun el id proporcionado en la url
        """
        company = self.get_object()
        serializer = self.get_serializer(company, data=request.data, partial=True)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            return Response(
                {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        try:
            company: Company = self.get_object()
            company.consultor = None
            company.delete()
            return Response(
                {"detail": "Object deleted successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except Exception as ex:
            return Response(
                {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # Actions personalizadas para funciones en especifico
    @action(detail=False)
    def findAllSegments(self, request):
        """
        Consulta todos los datos segun el criterio del filter
        """
        try:
            segments = Segments.objects.all()
            serializer = SegmentSerializer(segments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.error(f"Error en findAllSegments: {str(ex)}")
            return Response(
                {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False)
    def findAllMissions(self, request):
        """
        Consulta todos los datos segun el criterio del filter
        """
        try:
            missions = Mission.objects.all()
            serializer = MissionSerializer(missions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.error(f"Error en findAllSegments: {str(ex)}")
            return Response(
                {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False)
    def findCompanySizeByMissionId(self, request: Request):
        """
        Consulta todos los datos segun el criterio del filter
        """
        mission_id = request.query_params.get("mission")
        try:
            missions = MisionalitySizeCriteria.objects.filter(mission=mission_id)
            serializer = MisionalitySizeCriteriaSerializer(missions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.error(f"Error en findAllSegments: {str(ex)}")
            return Response(
                {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False)
    def findAllVehicleQuestions(self, request: Request):
        try:
            vehicleCuestions = VehicleQuestions.objects.all()
            serializer = VehicleQuestionSerializer(vehicleCuestions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.error(f"Error en findAllVehicleQuestions: {str(ex)}")
            return Response(
                {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False)
    def findAllDriverQuestions(self, request: Request):
        try:
            driverQuestions = DriverQuestion.objects.all()
            serializer = DriverQuestionSerializer(driverQuestions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.error(f"Error en findAllDriverQuestions: {str(ex)}")
            return Response(
                {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=[HTTPMethod.POST])
    def uploadCiiuCodes(self, request: Request):
        data = request.data.get("ciiu_csv_base64")
        if not data:
            return Response(
                {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
            )
        try:

            try:
                decoded_file = base64.b64decode(data)
                csv_file = StringIO(decoded_file.decode("utf-8"))
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            reader = csv.DictReader(csv_file, delimiter=";")
            errors = []
            processed_data = []
            with transaction.atomic():
                for row in reader:
                    code = row.get("Codigo")
                    description = row.get("Nombre")
                    if Ciiu.objects.filter(code=code).exists():
                        error = {"error": f"El codgio CIIU {code} ya existe"}
                        errors.append(error)

                    ciiu_data = {"code": code, "name": description}
                    serializer = CiiuSerializer(data=ciiu_data)
                    if serializer.is_valid():
                        serializer.save()
                        processed_data.append(serializer.data)
                    else:
                        error = {
                            field: f"at code {code} - {error}"
                            for field, error in serializer.errors.items()
                        }
                        errors.append(error)
                        return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(processed_data, status=status.HTTP_201_CREATED)

    @action(detail=False)
    def findCiiuByCode(self, request: Request):
        ciiu_code = request.query_params.get("ciiu_code", "")
        try:
            ciiu = None
            if ciiu_code:
                ciiu = Ciiu.objects.filter(code__icontains=ciiu_code)
            else:
                ciiu = Ciiu.objects.all()

            serializer = CiiuSerializer(ciiu, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response(
                {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False)
    def diagnosis_by_company(self, request: Request):
        companies = Company.objects.all()
        diagnostics_data = [
            {
                "name": company.name,
                "total_diagnostics": company.company_diagnosis.count(),
                "finalized_diagnostics": company.company_diagnosis.filter(
                    is_finalized=True
                ).count(),
                "in_progress_diagnostics": company.company_diagnosis.filter(
                    in_progress=True
                ).count(),
            }
            for company in companies
        ]

        return Response(diagnostics_data)


# @api_view(["POST"])
# @authentication_classes([JWTAuthentication])
# @permission_classes([IsAuthenticated])
# def findSizeByCounts(request):
#     min_vehicle = request.query_params.get("min_vehicle")
#     max_vehicle = request.query_params.get("max_vehicle")
#     min_driver = request.query_params.get("min_driver")
#     max_driver = request.query_params.get("max_driver")

#     queryset = CompanySize.objects.all()
#     if min_vehicle is not None:
#         queryset = queryset.filter(vehicle_min__gte=min_vehicle)
#     if max_vehicle is not None:
#         queryset = queryset.filter(vehicle_max__lte=max_vehicle)
#     if min_driver is not None:
#         queryset = queryset.filter(driver_min__gte=min_driver)
#     if max_driver is not None:
#         queryset = queryset.filter(driver_max__lte=max_driver)

#     serializer = CompanySizeSerializer(queryset, many=True)
#     return Response(serializer.data, status=status.HTTP_200_OK)
