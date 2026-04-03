"""
Señales del módulo de inventario.

1. ItemComanda → ENTREGADO: descuenta stock según receta del producto.
2. OrdenCompra → RECIBIDA: suma stock y actualiza costo para cada ítem.
"""

import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


# ─── ItemComanda: descuento automático al entregar ────────────────────────────


@receiver(pre_save, sender="comandas.ItemComanda")
def _capturar_estado_cocina_anterior(sender, instance, **kwargs):
    """Captura estado_cocina previo para detectar transición → ENTREGADO."""
    if instance.pk:
        try:
            instance._estado_cocina_anterior = sender.objects.values_list(
                "estado_cocina", flat=True
            ).get(pk=instance.pk)
        except sender.DoesNotExist:
            instance._estado_cocina_anterior = None
    else:
        instance._estado_cocina_anterior = None


@receiver(post_save, sender="comandas.ItemComanda")
def descontar_stock_por_entrega(sender, instance, created, **kwargs):
    """Descuenta stock automáticamente cuando un ítem pasa a ENTREGADO."""
    if created:
        return

    from apps.comandas.models import EstadoCocina

    estado_anterior = getattr(instance, "_estado_cocina_anterior", None)
    if (
        estado_anterior == EstadoCocina.ENTREGADO
        or instance.estado_cocina != EstadoCocina.ENTREGADO
    ):
        return

    # Determinar el producto (variante o producto directo; combos no descuentan por ahora)
    if instance.variante:
        producto = instance.variante.producto
    elif instance.producto:
        producto = instance.producto
    else:
        return

    from .models import MovimientoStock, Receta, TipoMovimiento

    recetas = Receta.objects.filter(producto=producto).select_related(
        "materia_prima__unidad"
    )
    for receta in recetas:
        mp = receta.materia_prima
        cantidad_a_descontar = receta.cantidad * instance.cantidad
        stock_anterior = mp.stock_actual
        mp.stock_actual -= cantidad_a_descontar
        mp.save(update_fields=["stock_actual"])
        try:
            comanda_num = instance.comanda.numero
        except AttributeError:
            comanda_num = "?"
        try:
            MovimientoStock.objects.create(
                tipo=TipoMovimiento.SALIDA,
                materia_prima=mp,
                cantidad=cantidad_a_descontar,
                stock_anterior=stock_anterior,
                stock_nuevo=mp.stock_actual,
                motivo=f"Venta automática — Comanda #{comanda_num}",
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error al registrar movimiento de stock: %s", exc)


# ─── OrdenCompra: entrada de stock al recibir ─────────────────────────────────


@receiver(pre_save, sender="inventario.OrdenCompra")
def _capturar_estado_orden_anterior(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._estado_anterior = sender.objects.values_list(
                "estado", flat=True
            ).get(pk=instance.pk)
        except sender.DoesNotExist:
            instance._estado_anterior = None
    else:
        instance._estado_anterior = None


@receiver(post_save, sender="inventario.OrdenCompra")
def actualizar_stock_al_recibir(sender, instance, created, **kwargs):
    """Cuando una orden pasa a RECIBIDA: suma stock y actualiza costo unitario."""
    if created:
        return

    from .models import EstadoOrdenCompra, MovimientoStock, TipoMovimiento

    estado_anterior = getattr(instance, "_estado_anterior", None)
    if (
        estado_anterior == EstadoOrdenCompra.RECIBIDA
        or instance.estado != EstadoOrdenCompra.RECIBIDA
    ):
        return

    for item in instance.items.select_related("materia_prima"):
        mp = item.materia_prima
        stock_anterior = mp.stock_actual
        mp.stock_actual += item.cantidad
        mp.costo_unitario = item.precio_unitario  # actualiza al precio más reciente
        mp.save(update_fields=["stock_actual", "costo_unitario"])
        try:
            MovimientoStock.objects.create(
                tipo=TipoMovimiento.ENTRADA,
                materia_prima=mp,
                cantidad=item.cantidad,
                stock_anterior=stock_anterior,
                stock_nuevo=mp.stock_actual,
                motivo=f"Compra OC #{instance.id} — {instance.proveedor.nombre}",
                registrado_por=instance.registrado_por,
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error al registrar entrada de stock: %s", exc)
