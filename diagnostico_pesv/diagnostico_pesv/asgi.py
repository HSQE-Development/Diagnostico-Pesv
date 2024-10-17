"""
ASGI config for diagnostico_pesv project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from . import routing

env = os.getenv("DEBUG", "False")
print(f"env: {env}")
env_debug = "development" if env == "True" else "production"
settings_module = f"diagnostico_pesv.settings.{env_debug}"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)
print(f"Usando configuración: {settings_module}")

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(URLRouter(routing.ws_urlpatterns)),
    }
)
