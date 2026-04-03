"""
Módulo de reservas.

Decisiones de diseño:
- Una Reserva puede venir del formulario web (cliente no logueado → nombre+teléfono)
  o del panel interno (mozo/cajero carga la reserva manualmente).
- La asociación a mesa es OPCIONAL: se sugiere al confirmar, pero no bloquea
  la creación. Esto refleja la operación real: a veces se confirma sin mesa asignada.
- La validación de disponibilidad horaria usa HorarioNegocio de configuracion.
- futura_comanda queda como FK null para vincular la reserva a la comanda cuando
  el cliente llega y se abre la mesa.
"""

from django.conf import settings
from django.db import models

from apps.common.models import ModeloBase
from apps.mesas.models import Mesa


class EstadoReserva(models.TextChoices):
    PENDIENTE = "pendiente", "Pendiente"
    CONFIRMADA = "confirmada", "Confirmada"
    CANCELADA = "cancelada", "Cancelada"
    COMPLETADA = "completada", "Completada"  # cliente llegó y se sentó
    NO_SHOW = "no_show", "No se presentó"


class OrigenReserva(models.TextChoices):
    WEB = "web", "Formulario web"
    TELEFONO = "telefono", "Teléfono"
    INTERNO = "interno", "Carga interna"
    WHATSAPP = "whatsapp", "WhatsApp"


class Reserva(ModeloBase):
    # Datos del solicitante (puede ser un cliente no registrado)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reservas",
        verbose_name="Usuario registrado",
        help_text="Solo si el cliente tiene cuenta en el sistema.",
    )
    nombre_contacto = models.CharField(
        max_length=120, verbose_name="Nombre de contacto"
    )
    telefono_contacto = models.CharField(
        max_length=30, verbose_name="Teléfono de contacto"
    )
    email_contacto = models.EmailField(blank=True, verbose_name="Email de contacto")

    # Datos de la reserva
    fecha = models.DateField(verbose_name="Fecha")
    hora = models.TimeField(verbose_name="Hora")
    cantidad_personas = models.PositiveSmallIntegerField(
        verbose_name="Cantidad de personas"
    )
    mesa = models.ForeignKey(
        Mesa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reservas",
        verbose_name="Mesa asignada",
    )
    estado = models.CharField(
        max_length=12,
        choices=EstadoReserva.choices,
        default=EstadoReserva.PENDIENTE,
        verbose_name="Estado",
    )
    origen = models.CharField(
        max_length=10,
        choices=OrigenReserva.choices,
        default=OrigenReserva.WEB,
        verbose_name="Origen",
    )
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    # Quién gestionó la reserva internamente
    gestionada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reservas_gestionadas",
        verbose_name="Gestionada por",
    )

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ["fecha", "hora"]

    def __str__(self):
        return (
            f"Reserva {self.nombre_contacto} — {self.fecha:%d/%m/%Y} {self.hora:%H:%M} "
            f"({self.cantidad_personas} pers.) [{self.get_estado_display()}]"
        )
