"""
Modelos abstractos reutilizables por todas las apps.
"""

from django.db import models


class ModeloBase(models.Model):
    """
    Base con timestamps para todos los modelos del sistema.
    Heredar de este modelo en lugar de models.Model.
    """

    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")
    actualizado_en = models.DateTimeField(auto_now=True, verbose_name="Actualizado en")

    class Meta:
        abstract = True
