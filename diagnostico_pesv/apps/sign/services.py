from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import EmailMessage
import random
import string
from .models import User


def send_temporary_password_email(user, temp_password):
    send_mail(
        "Contraseña temporal",
        f"Hola {user.first_name} {user.last_name}, tu contraseña temporal es: {temp_password}",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def get_existing_usernames() -> set:
    """
    Obtiene todos los nombres de usuario existentes en la base de datos.

    :return: Un conjunto de nombres de usuario existentes.
    """
    return set(User.objects.values_list("username", flat=True))


def generate_username(
    first_name: str,
    last_name: str,
    unique: bool = False,
    existing_usernames: set = None,
) -> str:
    """
    Genera un nombre de usuario basado en el nombre y apellido proporcionados.

    :param first_name: El primer nombre del usuario.
    :param last_name: El apellido del usuario.
    :param unique: Si True, intentará generar un nombre de usuario único.
    :param existing_usernames: Un conjunto de nombres de usuario existentes para verificar la unicidad.
    :return: Un nombre de usuario generado.
    """
    if existing_usernames is None:
        existing_usernames = set()

    # Crear una base para el nombre de usuario
    first_initial = first_name[0].lower() if first_name else ""
    last_name_lower = last_name.lower() if last_name else ""
    base_username = f"{first_initial}{last_name_lower}"

    # Si es necesario garantizar unicidad, añade un número
    if unique:
        username = base_username
        suffix = 1
        while username in existing_usernames:
            username = f"{base_username}{suffix}"
            suffix += 1
        return username
    else:
        return base_username
