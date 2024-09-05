from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

# Establece el módulo de configuración de Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "diagnostico_pesv.settings")

# Crea una instancia de Celery
app = Celery("diagnostico_pesv")

# Carga la configuración de Celery desde Django
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.beat_schedule = {}

# Descubre tareas en aplicaciones de Django
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
