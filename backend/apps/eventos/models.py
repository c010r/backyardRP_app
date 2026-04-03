"""
Módulo de eventos y entradas.

Un Evento tiene TiposDeEntrada con cupos y precios.
Una Entrada es el ticket comprado, con código QR UUID único para control de acceso.
"""

import uuid

from django.conf import settings
from django.db import models

from apps.common.models import ModeloBase


class Evento(ModeloBase):
    nombre = models.CharField(max_length=150, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    imagen = models.ImageField(
        upload_to="eventos/", blank=True, null=True, verbose_name="Imagen"
    )
    fecha = models.DateField(verbose_name="Fecha")
    hora_inicio = models.TimeField(verbose_name="Hora de inicio")
    hora_fin = models.TimeField(null=True, blank=True, verbose_name="Hora de fin")
    cupos_totales = models.PositiveIntegerField(verbose_name="Cupos totales")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    visible_publico = models.BooleanField(default=True, verbose_name="Visible en web")

    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ["-fecha", "-hora_inicio"]

    def __str__(self):
        return f"{self.nombre} ({self.fecha})"

    @property
    def cupos_vendidos(self):
        return Entrada.objects.filter(
            tipo_entrada__evento=self,
            estado__in=[EstadoEntrada.PAGADA, EstadoEntrada.VALIDADA],
        ).count()

    @property
    def cupos_disponibles(self):
        return self.cupos_totales - self.cupos_vendidos


class TipoEntrada(models.Model):
    evento = models.ForeignKey(
        Evento,
        on_delete=models.CASCADE,
        related_name="tipos_entrada",
        verbose_name="Evento",
    )
    nombre = models.CharField(max_length=80, verbose_name="Nombre")
    descripcion = models.CharField(
        max_length=200, blank=True, verbose_name="Descripción"
    )
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio")
    cupos = models.PositiveIntegerField(verbose_name="Cupos")
    activo = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Tipo de entrada"
        verbose_name_plural = "Tipos de entrada"
        ordering = ["precio"]

    def __str__(self):
        return f"{self.nombre} — {self.evento.nombre}"

    @property
    def cupos_vendidos(self):
        return self.entradas.filter(
            estado__in=[EstadoEntrada.PAGADA, EstadoEntrada.VALIDADA]
        ).count()

    @property
    def cupos_disponibles(self):
        return self.cupos - self.cupos_vendidos


class EstadoEntrada(models.TextChoices):
    PENDIENTE = "pendiente", "Pendiente de pago"
    PAGADA = "pagada", "Pagada"
    VALIDADA = "validada", "Validada en acceso"
    CANCELADA = "cancelada", "Cancelada"


class MedioPagoEntrada(models.TextChoices):
    EFECTIVO = "efectivo", "Efectivo"
    MERCADO_PAGO = "mercado_pago", "Mercado Pago"
    TRANSFERENCIA = "transferencia", "Transferencia"


class Entrada(ModeloBase):
    tipo_entrada = models.ForeignKey(
        TipoEntrada,
        on_delete=models.PROTECT,
        related_name="entradas",
        verbose_name="Tipo de entrada",
    )
    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="entradas",
        verbose_name="Cliente registrado",
    )
    nombre_comprador = models.CharField(
        max_length=120, verbose_name="Nombre del comprador"
    )
    email_comprador = models.EmailField(verbose_name="Email del comprador")
    telefono_comprador = models.CharField(
        max_length=30, blank=True, verbose_name="Teléfono"
    )
    estado = models.CharField(
        max_length=10,
        choices=EstadoEntrada.choices,
        default=EstadoEntrada.PENDIENTE,
        verbose_name="Estado",
    )
    medio_pago = models.CharField(
        max_length=15,
        choices=MedioPagoEntrada.choices,
        blank=True,
        verbose_name="Medio de pago",
    )
    precio_pagado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Precio pagado",
    )
    codigo_qr = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name="Código QR",
    )
    validada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="entradas_validadas",
        verbose_name="Validada por",
    )
    validada_en = models.DateTimeField(
        null=True, blank=True, verbose_name="Validada en"
    )
    observaciones = models.CharField(
        max_length=200, blank=True, verbose_name="Observaciones"
    )

    class Meta:
        verbose_name = "Entrada"
        verbose_name_plural = "Entradas"
        ordering = ["-creado_en"]

    def __str__(self):
        return (
            f"Entrada {self.tipo_entrada.evento.nombre} "
            f"— {self.nombre_comprador} [{self.get_estado_display()}]"
        )
