"""
Selecciona el entorno según la variable DJANGO_ENV del .env.
Por defecto usa desarrollo.
"""
from decouple import config

entorno = config("DJANGO_ENV", default="development")

if entorno == "production":
    from .production import *  # noqa
else:
    from .development import *  # noqa
