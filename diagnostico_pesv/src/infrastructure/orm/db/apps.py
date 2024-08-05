from django.apps import AppConfig


class UserConfig(AppConfig):
    label = "auth"
    name = "src.infrastructure.orm.db.authorize"
    verbose_name = "Users"
