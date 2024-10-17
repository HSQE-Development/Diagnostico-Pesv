"""
WSGI config for diagnostico_pesv project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os
from dotenv import load_dotenv

load_dotenv()

from django.core.wsgi import get_wsgi_application

env = os.getenv("DEBUG", "False").lower() in ("true", "1")
env_debug = "development" if env == True else "production"
settings_module = f"diagnostico_pesv.settings.{env_debug}"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

application = get_wsgi_application()
