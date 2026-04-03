"""
Módulo de catálogo: categorías, productos, variantes, extras, combos
y registro histórico de precios.

Decisiones de diseño:
- Producto tiene tres flags de visibilidad independientes (menú QR, online, salón)
  porque un producto puede estar en el salón pero no en el menú público.
- HistorialPrecio se guarda automáticamente con una señal (ver signals.py).
- Variantes y Extras son muchos-a-muchos con Producto para máxima flexibilidad.
- Combos tienen su propia tabla de ítems para poder controlar cantidad y precio
  de cada componente dentro del combo.
"""

from django.conf import settings
from django.db import models

from apps.common.models import ModeloBase


class Categoria(ModeloBase):
    nombre = models.CharField(max_length=80, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    imagen = models.ImageField(
        upload_to="catalogo/categorias/", null=True, blank=True, verbose_name="Imagen"
    )
    orden = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Orden",
        help_text="Número menor aparece primero en el menú.",
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")
    visible_menu_qr = models.BooleanField(
        default=True, verbose_name="Visible en menú QR"
    )

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class Extra(ModeloBase):
    """
    Agregado opcional a un producto (ej: salsa extra, queso adicional).
    Se asocia a productos mediante ManyToMany en Producto.
    """

    nombre = models.CharField(max_length=80, verbose_name="Nombre")
    precio = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Precio adicional"
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Extra"
        verbose_name_plural = "Extras"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} (+${self.precio})"


class Producto(ModeloBase):
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="productos",
        verbose_name="Categoría",
    )
    nombre = models.CharField(max_length=120, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    imagen = models.ImageField(
        upload_to="catalogo/productos/", null=True, blank=True, verbose_name="Imagen"
    )
    precio_costo = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Precio de costo"
    )
    precio_venta = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Precio de venta"
    )
    disponible = models.BooleanField(
        default=True,
        verbose_name="Disponible",
        help_text="Fuera de disponibilidad temporaria (sin eliminar).",
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")

    # Visibilidad independiente por canal
    visible_salon = models.BooleanField(default=True, verbose_name="Visible en salón")
    visible_menu_qr = models.BooleanField(
        default=True, verbose_name="Visible en menú QR"
    )
    visible_online = models.BooleanField(
        default=False, verbose_name="Visible en pedidos online"
    )

    extras = models.ManyToManyField(
        Extra,
        blank=True,
        related_name="productos",
        verbose_name="Extras disponibles",
    )

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["categoria", "nombre"]

    def __str__(self):
        return f"{self.nombre} (${self.precio_venta})"


class VarianteProducto(ModeloBase):
    """
    Variante de un producto (ej: tamaño chico/grande, sin TACC).
    Modifica el precio base con un delta (puede ser negativo).
    """

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="variantes",
        verbose_name="Producto",
    )
    nombre = models.CharField(max_length=80, verbose_name="Nombre de la variante")
    delta_precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Diferencia de precio",
        help_text="Suma o resta al precio base del producto. Puede ser negativo.",
    )
    disponible = models.BooleanField(default=True, verbose_name="Disponible")

    class Meta:
        verbose_name = "Variante de producto"
        verbose_name_plural = "Variantes de producto"
        unique_together = ("producto", "nombre")

    def __str__(self):
        signo = "+" if self.delta_precio >= 0 else ""
        return f"{self.producto.nombre} — {self.nombre} ({signo}${self.delta_precio})"

    @property
    def precio_final(self):
        return self.producto.precio_venta + self.delta_precio


class Combo(ModeloBase):
    """
    Combo armado con múltiples productos. Tiene precio propio.
    """

    nombre = models.CharField(max_length=120, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    imagen = models.ImageField(
        upload_to="catalogo/combos/", null=True, blank=True, verbose_name="Imagen"
    )
    precio = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Precio del combo"
    )
    disponible = models.BooleanField(default=True, verbose_name="Disponible")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    visible_salon = models.BooleanField(default=True, verbose_name="Visible en salón")
    visible_online = models.BooleanField(
        default=False, verbose_name="Visible en pedidos online"
    )

    class Meta:
        verbose_name = "Combo"
        verbose_name_plural = "Combos"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} (${self.precio})"


class ItemCombo(models.Model):
    """Producto que forma parte de un combo con su cantidad."""

    combo = models.ForeignKey(Combo, on_delete=models.CASCADE, related_name="items")
    producto = models.ForeignKey(
        Producto, on_delete=models.PROTECT, related_name="en_combos"
    )
    cantidad = models.PositiveSmallIntegerField(default=1, verbose_name="Cantidad")

    class Meta:
        verbose_name = "Ítem de combo"
        verbose_name_plural = "Ítems de combo"
        unique_together = ("combo", "producto")

    def __str__(self):
        return f"{self.combo.nombre} → {self.cantidad}x {self.producto.nombre}"


class HistorialPrecio(models.Model):
    """
    Registro automático cada vez que cambia el precio de un producto.
    Se llena desde signals.py, no se escribe a mano.
    """

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="historial_precios",
        verbose_name="Producto",
    )
    precio_anterior = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Precio anterior"
    )
    precio_nuevo = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Precio nuevo"
    )
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Modificado por",
    )
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")

    class Meta:
        verbose_name = "Historial de precio"
        verbose_name_plural = "Historial de precios"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.producto.nombre}: ${self.precio_anterior} → ${self.precio_nuevo}"
