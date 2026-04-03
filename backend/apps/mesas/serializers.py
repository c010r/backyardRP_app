from rest_framework import serializers

from .models import Mesa, Ubicacion
from apps.comandas.models import Comanda, EstadoComanda


class UbicacionSerializer(serializers.ModelSerializer):
    total_mesas = serializers.SerializerMethodField()

    class Meta:
        model = Ubicacion
        fields = ("id", "nombre", "descripcion", "orden", "activo", "total_mesas")

    def get_total_mesas(self, obj):
        return obj.mesas.filter(activo=True).count()


class MesaSerializer(serializers.ModelSerializer):
    ubicacion_nombre = serializers.CharField(source="ubicacion.nombre", read_only=True)
    etiqueta = serializers.ReadOnlyField()
    comanda_actual = serializers.SerializerMethodField()

    class Meta:
        model = Mesa
        fields = (
            "id",
            "numero",
            "nombre",
            "etiqueta",
            "ubicacion",
            "ubicacion_nombre",
            "capacidad",
            "estado",
            "comanda_actual",
            "pos_x",
            "pos_y",
            "activo",
            "creado_en",
        )

    def get_comanda_actual(self, obj):
        """Retorna la comanda abierta actual de la mesa."""
        comanda = obj.comandas.filter(
            estado__in=[EstadoComanda.ABIERTA, EstadoComanda.ENVIADA, EstadoComanda.LISTA]
        ).first()
        if comanda:
            return {"id": comanda.id, "numero": comanda.numero}
        return None


class MesaPosicionSerializer(serializers.ModelSerializer):
    """Serializer mínimo para actualizar posición (drag & drop)."""

    class Meta:
        model = Mesa
        fields = ("id", "pos_x", "pos_y")


class MesaEstadoSerializer(serializers.ModelSerializer):
    """Serializer mínimo para cambiar solo el estado de una mesa."""

    class Meta:
        model = Mesa
        fields = ("id", "estado")
