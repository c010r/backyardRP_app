"""
Módulo de pedidos online (take away y delivery propio).

Decisiones de diseño:
- Un Pedido es independiente de una Comanda de salón. Cuando llega al local
  o a la cocina, puede vincularse a una Comanda interna (campo comanda_interna).
- El carrito vive en ItemPedido con snapshot de precio, igual que comandas.
- DireccionEntrega se guarda embebida (no como modelo separado) porque el
  delivery es propio y la dirección del pedido es dato operativo, no maestro.
- El estado del repartidor es simple: asignado/en camino/entregado. Para v2
  se puede agregar tracking en tiempo real.
"""

from django.conf import settings
from django.db import models

from apps.common.models import ModeloBase


class TipoPedido(models.TextChoices):
    TAKE_AWAY = "take_away", "Take Away"
    DELIVERY = "delivery", "Delivery"


class EstadoPedido(models.TextChoices):
    RECIBIDO = "recibido", "Recibido"
    CONFIRMADO = "confirmado", "Confirmado"
    EN_PREPARACION = "en_preparacion", "En preparación"
    LISTO = "listo", "Listo para retirar / Salió a entregar"
    EN_CAMINO = "en_camino", "En camino"
    ENTREGADO = "entregado", "Entregado"
    CANCELADO = "cancelado", "Cancelado"


class MedioPagoPedido(models.TextChoices):
    EFECTIVO = "efectivo", "Efectivo al recibir"
    MERCADO_PAGO = "mercado_pago", "Mercado Pago"
    TRANSFERENCIA = "transferencia", "Transferencia"
    QR = "qr", "QR"


class Pedido(ModeloBase):
    numero = models.PositiveIntegerField(unique=True, verbose_name="Número de pedido")

    # Cliente puede ser registrado o no
    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pedidos",
        verbose_name="Cliente registrado",
    )
    nombre_cliente = models.CharField(max_length=120, verbose_name="Nombre del cliente")
    telefono_cliente = models.CharField(max_length=30, verbose_name="Teléfono")
    email_cliente = models.EmailField(blank=True, verbose_name="Email")

    tipo = models.CharField(
        max_length=10, choices=TipoPedido.choices, verbose_name="Tipo de pedido"
    )
    estado = models.CharField(
        max_length=15,
        choices=EstadoPedido.choices,
        default=EstadoPedido.RECIBIDO,
        verbose_name="Estado",
    )

    # Delivery
    direccion_entrega = models.CharField(
        max_length=255, blank=True, verbose_name="Dirección de entrega"
    )
    indicaciones_entrega = models.CharField(
        max_length=200, blank=True, verbose_name="Indicaciones de entrega"
    )
    repartidor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pedidos_asignados",
        verbose_name="Repartidor",
    )

    # Pago
    medio_pago = models.CharField(
        max_length=15,
        choices=MedioPagoPedido.choices,
        verbose_name="Medio de pago",
    )
    total = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="Total"
    )
    pagado = models.BooleanField(default=False, verbose_name="Pagado")

    observaciones = models.TextField(blank=True, verbose_name="Observaciones")

    # Vinculo opcional a comanda interna (cuando el pedido entra a cocina)
    comanda_interna = models.OneToOneField(
        "comandas.Comanda",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pedido_origen",
        verbose_name="Comanda interna",
    )
    atendido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pedidos_atendidos",
        verbose_name="Atendido por",
    )

    class Meta:
        verbose_name = "Pedido online"
        verbose_name_plural = "Pedidos online"
        ordering = ["-creado_en"]

    def __str__(self):
        return f"Pedido #{self.numero} — {self.nombre_cliente} [{self.get_estado_display()}]"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._siguiente_numero()
        super().save(*args, **kwargs)

    @staticmethod
    def _siguiente_numero():
        ultimo = Pedido.objects.order_by("-numero").first()
        return (ultimo.numero + 1) if ultimo else 1


class ItemPedido(ModeloBase):
    pedido = models.ForeignKey(
        Pedido, on_delete=models.CASCADE, related_name="items", verbose_name="Pedido"
    )
    producto = models.ForeignKey(
        "catalogo.Producto",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Producto",
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
    precio_unitario = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Precio unitario"
    )
    observaciones = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "Ítem de pedido"
        verbose_name_plural = "Ítems de pedido"

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad

    def __str__(self):
        nombre = self.variante or self.combo or self.producto
        return f"{self.cantidad}x {nombre} — Pedido #{self.pedido.numero}"
