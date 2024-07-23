import traceback
from django.shortcuts import render
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    CompanySerializer,
    SegmentSerializer,
    MissionSerializer,
    CompanySizeSerializer,
    VehicleQuestionSerializer,
    DriverQuestionSerializer,
    DriverSerializer,
    FleetSerializer,
    MisionalitySizeCriteriaSerializer,
)
from .models import (
    Company,
    Segments,
    Mission,
    CompanySize,
    VehicleQuestions,
    Fleet,
    DriverQuestion,
    Driver,
    MisionalitySizeCriteria,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from apps.sign.permissions import IsSuperAdmin, IsConsultor, IsAdmin
import logging
from apps.sign.models import User
from utils import functionUtils
from apps.arl.models import Arl
from rest_framework.exceptions import NotFound, ValidationError
from http import HTTPMethod
from .service import CompanyService

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
            serializer = self.get_serializer(data=transformed_data)
            serializer.is_valid(raise_exception=True)

            # Validate using external service methods
            CompanyService.validate_nit(transformed_data.get("nit"))
            CompanyService.validate_consultor(transformed_data.get("consultor"))

            # Save the new Company instance
            self.perform_create(serializer)
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

    @action(detail=False)
    def findFleetsByCompanyId(self, request: Request):
        company_id = request.query_params.get("company")
        try:
            fleets = Fleet.objects.filter(deleted_at=None, company=company_id)
            serializer = FleetSerializer(fleets, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.error(f"Error en findFleetsByCompanyId: {str(ex)}")
            return Response(
                {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False)
    def findDriversByCompanyId(self, request: Request):
        company_id = request.query_params.get("company")
        try:
            drivers = Driver.objects.filter(deleted_at=None, company=company_id)
            serializer = DriverSerializer(drivers, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.error(f"Error en findDriversByCompanyId: {str(ex)}")
            return Response(
                {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=[HTTPMethod.POST])
    def saveAnswerCuestions(self, request: Request):
        try:
            company_id = request.data.get("company")
            vehicle_data = request.data.get("vehicleData", [])
            driver_data = request.data.get("driverData", [])

            company = self.get_company(company_id)
            total_vehicles, vehicle_errors = self.process_vehicle_data(
                company_id, vehicle_data
            )
            total_drivers, driver_errors = self.process_driver_data(
                company_id, driver_data
            )

            company.size = self.update_company_size(
                company, total_vehicles, total_drivers
            )
            company.diagnosis_step = 1
            company.save()

            if vehicle_errors or driver_errors:
                return self.build_error_response(vehicle_errors, driver_errors)

            return self.build_success_response(vehicle_data, driver_data)

        except Company.DoesNotExist:
            return Response(
                {"error": "Company not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as ex:
            logger.error(f"Error en saveAnswerCuestions: {str(ex)}")
            return Response(
                {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_company(self, company_id):
        return Company.objects.get(pk=company_id)

    def process_vehicle_data(self, company_id, vehicle_data):
        vehicle_errors = []
        total_vehicles = functionUtils.calculate_total_vehicles_quantities_for_company(
            vehicle_data
        )
        for vehicle in vehicle_data:
            vehicle["company"] = company_id
            fleet_instance = Fleet.objects.filter(
                company=company_id, vehicle_question=vehicle.get("vehicle_question")
            ).first()
            serializer_fleet = FleetSerializer(instance=fleet_instance, data=vehicle)
            if serializer_fleet.is_valid():
                serializer_fleet.save()
            else:
                vehicle_errors.append(serializer_fleet.errors)
        return total_vehicles, vehicle_errors

    def process_driver_data(self, company_id, driver_data):
        driver_errors = []
        total_drivers = functionUtils.calculate_total_drivers_quantities_for_company(
            driver_data
        )
        for driver in driver_data:
            driver["company"] = company_id
            driver_instance = Driver.objects.filter(
                company=company_id, driver_question=driver.get("driver_question")
            ).first()
            serializer_driver = DriverSerializer(instance=driver_instance, data=driver)
            if serializer_driver.is_valid():
                serializer_driver.save()
            else:
                driver_errors.append(serializer_driver.errors)
        return total_drivers, driver_errors

    def update_company_size(self, company, total_vehicles, total_drivers):
        company_size_id = CompanyService.determine_company_size(
            company.mission.id, total_vehicles, total_drivers
        )
        return CompanySize.objects.get(pk=company_size_id)

    def build_error_response(self, vehicle_errors, driver_errors):
        return Response(
            {"vehicleErrors": vehicle_errors, "driverErrors": driver_errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def build_success_response(self, vehicle_data, driver_data):
        return Response(
            {"vehicleData": vehicle_data, "driverData": driver_data},
            status=status.HTTP_201_CREATED,
        )


# @api_view(["POST"])
# @authentication_classes([JWTAuthentication])
# @permission_classes([IsAuthenticated])  # Requiere autenticación JWT
# def saveAnswerCuestions(request: Request):
#     """Ester servicio se puede mejorar en logica y reutilizaion de codigo por favor cualquier idea sera bienvenida"""
#     try:
#         vehicle_data = request.data.get("vehicleData", [])
#         driver_data = request.data.get("driverData", [])

#         vehicle_errors = []
#         driver_errors = []

#         # Procesar y validar datos de vehículos
#         for vehicle in vehicle_data:
#             company_id = vehicle.get("company")

#             company: Company = Company.objects.get(pk=company_id)
# total_vehicles = (
#     functionUtils.calculate_total_vehicles_quantities_for_company(
#         vehicle_data, company_id
#     )
# )
# total_drivers = (
#     functionUtils.calculate_total_drivers_quantities_for_company(
#         driver_data, company_id
#     )
# )

#             company_size_name = functionUtils.determine_company_size(
#                 company.dedication.id, total_vehicles, total_drivers
#             )
#             # print(company_size_name)
#             company_size = CompanySize.objects.get(
#                 name__iexact=functionUtils.eliminar_tildes(company_size_name),
#                 dedication=company.dedication.id,
#             )
#             print(company_size)

#             # Guardar el tamaño de la organización en la instancia de Company
#             company.company_size = company_size
#             company.diagnosis_step = 1
#             company.save()

#             # Procesar el vehículo
#             fleet_instance = Fleet.objects.filter(
#                 company=company_id, vehicle_question=vehicle.get("vehicle_question")
#             ).first()

#             serializer_fleet = FleetSerializer(instance=fleet_instance, data=vehicle)
#             if serializer_fleet.is_valid():
#                 serializer_fleet.save()
#             else:
#                 vehicle_errors.append(serializer_fleet.errors)

#         # Procesar y validar datos de conductores
#         for driver in driver_data:
#             company_id = driver.get("company")

#             company = get_object_or_404(Company, pk=company_id)
# total_vehicles = (
#     functionUtils.calculate_total_vehicles_quantities_for_company(
#         vehicle_data, company_id
#     )
# )
#             total_drivers = (
#                 functionUtils.calculate_total_drivers_quantities_for_company(
#                     driver_data, company_id
#                 )
#             )

#             company_size_name = functionUtils.determine_company_size(
#                 company.dedication.id, total_vehicles, total_drivers
#             )

#             company_size = CompanySize.objects.get(
#                 name__iexact=functionUtils.eliminar_tildes(company_size_name),
#                 dedication=company.dedication.id,
#             )

#             # Guardar el tamaño de la organización en la instancia de Company
#             company.company_size = company_size
#             company.diagnosis_step = 1
#             company.save()

#             # Procesar el conductor
# driver_instance = Driver.objects.filter(
#     company=company_id, driver_question=driver.get("driver_question")
# ).first()

#             serializer_driver = DriverSerializer(instance=driver_instance, data=driver)
#             if serializer_driver.is_valid():
#                 serializer_driver.save()
#             else:
#                 driver_errors.append(serializer_driver.errors)

#         if vehicle_errors or driver_errors:
#             return Response(
#                 {"vehicleErrors": vehicle_errors, "driverErrors": driver_errors},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         return Response(
#             {
#                 "vehicleData": vehicle_data,
#                 "driverData": driver_data,
#             },
#             status=status.HTTP_201_CREATED,
#         )

#     except Exception as ex:
#         tb_str = traceback.format_exc()  # Formatear la traza del error
#         return Response(
#             {"error": str(ex), "traceback": tb_str},
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR,
#         )


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
