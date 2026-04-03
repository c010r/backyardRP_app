"""
Señales del catálogo.
Registra automáticamente el historial de precios cuando un producto
es guardado con un precio_venta diferente al anterior.
"""

from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import HistorialPrecio, Producto


@receiver(pre_save, sender=Producto)
def registrar_cambio_precio(sender, instance, **kwargs):
    if not instance.pk:
        # Producto nuevo — no hay precio anterior
        return

    try:
        anterior = Producto.objects.get(pk=instance.pk)
    except Producto.DoesNotExist:
        return

    if anterior.precio_venta != instance.precio_venta:
        HistorialPrecio.objects.create(
            producto=instance,
            precio_anterior=anterior.precio_venta,
            precio_nuevo=instance.precio_venta,
            # El usuario que hizo el cambio se inyecta desde la vista si está disponible.
            # La señal no tiene acceso al request; las vistas que necesiten registrar quién
            # cambió el precio deben crear el HistorialPrecio directamente antes de guardar.
        )
