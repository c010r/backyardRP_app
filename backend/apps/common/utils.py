"""
Utilidades compartidas por todas las apps del sistema.
"""


def nombre_usuario(usuario) -> str:
    """Devuelve el nombre completo del usuario o su username como fallback."""
    if usuario is None:
        return ""
    return usuario.get_full_name() or usuario.username


def nombre_item_catalogo(item) -> str:
    """
    Devuelve el nombre legible de un ítem que puede ser Producto, Variante o Combo.
    Usado por ItemComandaSerializer, ItemPedidoSerializer e ItemCocinaSerializer.
    """
    if getattr(item, "variante", None):
        return f"{item.variante.producto.nombre} — {item.variante.nombre}"
    if getattr(item, "combo", None):
        return item.combo.nombre
    if getattr(item, "producto", None):
        return item.producto.nombre
    return ""


def precio_desde_attrs_item(attrs: dict):
    """
    Extrae el precio unitario de un dict de atributos de ítem de catálogo.
    Usado al crear ItemComanda e ItemPedido.
    """
    if attrs.get("variante"):
        return attrs["variante"].precio_final
    if attrs.get("combo"):
        return attrs["combo"].precio
    return attrs["producto"].precio_venta


def validar_un_solo_item(attrs: dict):
    """
    Valida que exactamente uno de (producto, variante, combo) esté presente.
    Lanza ValidationError si no se cumple.
    """
    from rest_framework import serializers as drf_serializers

    opciones = [
        x
        for x in [attrs.get("producto"), attrs.get("variante"), attrs.get("combo")]
        if x
    ]
    if len(opciones) != 1:
        raise drf_serializers.ValidationError(
            "Debe especificar exactamente uno: producto, variante o combo."
        )
