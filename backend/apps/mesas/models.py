"""
Módulo de mesas y ubicaciones.

Decisiones de diseño:
- Ubicacion representa zonas físicas (salón principal, terraza, barra, VIP).
- Mesa guarda posición X/Y como enteros para el mapa drag & drop del frontend.
  El frontend es quien define la escala; el backend solo persiste los valores.
- EstadoMesa usa choices en lugar de FK para simplicidad y velocidad de lectura
  en el panel operativo. Los estados cambian frecuentemente durante el servicio.
- nunca se eliminan mesas: se desactivan con activo=False para preservar historial.
"""

from django.db import models

from apps.common.models import ModeloBase


class Ubicacion(ModeloBase):
    nombre = models.CharField(max_length=80, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    orden = models.PositiveSmallIntegerField(default=0, verbose_name="Orden")
    activo = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Ubicación"
        verbose_name_plural = "Ubicaciones"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class EstadoMesa(models.TextChoices):
    LIBRE = "libre", "Libre"
    OCUPADA = "ocupada", "Ocupada"
    RESERVADA = "reservada", "Reservada"
    CERRADA = "cerrada", "Cerrada"  # fuera de servicio temporal


class Mesa(ModeloBase):
    ubicacion = models.ForeignKey(
        Ubicacion,
        on_delete=models.PROTECT,
        related_name="mesas",
        verbose_name="Ubicación",
    )
    numero = models.PositiveSmallIntegerField(verbose_name="Número de mesa")
    nombre = models.CharField(
        max_length=40,
        blank=True,
        verbose_name="Nombre / alias",
        help_text="Ej: 'Terraza 1', 'Barra'. Opcional.",
    )
    capacidad = models.PositiveSmallIntegerField(
        default=4, verbose_name="Capacidad (personas)"
    )
    estado = models.CharField(
        max_length=10,
        choices=EstadoMesa.choices,
        default=EstadoMesa.LIBRE,
        verbose_name="Estado",
    )
    # Posición en el mapa visual del frontend (coordenadas en píxeles o unidades de grilla)
    pos_x = models.PositiveSmallIntegerField(default=0, verbose_name="Posición X")
    pos_y = models.PositiveSmallIntegerField(default=0, verbose_name="Posición Y")
    activo = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Mesa"
        verbose_name_plural = "Mesas"
        ordering = ["ubicacion", "numero"]
        unique_together = ("ubicacion", "numero")

    def __str__(self):
        alias = f" ({self.nombre})" if self.nombre else ""
        return f"Mesa {self.numero}{alias} — {self.ubicacion.nombre}"

    @property
    def etiqueta(self):
        return self.nombre if self.nombre else f"Mesa {self.numero}"
