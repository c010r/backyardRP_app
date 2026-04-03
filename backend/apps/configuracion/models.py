"""
Configuración general del negocio.
Solo debe existir UNA instancia de Empresa (singleton).
"""

from django.db import models


class DiaSemana(models.TextChoices):
    LUNES = "lunes", "Lunes"
    MARTES = "martes", "Martes"
    MIERCOLES = "miercoles", "Miércoles"
    JUEVES = "jueves", "Jueves"
    VIERNES = "viernes", "Viernes"
    SABADO = "sabado", "Sábado"
    DOMINGO = "domingo", "Domingo"


class Empresa(models.Model):
    """
    Datos del negocio. Se crea una sola instancia mediante el panel admin
    o un comando de gestión. Los endpoints la leen/actualizan sin crear nuevas.
    """

    nombre = models.CharField(max_length=120, verbose_name="Nombre del negocio")
    razon_social = models.CharField(
        max_length=200, blank=True, verbose_name="Razón social"
    )
    rut = models.CharField(max_length=20, blank=True, verbose_name="RUT")
    telefono = models.CharField(max_length=30, blank=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, verbose_name="Email")
    direccion = models.CharField(max_length=255, blank=True, verbose_name="Dirección")
    ciudad = models.CharField(max_length=100, blank=True, verbose_name="Ciudad")
    logo = models.ImageField(
        upload_to="configuracion/logos/", null=True, blank=True, verbose_name="Logo"
    )
    moneda = models.CharField(max_length=10, default="UYU", verbose_name="Moneda")
    zona_horaria = models.CharField(
        max_length=60,
        default="America/Montevideo",
        verbose_name="Zona horaria",
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresa"

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        # Singleton: si ya existe una instancia, actualiza en lugar de crear
        if not self.pk and Empresa.objects.exists():
            raise ValueError("Solo puede existir una configuración de empresa.")
        super().save(*args, **kwargs)


class HorarioNegocio(models.Model):
    """
    Horarios de apertura por día de la semana.
    Se usan para validar reservas y pedidos online.
    """

    dia = models.CharField(
        max_length=10,
        choices=DiaSemana.choices,
        unique=True,
        verbose_name="Día",
    )
    apertura = models.TimeField(verbose_name="Hora de apertura")
    cierre = models.TimeField(verbose_name="Hora de cierre")
    cierre_siguiente_dia = models.BooleanField(
        default=False,
        verbose_name="Cierra al día siguiente",
        help_text="Marcar si el horario de cierre es pasada la medianoche.",
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Horario del negocio"
        verbose_name_plural = "Horarios del negocio"
        ordering = ["dia"]

    def __str__(self):
        return f"{self.get_dia_display()} {self.apertura:%H:%M} – {self.cierre:%H:%M}"
