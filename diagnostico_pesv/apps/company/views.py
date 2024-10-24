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
from apps.sign.models import User, QueryLog
from utils.functionUtils import validate_max_length, validate_min_length

logger = logging.getLogger(__name__)


# Create your views here.
class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    services = CompanyService()

    def get_queryset(self):
        arlId = self.request.query_params.get("arlId")
        queryset = Company.objects.filter(deleted_at__isnull=True)
        if arlId is not None:
            queryset = queryset.filter(arl=arlId)
        # if IsSuperAdmin().has_permission(
        #     user=self.request.user
        # ) or IsAdmin().has_permission(user=self.request.user):
        #     return Company.objects_with_deleted
        return queryset

    def create(self, request: Request, *args, **kwargs):
        try:
            user = request.user
            # Prepare data for validation and perform validation
            data = request.data.copy()
            external_user = data.get("external_user")
            data.pop("external_user", None)
            with transaction.atomic():
                transformed_data = self.prepare_data(data)

                # Deserialize and validate the data
                serializer = self.get_serializer(data=transformed_data)

                CompanyService.validate_nit(transformed_data.get("nit"))
                CompanyService.validate_name(transformed_data.get("name"))

                serializer.is_valid(raise_exception=True)

                # Validate using external service methods

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

                if external_user:
                    userInstance = User.objects.get(pk=user.id)
                    userInstance.external_step = 1
                    userInstance.save()

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

            if not self.services.has_no_active_diagnosis_company(company):
                return Response(
                    {
                        "error": "Esta empresa tiene diagnosticos activos, no se puede eliminar"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            company.delete()
            return Response(
                None,
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

    @action(detail=False, methods=["GET"])
    def find_company_by_nit(self, request: Request):
        nit = request.query_params.get("nit")
        ip_address = request.META.get("REMOTE_ADDR", "0.0.0.0")
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        if not nit or nit == 0:
            return Response(
                {"error": "El nit es obligatorio"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not validate_max_length(nit, 10):
            return Response(
                {"error": "El nit debe de ser de maximo 10 caracteres"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not validate_min_length(nit, 10):
            return Response(
                {"error": "El nit debe de ser de minimo 10 caracteres"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            try:
                # Intenta obtener la empresa por el NIT
                company = Company.objects.get(nit=nit)
                serializer = CompanySerializer(company)
                QueryLog.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    ip_address=ip_address,
                    action="find_company_by_nit",
                    http_method=request.method,
                    query_params=dict(request.query_params),
                    user_agent=user_agent,
                )
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Company.DoesNotExist:
                # Si no encuentra la empresa, envía una respuesta vacía
                QueryLog.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    ip_address=ip_address,
                    action="find_company_by_nit - company not found",
                    http_method=request.method,
                    query_params=dict(request.query_params),
                    user_agent=user_agent,
                )
                return Response({}, status=status.HTTP_200_OK)
        except Exception as ex:
            # Registra la excepción en QueryLog
            QueryLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                ip_address=ip_address,
                action=f"find_company_by_nit - error: {str(ex)}",
                http_method=request.method,
                query_params=dict(request.query_params),
                user_agent=user_agent,
            )
            return Response(
                {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
