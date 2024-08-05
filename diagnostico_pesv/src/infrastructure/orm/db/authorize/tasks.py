import json

from celery import shared_task

from src.infrastructure.orm.db.authorize.models import User


def get_user(id: int) -> User:
    attrs = {"id": id}
    currency = User.objects.get(**attrs)
    return currency


def save_user(user_json: str):
    user = json.loads(user_json)
    return User.objects.create(
        first_name=user.get("first_name"),
        last_name=user.get("last_name"),
        username=user.get("username"),
        email=user.get("email"),
        # password=user.get("password"),
        licensia_sst=user.get("licensia_sst"),
        cedula=user.get("cedula"),
    )
