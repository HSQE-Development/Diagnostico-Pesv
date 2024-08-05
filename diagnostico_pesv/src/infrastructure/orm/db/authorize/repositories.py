import dataclasses
import json
from typing import List, Tuple

from src.domain.user import UserEntity
from src.infrastructure.orm.db.authorize.models import User
from src.infrastructure.orm.db.authorize.tasks import get_user, save_user
from src.infrastructure.utils.authorize.utils import get_tokens_for_user
from src.interface.repositories.exceptions import EntityDoesNotExist
from src.infrastructure.utils.general import save_avatar
from django.db import transaction


class UserDatabaseRepository:
    def get(self, id: int) -> UserEntity:
        user = User.objects.filter(pk=id).values().first()
        if not user:
            raise EntityDoesNotExist(f"{id} user id does not exist")
        return UserEntity(**user)

    def list_all(self) -> List[UserEntity]:
        return list(map(lambda x: UserEntity(**x), User.objects.values()))

    def get_user_by_email(self, email: str) -> UserEntity:
        user = User.objects.get(email=email)
        return UserEntity(**user)

    def check_password(self, user: UserEntity, password: str) -> bool:
        try:
            user = User.objects.get(email=user.email)
            return user.check_password(password)
        except User.DoesNotExist:
            return False

    def save(self, user: UserEntity) -> UserEntity:
        with transaction.atomic():
            avatar_path = save_avatar(user.avatar)

            django_user = User(
                username=user.username,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                is_active=user.is_active,
            )
            # Asegúrate de guardar atributos adicionales correctamente
            django_user.cedula = user.cedula
            django_user.avatar = avatar_path
            django_user.licensia_sst = user.licensia_sst

            django_user.save()

            user_entity_data = {
                "id": django_user.id,
                "username": django_user.username,
                "email": django_user.email,
                "first_name": django_user.first_name,
                "last_name": django_user.last_name,
                "is_active": django_user.is_active,
                "licensia_sst": user.licensia_sst,  # Si corresponde
                "cedula": user.cedula,
                "avatar": avatar_path,
                "date_joined": django_user.date_joined,
                "is_staff": django_user.is_staff,
                "is_superuser": django_user.is_superuser,
                "last_login": django_user.last_login,
                "password": django_user.password,  # No almacenamos el password aquí
            }

            user_entity = UserEntity(**user_entity_data)
            return user_entity

    def set_password(self, user: UserEntity, password: str) -> None:
        with transaction.atomic():
            django_user = User.objects.get(pk=user.id)
            django_user.set_password(password)
            django_user.save()
        return django_user

    def assign_groups(self, user: UserEntity, groups: list) -> None:
        with transaction.atomic():
            django_user = User.objects.get(pk=user.id)
            django_user.groups.set(groups)
            django_user.save()
