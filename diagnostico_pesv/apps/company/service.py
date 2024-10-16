# service.py
from .models import *
from apps.sign.models import User
from django.core.exceptions import ObjectDoesNotExist


class CompanyService:
    class NitAlreadyExists(Exception):
        pass

    class NametAlreadyExists(Exception):
        pass

    class ConsultorNotFound(Exception):
        pass

    @staticmethod
    def validate_nit(nit):
        if Company.objects.filter(nit=nit).exists():
            raise CompanyService.NitAlreadyExists("La empresa con este NIT ya existe.")

    @staticmethod
    def validate_name(name):
        if Company.objects.filter(name=name).exists():
            raise CompanyService.NametAlreadyExists(
                "La empresa con este nombre ya existe."
            )

    @staticmethod
    def validate_consultor(consultor_id):
        if not User.objects.filter(pk=consultor_id).exists():
            raise CompanyService.ConsultorNotFound("No se encontró el consultor.")
        if Company.objects.filter(consultor=consultor_id, deleted_at=None).exists():
            raise CompanyService.ConsultorNotFound(
                "Este consultor ya se encuentra asignado."
            )

    @staticmethod
    def determine_company_size(mission_id, total_vehicles: int, total_drivers: int):
        try:
            # Obtener todos los criterios de tamaño para la misión específica
            misionality_criteria = MisionalitySizeCriteria.objects.filter(
                mission_id=mission_id
            )
            selected_size = None
            for criteria in misionality_criteria:
                size_criteria = criteria.criteria

                # Comprobar los valores de vehículos y conductores
                vehicle_in_range = (
                    size_criteria.vehicle_min
                    <= total_vehicles
                    <= (size_criteria.vehicle_max or float("inf"))
                )
                driver_in_range = (
                    size_criteria.driver_min
                    <= total_drivers
                    <= (size_criteria.driver_max or float("inf"))
                )
                # Si ambos criterios se cumplen, devolvemos el tamaño mayor
                if vehicle_in_range and driver_in_range:
                    return criteria.size.id

                # Si solo uno de los criterios se cumple, guardamos temporalmente el tamaño
                if vehicle_in_range or driver_in_range:
                    selected_size = criteria.size.id

            # Si se encontró al menos un criterio que coincida, devolvemos el tamaño seleccionado
            if selected_size:
                return selected_size

            raise ValueError(
                f"No se pudo determinar el tamaño de la organización para mission_id={mission_id} con total_vehicles={total_vehicles} y total_drivers={total_drivers}."
            )
        except ObjectDoesNotExist:
            raise ValueError(f"El valor de mission_id={mission_id} no es válido.")

    @staticmethod
    def get_company(company_id):
        return Company.objects.get(pk=company_id)

    @staticmethod
    def update_company_size(company, total_vehicles, total_drivers):
        company_size_id = CompanyService.determine_company_size(
            company.mission.id, total_vehicles, total_drivers
        )
        return CompanySize.objects.get(pk=company_size_id)

    @staticmethod
    def update_company_size_highest(company, total_vehicles, total_drivers):
        company_size_id = CompanyService.determine_company_size(
            company.mission.id, total_vehicles, total_drivers
        )
        return CompanySize.objects.get(pk=company_size_id)
