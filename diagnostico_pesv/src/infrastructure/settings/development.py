from src.infrastructure.settings.base import *


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
print(os.getenv("DB_NAME", "pesv"))
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("DB_NAME", "pesv"),  # Nombre de la base de datos
        "USER": os.getenv("DB_USER"),  # Usuario de MySQL
        "PASSWORD": os.getenv("DB_PASSWORD"),  # Contraseña de MySQL
        "HOST": os.getenv(
            "DB_HOST"
        ),  # Host donde se encuentra la base de datos (usualmente 'localhost')
        "PORT": os.getenv("DB_PORT"),  # Puerto de MySQL (por defecto es 3306)
        "OPTIONS": {"init_command": "SET sql_mode='STRICT_TRANS_TABLES'"},
    }
}
