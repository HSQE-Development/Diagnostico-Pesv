#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

ENV_FILE = Path(__file__).resolve().parent.parent / ".env.development"
load_dotenv(ENV_FILE)


def main():
    """Run administrative tasks."""
    env = os.getenv("DEBUG", "False").lower() in ("true", "1")
    env_debug = "development" if env == True else "production"
    settings_module = f"diagnostico_pesv.settings.{env_debug}"
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

    print(f"Usando configuración: {settings_module}")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
