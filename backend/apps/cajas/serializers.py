from rest_framework import serializers

from apps.common.utils import nombre_usuario
from .models import Caja, CierreCaja, MedioPago, MovimientoCaja, PagoComanda


class MovimientoCajaSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    medio_display = serializers.CharField(
        source="get_medio_pago_display", read_only=True
    )
    recibo_url = serializers.SerializerMethodField()

    class Meta:
        model = MovimientoCaja
        fields = (
            "id",
            "tipo",
            "tipo_display",
            "medio_pago",
            "medio_display",
            "monto",
            "descripcion",
            "recibo",
            "recibo_url",
            "registrado_por",
            "creado_en",
        )
        read_only_fields = ("registrado_por",)

    def get_recibo_url(self, obj):
        if not obj.recibo:
            return None

        request = self.context.get("request")
        if request is not None:
            return request.build_absolute_uri(obj.recibo.url)

        # Fallback en caso de que no haya request: apuntar al backend en localhost:8000
        return f"http://localhost:8000{obj.recibo.url}"


class CajaSerializer(serializers.ModelSerializer):
    cajero_nombre = serializers.SerializerMethodField()
    total_ingresos = serializers.ReadOnlyField()
    total_egresos = serializers.ReadOnlyField()
    saldo_esperado = serializers.ReadOnlyField()
    movimientos = MovimientoCajaSerializer(many=True, read_only=True)

    class Meta:
        model = Caja
        fields = (
            "id",
            "cajero",
            "cajero_nombre",
            "abierta",
            "monto_inicial",
            "monto_final_declarado",
            "total_ingresos",
            "total_egresos",
            "saldo_esperado",
            "movimientos",
            "observaciones_apertura",
            "cerrada_en",
            "creado_en",
        )
        read_only_fields = ("abierta", "cerrada_en")

    def get_cajero_nombre(self, obj):
        return nombre_usuario(obj.cajero)


class AperturaCajaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Caja
        fields = ("monto_inicial", "observaciones_apertura")


class PagoComandaSerializer(serializers.ModelSerializer):
    medio_display = serializers.CharField(
        source="get_medio_pago_display", read_only=True
    )

    class Meta:
        model = PagoComanda
        fields = (
            "id",
            "caja",
            "comanda",
            "medio_pago",
            "medio_display",
            "monto",
            "propina",
            "registrado_por",
            "creado_en",
        )
        read_only_fields = ("registrado_por", "caja")


class CobrarComandaSerializer(serializers.Serializer):
    """
    Payload para cobrar una comanda desde caja.
    Soporta múltiples medios de pago en una sola operación.
    """

    class PagoItem(serializers.Serializer):
        medio_pago = serializers.ChoiceField(choices=MedioPago.choices)
        monto = serializers.DecimalField(max_digits=12, decimal_places=2)
        propina = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)

    comanda_id = serializers.IntegerField()
    pagos = PagoItem(many=True)

    def validate_pagos(self, value):
        if not value:
            raise serializers.ValidationError("Debe incluir al menos un medio de pago.")
        return value


class CierreCajaSerializer(serializers.ModelSerializer):
    medio_display = serializers.CharField(
        source="get_medio_pago_display", read_only=True
    )

    class Meta:
        model = CierreCaja
        fields = ("medio_pago", "medio_display", "total_cobrado", "total_propinas")


class ArqueoCajaSerializer(serializers.Serializer):
    """Payload para cerrar caja con monto declarado."""

    monto_final_declarado = serializers.DecimalField(max_digits=12, decimal_places=2)
