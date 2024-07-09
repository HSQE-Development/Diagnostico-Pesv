import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "diagnostico_pesv.settings")
django.setup()

from django.contrib.auth.models import Group
from apps.sign.models import User

Group.objects.get_or_create(name="SuperAdmin")
Group.objects.get_or_create(name="Admin")
Group.objects.get_or_create(name="Consultor")
# Agregar otros roles de ser necesario Group.objects.get_or_create(name="SuperAdmin")


def assign_role_to_user(user_id, role_name):
    try:
        user = User.objects.get(id=user_id)
        role = Group.objects.get(name=role_name)
        user.groups.add(role)
        user.save()
        print(f"Rol '{role_name}' asignado al usuario '{user.username}'")
    except User.DoesNotExist:
        print(f"Usuario con ID {user_id} no existe")
    except Group.DoesNotExist:
        print(f"Rol '{role_name}' no existe")


# Asigna el rol de SuperAdmin al usuario con ID 1
assign_role_to_user(user_id=1, role_name="SuperAdmin")

# Asigna el rol de Consultor al usuario con ID 2
assign_role_to_user(user_id=2, role_name="Consultor")
