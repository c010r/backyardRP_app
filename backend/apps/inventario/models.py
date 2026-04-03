"""
Módulo de inventario.

Gestiona materias primas, recetas, proveedores y órdenes de compra.
El stock se descuenta automáticamente cuando se entrega un ítem de comanda
(ver signals.py). Las órdenes de compra actualizan el stock al ser recibidas.
"""

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import ExpressionWrapper, F, Sum
from django.db.models import DecimalField as DDF

from apps.common.models import ModeloBase


class UnidadMedida(models.Model):
    nombre = models.CharField(max_length=50, unique=True, verbose_name="Nombre")
    simbolo = models.CharField(max_length=10, verbose_name="Símbolo")

    class Meta:
        verbose_name = "Unidad de medida"
        verbose_name_plural = "Unidades de medida"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.simbolo})"


class MateriaPrima(ModeloBase):
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    unidad = models.ForeignKey(
        UnidadMedida,
        on_delete=models.PROTECT,
        related_name="materias_primas",
        verbose_name="Unidad de medida",
    )
    stock_actual = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
        verbose_name="Stock actual",
    )
    stock_minimo = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
        verbose_name="Stock mínimo",
    )
    costo_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Costo por unidad",
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Materia prima"
        verbose_name_plural = "Materias primas"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.stock_actual} {self.unidad.simbolo})"

    @property
    def bajo_stock(self):
        return self.stock_actual <= self.stock_minimo


class TipoMovimiento(models.TextChoices):
    ENTRADA = "entrada", "Entrada"
    SALIDA = "salida", "Salida"
    AJUSTE = "ajuste", "Ajuste (establece valor absoluto)"


class MovimientoStock(ModeloBase):
    tipo = models.CharField(
        max_length=10, choices=TipoMovimiento.choices, verbose_name="Tipo"
    )
    materia_prima = models.ForeignKey(
        MateriaPrima,
        on_delete=models.PROTECT,
        related_name="movimientos",
        verbose_name="Materia prima",
    )
    cantidad = models.DecimalField(
        max_digits=12, decimal_places=3, verbose_name="Cantidad"
    )
    stock_anterior = models.DecimalField(
        max_digits=12, decimal_places=3, verbose_name="Stock anterior"
    )
    stock_nuevo = models.DecimalField(
        max_digits=12, decimal_places=3, verbose_name="Stock nuevo"
    )
    motivo = models.CharField(max_length=200, blank=True, verbose_name="Motivo")
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos_stock",
        verbose_name="Registrado por",
    )

    class Meta:
        verbose_name = "Movimiento de stock"
        verbose_name_plural = "Movimientos de stock"
        ordering = ["-creado_en"]

    def __str__(self):
        return f"{self.get_tipo_display()} {self.materia_prima.nombre}: {self.cantidad}"


class Receta(models.Model):
    """Ingredientes necesarios para preparar una unidad de un producto."""

    producto = models.ForeignKey(
        "catalogo.Producto",
        on_delete=models.CASCADE,
        related_name="receta",
        verbose_name="Producto",
    )
    materia_prima = models.ForeignKey(
        MateriaPrima,
        on_delete=models.CASCADE,
        related_name="en_recetas",
        verbose_name="Materia prima",
    )
    cantidad = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        verbose_name="Cantidad por unidad",
    )

    class Meta:
        verbose_name = "Ingrediente de receta"
        verbose_name_plural = "Recetas"
        unique_together = ("producto", "materia_prima")
        ordering = ["producto__nombre", "materia_prima__nombre"]

    def __str__(self):
        return (
            f"{self.producto.nombre}: {self.cantidad} "
            f"{self.materia_prima.unidad.simbolo} de {self.materia_prima.nombre}"
        )


class Proveedor(ModeloBase):
    nombre = models.CharField(max_length=120, verbose_name="Nombre / Razón social")
    contacto = models.CharField(
        max_length=100, blank=True, verbose_name="Nombre del contacto"
    )
    telefono = models.CharField(max_length=30, blank=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, verbose_name="Email")
    direccion = models.CharField(max_length=200, blank=True, verbose_name="Dirección")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    notas = models.TextField(blank=True, verbose_name="Notas")

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class EstadoOrdenCompra(models.TextChoices):
    BORRADOR = "borrador", "Borrador"
    ENVIADA = "enviada", "Enviada al proveedor"
    RECIBIDA = "recibida", "Recibida"
    CANCELADA = "cancelada", "Cancelada"


class OrdenCompra(ModeloBase):
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        related_name="ordenes",
        verbose_name="Proveedor",
    )
    estado = models.CharField(
        max_length=10,
        choices=EstadoOrdenCompra.choices,
        default=EstadoOrdenCompra.BORRADOR,
        verbose_name="Estado",
    )
    fecha_emision = models.DateField(auto_now_add=True, verbose_name="Fecha de emisión")
    fecha_recepcion = models.DateField(
        null=True, blank=True, verbose_name="Fecha de recepción"
    )
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ordenes_compra",
        verbose_name="Registrado por",
    )

    class Meta:
        verbose_name = "Orden de compra"
        verbose_name_plural = "Órdenes de compra"
        ordering = ["-creado_en"]

    def __str__(self):
        return f"OC #{self.id} — {self.proveedor.nombre} [{self.get_estado_display()}]"

    @property
    def total(self):
        resultado = self.items.aggregate(
            total=Sum(
                ExpressionWrapper(
                    F("precio_unitario") * F("cantidad"),
                    output_field=DDF(max_digits=14, decimal_places=2),
                )
            )
        )
        return resultado["total"] or Decimal("0")


class ItemOrdenCompra(models.Model):
    orden = models.ForeignKey(
        OrdenCompra,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Orden de compra",
    )
    materia_prima = models.ForeignKey(
        MateriaPrima,
        on_delete=models.PROTECT,
        related_name="items_orden",
        verbose_name="Materia prima",
    )
    cantidad = models.DecimalField(
        max_digits=12, decimal_places=3, verbose_name="Cantidad"
    )
    precio_unitario = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Precio unitario"
    )

    class Meta:
        verbose_name = "Ítem de orden de compra"
        verbose_name_plural = "Ítems de orden de compra"

    def __str__(self):
        return f"{self.materia_prima.nombre} x{self.cantidad}"

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad
