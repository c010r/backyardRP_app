"""
Módulo de comandas (órdenes de mesa).

Decisiones de diseño:
- Una Comanda agrupa los ítems pedidos por una mesa en un servicio.
- ItemComanda guarda precio_unitario al momento del pedido (snapshot):
  si el producto cambia de precio luego, la comanda queda con el precio original.
- El estado de cocina (EstadoCocina) vive en ItemComanda para que la cocina
  pueda marcar cada ítem individualmente (ej: una hamburguesa lista pero las
  papas todavía no).
- Una Comanda puede tener múltiples ítems enviados a cocina en distintos momentos
  (rondas). El campo 'enviado_cocina' en ItemComanda indica si ya fue enviado.
- La división de cuenta y el cobro se manejan en el módulo cajas.
  Comanda solo registra si fue 'cerrada' (cobrada) o no.
- Se permite transferir comanda a otra mesa (campo mesa es FK nullable temporal,
  se reasigna). Se registra en auditoría.
"""

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import ExpressionWrapper, F, Sum
from django.db.models import DecimalField as DjangoDecimalField

from apps.common.models import ModeloBase
from apps.mesas.models import Mesa


class EstadoComanda(models.TextChoices):
    ABIERTA = "abierta", "Abierta"
    ENVIADA = "enviada", "Enviada a cocina"
    LISTA = "lista", "Lista para cobrar"
    CERRADA = "cerrada", "Cerrada / Cobrada"
    CANCELADA = "cancelada", "Cancelada"


class EstadoCocina(models.TextChoices):
    PENDIENTE = "pendiente", "Pendiente"
    EN_PREPARACION = "en_preparacion", "En preparación"
    LISTO = "listo", "Listo"
    ENTREGADO = "entregado", "Entregado"


class Comanda(ModeloBase):
    numero = models.PositiveIntegerField(
        unique=True,
        verbose_name="Número de comanda",
        help_text="Se genera automáticamente al abrir.",
    )
    mesa = models.ForeignKey(
        Mesa,
        on_delete=models.PROTECT,
        related_name="comandas",
        verbose_name="Mesa",
        null=True,
        blank=True,
        help_text="Null si es para llevar o delivery.",
    )
    mozo = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="comandas_asignadas",
        verbose_name="Mozo",
        null=True,
        blank=True,
    )
    estado = models.CharField(
        max_length=12,
        choices=EstadoComanda.choices,
        default=EstadoComanda.ABIERTA,
        verbose_name="Estado",
    )
    cantidad_personas = models.PositiveSmallIntegerField(
        default=1, verbose_name="Cantidad de personas"
    )
    observaciones = models.TextField(blank=True, verbose_name="Observaciones generales")
    # Se llena cuando la comanda es cobrada (desde el módulo cajas)
    cerrada_en = models.DateTimeField(null=True, blank=True, verbose_name="Cerrada en")

    class Meta:
        verbose_name = "Comanda"
        verbose_name_plural = "Comandas"
        ordering = ["-creado_en"]

    def __str__(self):
        mesa_str = str(self.mesa) if self.mesa else "Sin mesa"
        return f"Comanda #{self.numero} — {mesa_str} [{self.get_estado_display()}]"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._siguiente_numero()
        super().save(*args, **kwargs)

    @staticmethod
    def _siguiente_numero():
        ultima = Comanda.objects.order_by("-numero").first()
        return (ultima.numero + 1) if ultima else 1

    @property
    def total(self):
        resultado = self.items.filter(cancelado=False).aggregate(
            total=Sum(
                ExpressionWrapper(
                    F("precio_unitario") * F("cantidad"),
                    output_field=DjangoDecimalField(max_digits=12, decimal_places=2),
                )
            )
        )
        return resultado["total"] or Decimal("0")


class ItemComanda(ModeloBase):
    comanda = models.ForeignKey(
        Comanda,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Comanda",
    )
    producto = models.ForeignKey(
        "catalogo.Producto",
        on_delete=models.PROTECT,
        related_name="items_comanda",
        verbose_name="Producto",
        null=True,
        blank=True,
    )
    variante = models.ForeignKey(
        "catalogo.VarianteProducto",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Variante",
    )
    combo = models.ForeignKey(
        "catalogo.Combo",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Combo",
    )
    cantidad = models.PositiveSmallIntegerField(default=1, verbose_name="Cantidad")
    # Precio al momento del pedido — no cambia si el catálogo se actualiza
    precio_unitario = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Precio unitario"
    )
    observaciones = models.CharField(
        max_length=200, blank=True, verbose_name="Observaciones del ítem"
    )
    estado_cocina = models.CharField(
        max_length=15,
        choices=EstadoCocina.choices,
        default=EstadoCocina.PENDIENTE,
        verbose_name="Estado en cocina",
    )
    enviado_cocina = models.BooleanField(
        default=False,
        verbose_name="Enviado a cocina",
        help_text="True desde el momento en que se envió a la pantalla de cocina.",
    )
    cancelado = models.BooleanField(default=False, verbose_name="Cancelado")
    cancelado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items_cancelados",
        verbose_name="Cancelado por",
    )

    class Meta:
        verbose_name = "Ítem de comanda"
        verbose_name_plural = "Ítems de comanda"
        ordering = ["creado_en"]

    def __str__(self):
        nombre = self.variante or self.combo or self.producto
        return f"{self.cantidad}x {nombre} — Comanda #{self.comanda.numero}"

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad
