from rest_framework import serializers

from apps.common.utils import nombre_usuario
from .models import Entrada, EstadoEntrada, Evento, TipoEntrada


class TipoEntradaSerializer(serializers.ModelSerializer):
    cupos_vendidos = serializers.ReadOnlyField()
    cupos_disponibles = serializers.ReadOnlyField()

    class Meta:
        model = TipoEntrada
        fields = (
            "id",
            "nombre",
            "descripcion",
            "precio",
            "cupos",
            "cupos_vendidos",
            "cupos_disponibles",
            "activo",
        )


class EventoListSerializer(serializers.ModelSerializer):
    cupos_vendidos = serializers.ReadOnlyField()
    cupos_disponibles = serializers.ReadOnlyField()

    class Meta:
        model = Evento
        fields = (
            "id",
            "nombre",
            "imagen",
            "fecha",
            "hora_inicio",
            "cupos_totales",
            "cupos_vendidos",
            "cupos_disponibles",
            "activo",
            "visible_publico",
        )


class EventoSerializer(serializers.ModelSerializer):
    tipos_entrada = TipoEntradaSerializer(many=True, read_only=True)
    cupos_vendidos = serializers.ReadOnlyField()
    cupos_disponibles = serializers.ReadOnlyField()

    class Meta:
        model = Evento
        fields = (
            "id",
            "nombre",
            "descripcion",
            "imagen",
            "fecha",
            "hora_inicio",
            "hora_fin",
            "cupos_totales",
            "cupos_vendidos",
            "cupos_disponibles",
            "activo",
            "visible_publico",
            "tipos_entrada",
            "creado_en",
        )
        read_only_fields = ("creado_en",)


class EntradaPublicaSerializer(serializers.ModelSerializer):
    """Para la compra pública de entradas (sin autenticación requerida)."""

    class Meta:
        model = Entrada
        fields = (
            "id",
            "tipo_entrada",
            "nombre_comprador",
            "email_comprador",
            "telefono_comprador",
            "medio_pago",
            "codigo_qr",
        )
        read_only_fields = ("id", "codigo_qr")

    def validate_tipo_entrada(self, value):
        if not value.activo:
            raise serializers.ValidationError(
                "Este tipo de entrada no está disponible."
            )
        if value.cupos_disponibles <= 0:
            raise serializers.ValidationError(
                "No hay cupos disponibles para este tipo de entrada."
            )
        return value

    def create(self, validated_data):
        validated_data["precio_pagado"] = validated_data["tipo_entrada"].precio
        return super().create(validated_data)


class EntradaSerializer(serializers.ModelSerializer):
    """Vista completa para el panel interno."""

    evento_nombre = serializers.CharField(
        source="tipo_entrada.evento.nombre", read_only=True
    )
    tipo_nombre = serializers.CharField(source="tipo_entrada.nombre", read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    validada_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Entrada
        fields = (
            "id",
            "tipo_entrada",
            "tipo_nombre",
            "evento_nombre",
            "cliente",
            "nombre_comprador",
            "email_comprador",
            "telefono_comprador",
            "estado",
            "estado_display",
            "medio_pago",
            "precio_pagado",
            "codigo_qr",
            "validada_por",
            "validada_por_nombre",
            "validada_en",
            "observaciones",
            "creado_en",
        )
        read_only_fields = (
            "codigo_qr",
            "validada_por",
            "validada_en",
            "precio_pagado",
            "creado_en",
        )

    def get_validada_por_nombre(self, obj):
        return nombre_usuario(obj.validada_por)


class ValidarEntradaSerializer(serializers.Serializer):
    codigo_qr = serializers.UUIDField()


class CambiarEstadoEntradaSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=EstadoEntrada.choices)
