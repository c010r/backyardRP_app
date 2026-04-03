from rest_framework import serializers

from apps.common.utils import nombre_usuario
from .models import (
    Categoria,
    Combo,
    Extra,
    HistorialPrecio,
    ItemCombo,
    Producto,
    VarianteProducto,
)


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = (
            "id",
            "nombre",
            "descripcion",
            "imagen",
            "orden",
            "activo",
            "visible_menu_qr",
            "creado_en",
        )


class ExtraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Extra
        fields = ("id", "nombre", "precio", "activo")


class VarianteSerializer(serializers.ModelSerializer):
    precio_final = serializers.ReadOnlyField()

    class Meta:
        model = VarianteProducto
        fields = ("id", "nombre", "delta_precio", "precio_final", "disponible")


class ProductoListSerializer(serializers.ModelSerializer):
    """Versión compacta para listados."""

    categoria_nombre = serializers.CharField(source="categoria.nombre", read_only=True)

    class Meta:
        model = Producto
        fields = (
            "id",
            "nombre",
            "categoria",
            "categoria_nombre",
            "precio_venta",
            "disponible",
            "activo",
            "visible_salon",
            "visible_menu_qr",
            "visible_online",
            "imagen",
        )


class ProductoDetalleSerializer(serializers.ModelSerializer):
    """Versión completa con variantes y extras anidados."""

    variantes = VarianteSerializer(many=True, read_only=True)
    extras = ExtraSerializer(many=True, read_only=True)
    categoria_nombre = serializers.CharField(source="categoria.nombre", read_only=True)

    class Meta:
        model = Producto
        fields = (
            "id",
            "nombre",
            "descripcion",
            "imagen",
            "categoria",
            "categoria_nombre",
            "precio_costo",
            "precio_venta",
            "disponible",
            "activo",
            "visible_salon",
            "visible_menu_qr",
            "visible_online",
            "variantes",
            "extras",
            "creado_en",
            "actualizado_en",
        )


class ProductoEscrituraSerializer(serializers.ModelSerializer):
    """Para crear/editar productos. Extras se pasan como lista de IDs."""

    extras = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Extra.objects.all(), required=False
    )

    class Meta:
        model = Producto
        fields = (
            "id",
            "nombre",
            "descripcion",
            "imagen",
            "categoria",
            "precio_costo",
            "precio_venta",
            "disponible",
            "activo",
            "visible_salon",
            "visible_menu_qr",
            "visible_online",
            "extras",
        )


class ItemComboSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.nombre", read_only=True)

    class Meta:
        model = ItemCombo
        fields = ("id", "producto", "producto_nombre", "cantidad")


class ComboSerializer(serializers.ModelSerializer):
    items = ItemComboSerializer(many=True, read_only=True)

    class Meta:
        model = Combo
        fields = (
            "id",
            "nombre",
            "descripcion",
            "imagen",
            "precio",
            "disponible",
            "activo",
            "visible_salon",
            "visible_online",
            "items",
            "creado_en",
        )


class HistorialPrecioSerializer(serializers.ModelSerializer):
    modificado_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = HistorialPrecio
        fields = (
            "id",
            "producto",
            "precio_anterior",
            "precio_nuevo",
            "modificado_por",
            "modificado_por_nombre",
            "fecha",
        )

    def get_modificado_por_nombre(self, obj):
        return nombre_usuario(obj.modificado_por) or "sistema"
