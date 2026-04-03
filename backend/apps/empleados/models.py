"""
Módulo de empleados.

Extiende el Usuario con datos de RRHH: documento, dirección, costo laboral.
Decisión de diseño: perfil separado (OneToOne → Usuario) para no contaminar
el modelo de usuario con datos exclusivamente de recursos humanos.
"""

from django.conf import settings
from django.db import models

from apps.common.models import ModeloBase


class TipoContrato(models.TextChoices):
    POR_HORA = "hora", "Por hora"
    FIJO = "fijo", "Salario fijo"
    EVENTUAL = "eventual", "Eventual"


class Empleado(ModeloBase):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_empleado",
        verbose_name="Usuario del sistema",
    )
    documento = models.CharField(
        max_length=20, blank=True, verbose_name="DNI / Documento"
    )
    direccion = models.CharField(max_length=200, blank=True, verbose_name="Dirección")
    telefono_emergencia = models.CharField(
        max_length=30, blank=True, verbose_name="Teléfono de emergencia"
    )
    contacto_emergencia = models.CharField(
        max_length=100, blank=True, verbose_name="Contacto de emergencia"
    )
    fecha_nacimiento = models.DateField(
        null=True, blank=True, verbose_name="Fecha de nacimiento"
    )
    fecha_ingreso = models.DateField(
        null=True, blank=True, verbose_name="Fecha de ingreso"
    )
    tipo_contrato = models.CharField(
        max_length=10,
        choices=TipoContrato.choices,
        default=TipoContrato.POR_HORA,
        verbose_name="Tipo de contrato",
    )
    costo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Costo ($/hora o $/mes según tipo)",
    )
    notas = models.TextField(blank=True, verbose_name="Notas internas")

    class Meta:
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"
        ordering = ["usuario__last_name", "usuario__first_name"]

    def __str__(self):
        return f"{self.usuario.get_full_name() or self.usuario.username} [{self.get_tipo_contrato_display()}]"
