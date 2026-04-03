"""
Módulo de clientes.

Un cliente puede estar vinculado a un usuario registrado (rol CLIENTE)
o ser simplemente un perfil de contacto creado internamente.
"""

from django.conf import settings
from django.db import models

from apps.common.models import ModeloBase


class Cliente(ModeloBase):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="perfil_cliente",
        verbose_name="Usuario del sistema",
    )
    nombre = models.CharField(max_length=80, verbose_name="Nombre")
    apellido = models.CharField(max_length=80, verbose_name="Apellido")
    telefono = models.CharField(max_length=30, blank=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, verbose_name="Email")
    documento = models.CharField(
        max_length=20, blank=True, verbose_name="DNI / Documento"
    )
    direccion = models.CharField(max_length=200, blank=True, verbose_name="Dirección")
    fecha_nacimiento = models.DateField(
        null=True, blank=True, verbose_name="Fecha de nacimiento"
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")
    notas = models.TextField(blank=True, verbose_name="Notas internas")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["apellido", "nombre"]

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}".strip()
