import pymysql

# Hace que Celery se cargue cuando Django inicie
from .celery import app as celery_app

pymysql.install_as_MySQLdb()

__all__ = ("celery_app",)
