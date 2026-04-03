from rest_framework import serializers

from apps.common.utils import (
    nombre_item_catalogo,
    nombre_usuario,
    precio_desde_attrs_item,
    validar_un_solo_item,
)
from .models import Comanda, ItemComanda


class ItemComandaSerializer(serializers.ModelSerializer):
    subtotal = serializers.ReadOnlyField()
    producto_nombre = serializers.SerializerMethodField()
    estado_cocina_display = serializers.CharField(
        source="get_estado_cocina_display", read_only=True
    )

    class Meta:
        model = ItemComanda
        fields = (
            "id",
            "producto",
            "producto_nombre",
            "variante",
            "combo",
            "cantidad",
            "precio_unitario",
            "subtotal",
            "observaciones",
            "estado_cocina",
            "estado_cocina_display",
            "enviado_cocina",
            "cancelado",
        )
        read_only_fields = ("precio_unitario", "subtotal", "enviado_cocina")

    def get_producto_nombre(self, obj):
        return nombre_item_catalogo(obj)


class ItemComandaEscrituraSerializer(serializers.ModelSerializer):
    """
    Para agregar ítems a una comanda.
    El precio se toma automáticamente del catálogo — no se envía desde el cliente.
    """

    class Meta:
        model = ItemComanda
        fields = ("id", "producto", "variante", "combo", "cantidad", "observaciones")

    def validate(self, attrs):
        validar_un_solo_item(attrs)
        variante = attrs.get("variante")
        producto = attrs.get("producto")
        if variante and producto and variante.producto != producto:
            raise serializers.ValidationError(
                "La variante no pertenece al producto indicado."
            )
        return attrs

    def create(self, validated_data):
        validated_data["precio_unitario"] = precio_desde_attrs_item(validated_data)
        return super().create(validated_data)


class ComandaSerializer(serializers.ModelSerializer):
    items = ItemComandaSerializer(many=True, read_only=True)
    total = serializers.ReadOnlyField()
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    mozo_nombre = serializers.SerializerMethodField()
    mesa_etiqueta = serializers.SerializerMethodField()

    class Meta:
        model = Comanda
        fields = (
            "id",
            "numero",
            "mesa",
            "mesa_etiqueta",
            "mozo",
            "mozo_nombre",
            "estado",
            "estado_display",
            "cantidad_personas",
            "observaciones",
            "total",
            "items",
            "cerrada_en",
            "creado_en",
            "actualizado_en",
        )
        read_only_fields = ("numero", "cerrada_en")

    def get_mozo_nombre(self, obj):
        return nombre_usuario(obj.mozo)

    def get_mesa_etiqueta(self, obj):
        return obj.mesa.etiqueta if obj.mesa else "Sin mesa"


class ComandaListSerializer(serializers.ModelSerializer):
    """Versión compacta para el panel operativo."""

    total = serializers.ReadOnlyField()
    mesa_etiqueta = serializers.SerializerMethodField()
    mozo_nombre = serializers.SerializerMethodField()
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Comanda
        fields = (
            "id",
            "numero",
            "mesa",
            "mesa_etiqueta",
            "mozo",
            "mozo_nombre",
            "estado",
            "estado_display",
            "total",
            "items_count",
            "creado_en",
        )

    def get_mesa_etiqueta(self, obj):
        return obj.mesa.etiqueta if obj.mesa else "Sin mesa"

    def get_mozo_nombre(self, obj):
        return nombre_usuario(obj.mozo)

    def get_items_count(self, obj):
        return sum(1 for item in obj.items.all() if not item.cancelado)


class TransferirMesaSerializer(serializers.Serializer):
    mesa_destino_id = serializers.IntegerField()

    def validate_mesa_destino_id(self, value):
        from apps.mesas.models import Mesa

        try:
            Mesa.objects.get(pk=value, activo=True)
        except Mesa.DoesNotExist:
            raise serializers.ValidationError("Mesa destino no encontrada o inactiva.")
        return value
