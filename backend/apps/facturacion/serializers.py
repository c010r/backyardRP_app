from rest_framework import serializers

from apps.common.utils import nombre_usuario
from .models import Comprobante, EstadoComprobante, ItemComprobante, TipoComprobante


class ItemComprobanteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemComprobante
        fields = (
            "id",
            "descripcion",
            "cantidad",
            "precio_unitario",
            "alicuota_iva",
        )


class ComprobanteSerializer(serializers.ModelSerializer):
    items = ItemComprobanteSerializer(many=True, read_only=True)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    emitido_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Comprobante
        fields = (
            "id",
            "tipo",
            "tipo_display",
            "estado",
            "estado_display",
            "punto_venta",
            "numero",
            "razon_social_receptor",
            "documento_receptor",
            "tipo_documento_receptor",
            "subtotal",
            "iva",
            "total",
            "cae",
            "cae_vencimiento",
            "comanda",
            "pedido",
            "emitido_por",
            "emitido_por_nombre",
            "items",
            "creado_en",
        )
        read_only_fields = (
            "cae",
            "cae_vencimiento",
            "respuesta_dgi",
            "emitido_por",
            "creado_en",
        )

    def get_emitido_por_nombre(self, obj):
        return nombre_usuario(obj.emitido_por)


class EmitirComprobanteSerializer(serializers.Serializer):
    """
    Payload para emitir un comprobante a partir de una comanda o pedido.
    La integración real con DGI se implementa en v2.
    """

    tipo = serializers.ChoiceField(choices=TipoComprobante.choices)
    comanda_id = serializers.IntegerField(required=False, allow_null=True)
    pedido_id = serializers.IntegerField(required=False, allow_null=True)
    razon_social_receptor = serializers.CharField(
        max_length=200, default="Consumidor Final"
    )
    documento_receptor = serializers.CharField(
        max_length=20, default="", allow_blank=True
    )
    tipo_documento_receptor = serializers.CharField(
        max_length=50, default="Consumidor Final", allow_blank=True
    )

    def validate(self, attrs):
        if not attrs.get("comanda_id") and not attrs.get("pedido_id"):
            raise serializers.ValidationError(
                "Debe indicar una comanda_id o pedido_id."
            )
        if attrs.get("comanda_id") and attrs.get("pedido_id"):
            raise serializers.ValidationError(
                "Indique solo comanda_id o pedido_id, no ambos."
            )
        return attrs
