"""
Configuración de desarrollo — SQLite, debug activo, CORS abierto.
"""
from .base import *  # noqa
from decouple import config

DEBUG = True

ALLOWED_HOSTS = ["*"]

# SQLite para desarrollo — sin configuración extra
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db_desarrollo.sqlite3",
    }
}

# CORS abierto en desarrollo
CORS_ALLOW_ALL_ORIGINS = True

# Emails en consola durante desarrollo
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Logging básico en consola
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "consola": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["consola"],
        "level": "DEBUG",
    },
}
