from rest_framework import serializers

from apps.common.utils import (
    nombre_item_catalogo,
    nombre_usuario,
    precio_desde_attrs_item,
    validar_un_solo_item,
)
from .models import EstadoPedido, ItemPedido, Pedido, TipoPedido


class ItemPedidoSerializer(serializers.ModelSerializer):
    subtotal = serializers.ReadOnlyField()
    nombre = serializers.SerializerMethodField()

    class Meta:
        model = ItemPedido
        fields = (
            "id",
            "producto",
            "variante",
            "combo",
            "nombre",
            "cantidad",
            "precio_unitario",
            "subtotal",
            "observaciones",
        )
        read_only_fields = ("precio_unitario", "subtotal")

    def get_nombre(self, obj):
        return nombre_item_catalogo(obj)


class ItemPedidoEscrituraSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemPedido
        fields = ("producto", "variante", "combo", "cantidad", "observaciones")

    def validate(self, attrs):
        validar_un_solo_item(attrs)
        return attrs


class PedidoPublicoSerializer(serializers.ModelSerializer):
    """Para el formulario de pedidos online. El cliente envía datos + ítems."""

    items = ItemPedidoEscrituraSerializer(many=True, write_only=True)

    class Meta:
        model = Pedido
        fields = (
            "id",
            "numero",
            "nombre_cliente",
            "telefono_cliente",
            "email_cliente",
            "tipo",
            "medio_pago",
            "direccion_entrega",
            "indicaciones_entrega",
            "observaciones",
            "items",
        )
        read_only_fields = ("id", "numero")

    def validate(self, attrs):
        if attrs.get("tipo") == TipoPedido.DELIVERY and not attrs.get(
            "direccion_entrega"
        ):
            raise serializers.ValidationError(
                {"direccion_entrega": "La dirección es obligatoria para delivery."}
            )
        if not attrs.get("items"):
            raise serializers.ValidationError(
                {"items": "El pedido debe tener al menos un ítem."}
            )
        return attrs

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        total = 0
        items_a_crear = []

        for item_data in items_data:
            precio = precio_desde_attrs_item(item_data)
            total += precio * item_data["cantidad"]
            items_a_crear.append((item_data, precio))

        pedido = Pedido.objects.create(**validated_data, total=total)
        for item_data, precio in items_a_crear:
            ItemPedido.objects.create(
                pedido=pedido, precio_unitario=precio, **item_data
            )
        return pedido


class PedidoSerializer(serializers.ModelSerializer):
    """Vista completa para el panel interno."""

    items = ItemPedidoSerializer(many=True, read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    medio_pago_display = serializers.CharField(
        source="get_medio_pago_display", read_only=True
    )
    repartidor_nombre = serializers.SerializerMethodField()
    atendido_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = (
            "id",
            "numero",
            "cliente",
            "nombre_cliente",
            "telefono_cliente",
            "email_cliente",
            "tipo",
            "tipo_display",
            "estado",
            "estado_display",
            "direccion_entrega",
            "indicaciones_entrega",
            "repartidor",
            "repartidor_nombre",
            "medio_pago",
            "medio_pago_display",
            "total",
            "pagado",
            "observaciones",
            "comanda_interna",
            "atendido_por",
            "atendido_por_nombre",
            "items",
            "creado_en",
            "actualizado_en",
        )
        read_only_fields = ("numero", "total", "creado_en", "actualizado_en")

    def get_repartidor_nombre(self, obj):
        return nombre_usuario(obj.repartidor)

    def get_atendido_por_nombre(self, obj):
        return nombre_usuario(obj.atendido_por)


class PedidoListSerializer(serializers.ModelSerializer):
    """Versión compacta para el listado operativo."""

    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = Pedido
        fields = (
            "id",
            "numero",
            "nombre_cliente",
            "telefono_cliente",
            "tipo",
            "tipo_display",
            "estado",
            "estado_display",
            "total",
            "pagado",
            "creado_en",
        )


class CambiarEstadoPedidoSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=EstadoPedido.choices)
    repartidor_id = serializers.IntegerField(required=False, allow_null=True)
