import traceback
from django.shortcuts import render
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    CompanySerializer,
    SegmentSerializer,
    DedicationSerializer,
    CompanySizeSerializer,
    VehicleQuestionSerializer,
    DriverQuestionSerializer,
    DriverSerializer,
    FleetSerializer,
)
from .models import (
    Company,
    Segments,
    Dedication,
    CompanySize,
    VehicleQuestions,
    Fleet,
    DriverQuestion,
    Driver,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from apps.sign.permissions import IsSuperAdmin, IsConsultor, IsAdmin
import logging
from apps.sign.models import User
from utils import functionUtils

logger = logging.getLogger(__name__)


# Create your views here.
@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def findAll(request: Request):
    """
    Consulta todos los datos segun el criterio del filter
    """
    try:
        if IsSuperAdmin.has_permission(user=request.user) or IsAdmin.has_permission(
            user=request.user
        ):
            companies = Company.objects_with_deleted
        else:
            companies = Company.objects.filter(deleted_at=None)

        serializer = CompanySerializer(companies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as ex:
        logger.error(f"Error en findAll: {str(ex)}")
        return Response(
            {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def save(request: Request):
    try:
        nit = request.data.get("nit")
        consultor_id = request.data.get("consultor")
        dependant_phone = request.data.get("dependant_phone")
        dependant_position = request.data.get("dependant_position")

        valuesToNone = [dependant_phone, dependant_position]
        transformed_values = [
            functionUtils.blank_to_null(value) for value in valuesToNone
        ]
        request.data["dependant_phone"] = transformed_values[0]
        request.data["dependant_position"] = transformed_values[1]
        try:
            consultor = User.objects.get(pk=consultor_id)
        except User.DoesNotExist:
            return Response(
                {"error": "No se encontro el consultor"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if Company.objects.filter(consultor=consultor_id, deleted_at=None).exists():
            return Response(
                {"error": "Este consultor ya se encuentra asignado"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            Company.objects.get(nit=nit)
            return Response(
                {"error": "La Empresa que intenta registrar ya existe"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Company.DoesNotExist:
            pass  # Si no existe, continuamos con la creación de la compañía
        serializer = CompanySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as ex:
        return Response(
            {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def findById(request: Request, id):
    """
    Consulta segun el id proporcionado en la url
    """
    try:
        company = Company.objects_with_deleted.get(pk=id)
        serializer = CompanySerializer(company)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as ex:
        return Response(
            {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["PATCH"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def update(request: Request):
    """
    Actualiza segun el id proporcionado en el body del cuerpoo, el ID no se pide en la url
    """
    try:
        id = request.data.get("id")
        if id is None:
            return Response(
                {"error": "No se proporciona el id que se va a actualizar"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        name = request.data.get("name")
        nit = request.data.get("nit")
        size = request.data.get("size")
        segment_id = request.data.get("segment")
        dependant = request.data.get("dependant")
        dependant_phone = request.data.get("dependant_phone")
        activities_ciiu = request.data.get("activities_ciiu")
        email = request.data.get("email")
        acquired_certification = request.data.get("acquired_certification")
        diagnosis = request.data.get("diagnosis")
        consultor_id = request.data.get("consultor")
        dedication_id = request.data.get("dedication")
        company_size_id = request.data.get("company_size")

        company = Company.objects_with_deleted.get(pk=id)

        if name is not None:
            company.name = name
        if nit is not None:
            company.nit = nit
        if size is not None:
            company.size = size
        if segment_id is not None:
            segment = Segments.objects.get(pk=segment_id)
            if not segment:
                return Response(
                    {"error": "No se encontro el segmento"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            company.segment = segment
        if dependant is not None:
            company.dependant = dependant
        if dependant_phone is not None:
            company.dependant_phone = dependant_phone
        if activities_ciiu is not None:
            company.activities_ciiu = activities_ciiu
        if email is not None:
            company.email = email
        if acquired_certification is not None:
            company.acquired_certification = acquired_certification
        if diagnosis is not None:
            company.diagnosis = diagnosis
        if consultor_id is not None:
            if company.consultor and company.consultor.id == consultor_id:
                pass
            else:
                try:
                    consultor = User.objects.get(pk=consultor_id)
                except User.DoesNotExist:
                    return Response(
                        {"error": "No se encontro el consultor"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if Company.objects.filter(consultor=consultor).exists():
                    return Response(
                        {"error": "Este consultor ya se encuentra asignado"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                company.consultor = consultor
        if dedication_id is not None:
            if company.dedication and company.dedication.id == dedication_id:
                pass
            else:
                try:
                    dedication = Dedication.objects.get(pk=dedication_id)
                except Dedication.DoesNotExist:
                    return Response(
                        {"error": "No se encontro la misionalidad"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                company.dedication = dedication
        if company_size_id is not None:
            if company.company_size and company.company_size.id == company_size_id:
                pass
            else:
                try:
                    companySize = CompanySize.objects.get(pk=company_size_id)
                except CompanySize.DoesNotExist:
                    return Response(
                        {"error": "No se encontro el tamaño asociado"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                company.company_size = companySize

        company.save()
        serializer = CompanySerializer(company)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as ex:
        return Response(
            {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["DELETE"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def delete(request: Request, id):
    """
    Elimina segun el id proporcionado en la url, se usa soft deletes, osea no elimina el registro como tal
    """
    try:
        company = Company.objects_with_deleted.get(pk=id)
        company.consultor = None
        company.delete()
        serializer = CompanySerializer(company)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as ex:
        return Response(
            {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def findAllSegments(request: Request):
    """
    Consulta todos los datos segun el criterio del filter
    """
    try:
        segments = Segments.objects.filter(deleted_at=None)
        serializer = SegmentSerializer(segments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as ex:
        logger.error(f"Error en findAllSegments: {str(ex)}")
        return Response(
            {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def findAllDedications(request: Request):
    """
    Consulta todos los datos segun el criterio del filter
    """
    try:
        dedications = Dedication.objects.filter(deleted_at=None)
        serializer = DedicationSerializer(dedications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as ex:
        logger.error(f"Error en findAllDedications: {str(ex)}")
        return Response(
            {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def findcompanySizeByDedicactionId(request: Request, id):
    """
    Consulta todos los datos segun el criterio del filter
    """
    try:
        companySizes = CompanySize.objects.filter(deleted_at=None, dedication=id)
        serializer = CompanySizeSerializer(companySizes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as ex:
        logger.error(f"Error en findAllDedications: {str(ex)}")
        return Response(
            {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def findAllVehicleQuestions(request: Request):
    """
    Consulta todos los datos segun el criterio del filter
    """
    try:
        vehicleCuestions = VehicleQuestions.objects.filter(deleted_at=None)
        serializer = VehicleQuestionSerializer(vehicleCuestions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as ex:
        logger.error(f"Error en findAllDedications: {str(ex)}")
        return Response(
            {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def findAllDriverQuestions(request: Request):
    """
    Consulta todos los datos segun el criterio del filter
    """
    try:
        driverQuestions = DriverQuestion.objects.filter(deleted_at=None)
        serializer = DriverQuestionSerializer(driverQuestions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as ex:
        logger.error(f"Error en findAllDedications: {str(ex)}")
        return Response(
            {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def findFleetsByCompanyId(request: Request, companyId):
    """
    Consulta todos los datos segun el criterio del filter
    """
    try:
        fleets = Fleet.objects.filter(deleted_at=None, company=companyId)
        serializer = FleetSerializer(fleets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as ex:
        logger.error(f"Error en findAllDedications: {str(ex)}")
        return Response(
            {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def findDriversByCompanyId(request: Request, companyId):
    """
    Consulta todos los datos segun el criterio del filter
    """
    try:
        drivers = Driver.objects.filter(deleted_at=None, company=companyId)
        serializer = DriverSerializer(drivers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as ex:
        logger.error(f"Error en findAllDedications: {str(ex)}")
        return Response(
            {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def saveAnswerCuestions(request: Request):
    """Ester servicio se puede mejorar en logica y reutilizaion de codigo por favor cualquier idea sera bienvenida"""
    try:
        vehicle_data = request.data.get("vehicleData", [])
        driver_data = request.data.get("driverData", [])

        vehicle_errors = []
        driver_errors = []

        # Procesar y validar datos de vehículos
        for vehicle in vehicle_data:
            company_id = vehicle.get("company")

            company: Company = Company.objects.get(pk=company_id)
            total_vehicles = (
                functionUtils.calculate_total_vehicles_quantities_for_company(
                    vehicle_data, company_id
                )
            )
            total_drivers = (
                functionUtils.calculate_total_drivers_quantities_for_company(
                    driver_data, company_id
                )
            )

            company_size_name = functionUtils.determine_company_size(
                company.dedication.id, total_vehicles, total_drivers
            )

            company_size = get_object_or_404(
                CompanySize, name=company_size_name, dedication=company.dedication.id
            )

            # Guardar el tamaño de la organización en la instancia de Company
            company.company_size = company_size
            company.diagnosis_step = 1
            company.save()

            # Procesar el vehículo
            fleet_instance = Fleet.objects.filter(
                company=company_id, vehicle_question=vehicle.get("vehicle_question")
            ).first()

            serializer_fleet = FleetSerializer(instance=fleet_instance, data=vehicle)
            if serializer_fleet.is_valid():
                serializer_fleet.save()
            else:
                vehicle_errors.append(serializer_fleet.errors)

        # Procesar y validar datos de conductores
        for driver in driver_data:
            company_id = driver.get("company")

            company = get_object_or_404(Company, pk=company_id)
            total_vehicles = (
                functionUtils.calculate_total_vehicles_quantities_for_company(
                    vehicle_data, company_id
                )
            )
            total_drivers = (
                functionUtils.calculate_total_drivers_quantities_for_company(
                    driver_data, company_id
                )
            )

            company_size_name = functionUtils.determine_company_size(
                company.dedication.id, total_vehicles, total_drivers
            )

            company_size = get_object_or_404(
                CompanySize, name=company_size_name, dedication=company.dedication.id
            )

            # Guardar el tamaño de la organización en la instancia de Company
            company.company_size = company_size
            company.diagnosis_step = 1
            company.save()

            # Procesar el conductor
            driver_instance = Driver.objects.filter(
                company=company_id, driver_question=driver.get("driver_question")
            ).first()

            serializer_driver = DriverSerializer(instance=driver_instance, data=driver)
            if serializer_driver.is_valid():
                serializer_driver.save()
            else:
                driver_errors.append(serializer_driver.errors)

        if vehicle_errors or driver_errors:
            return Response(
                {"vehicleErrors": vehicle_errors, "driverErrors": driver_errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "vehicleData": vehicle_data,
                "driverData": driver_data,
            },
            status=status.HTTP_201_CREATED,
        )

    except Exception as ex:
        tb_str = traceback.format_exc()  # Formatear la traza del error
        return Response(
            {"error": str(ex), "traceback": tb_str},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def findSizeByCounts(request):
    min_vehicle = request.query_params.get("min_vehicle")
    max_vehicle = request.query_params.get("max_vehicle")
    min_driver = request.query_params.get("min_driver")
    max_driver = request.query_params.get("max_driver")

    queryset = CompanySize.objects.all()
    if min_vehicle is not None:
        queryset = queryset.filter(vehicle_min__gte=min_vehicle)
    if max_vehicle is not None:
        queryset = queryset.filter(vehicle_max__lte=max_vehicle)
    if min_driver is not None:
        queryset = queryset.filter(driver_min__gte=min_driver)
    if max_driver is not None:
        queryset = queryset.filter(driver_max__lte=max_driver)

    serializer = CompanySizeSerializer(queryset, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
