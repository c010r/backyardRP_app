"""
Módulo de facturación electrónica.

Arquitectura preparada para integración con DGI (Uruguay).
En v1 se registran los comprobantes de forma local.
La integración real con el webservice de DGI (e-Factura) se implementa en v2.

Tipos de comprobante CFE relevantes:
  101 → e-Ticket
  102 → Nota de Crédito de e-Ticket
  111 → e-Factura
  112 → Nota de Crédito de e-Factura
"""

from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.common.models import ModeloBase


class TipoComprobante(models.TextChoices):
    E_TICKET = "101", "e-Ticket"
    NC_E_TICKET = "102", "Nota de Crédito de e-Ticket"
    ND_E_TICKET = "103", "Nota de Débito de e-Ticket"
    E_FACTURA = "111", "e-Factura"
    NC_E_FACTURA = "112", "Nota de Crédito de e-Factura"
    ND_E_FACTURA = "113", "Nota de Débito de e-Factura"


class EstadoComprobante(models.TextChoices):
    PENDIENTE = "pendiente", "Pendiente de envío a DGI"
    EMITIDO = "emitido", "Emitido (CAE obtenido)"
    RECHAZADO = "rechazado", "Rechazado por DGI"
    ANULADO = "anulado", "Anulado"


class Comprobante(ModeloBase):
    """
    Comprobante fiscal electrónico.
    Se vincula a una Comanda o Pedido según corresponda.
    """

    tipo = models.CharField(
        max_length=5,
        choices=TipoComprobante.choices,
        verbose_name="Tipo de comprobante",
    )
    estado = models.CharField(
        max_length=10,
        choices=EstadoComprobante.choices,
        default=EstadoComprobante.PENDIENTE,
        verbose_name="Estado",
    )
    punto_venta = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Punto de venta",
    )
    numero = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Número de comprobante",
    )

    # Receptor (cliente)
    razon_social_receptor = models.CharField(
        max_length=200, blank=True, verbose_name="Razón social del receptor"
    )
    documento_receptor = models.CharField(
        max_length=20, blank=True, verbose_name="RUT / CI del receptor"
    )
    tipo_documento_receptor = models.CharField(
        max_length=50, blank=True, verbose_name="Tipo de Documento (RUT/CI/Pasaporte)"
    )

    # Totales
    subtotal = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Subtotal neto"
    )
    iva = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="IVA"
    )
    total = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Total"
    )

    # DGI
    cae = models.CharField(max_length=20, blank=True, verbose_name="CAE")
    cae_vencimiento = models.DateField(
        null=True, blank=True, verbose_name="Vencimiento del CAE"
    )
    respuesta_dgi = models.JSONField(
        null=True, blank=True, verbose_name="Respuesta completa DGI"
    )

    # Asociación (comanda o pedido — solo uno a la vez)
    comanda = models.OneToOneField(
        "comandas.Comanda",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="comprobante",
        verbose_name="Comanda",
    )
    pedido = models.OneToOneField(
        "pedidos.Pedido",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="comprobante",
        verbose_name="Pedido online",
    )

    emitido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="comprobantes_emitidos",
        verbose_name="Emitido por",
    )

    class Meta:
        verbose_name = "Comprobante"
        verbose_name_plural = "Comprobantes"
        ordering = ["-creado_en"]
        unique_together = ("tipo", "punto_venta", "numero")

    def __str__(self):
        numero_str = str(self.numero).zfill(8) if self.numero else "--------"
        return f"{self.get_tipo_display()} {self.punto_venta:04d}-{numero_str}"


class ItemComprobante(models.Model):
    """Línea de detalle del comprobante fiscal."""

    comprobante = models.ForeignKey(
        Comprobante,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Comprobante",
    )
    descripcion = models.CharField(max_length=200, verbose_name="Descripción")
    cantidad = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Cantidad"
    )
    precio_unitario = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Precio unitario neto"
    )
    alicuota_iva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=22,
        verbose_name="Alícuota IVA (%)",
    )

    class Meta:
        verbose_name = "Ítem de comprobante"
        verbose_name_plural = "Ítems de comprobante"

    @property
    def subtotal_neto(self):
        return self.precio_unitario * self.cantidad

    @property
    def iva_monto(self):
        return self.subtotal_neto * (self.alicuota_iva / Decimal("100"))

    @property
    def subtotal_total(self):
        return self.subtotal_neto + self.iva_monto
