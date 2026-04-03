"""
Cocina no tiene modelos propios: trabaja sobre ItemComanda y Comanda
del módulo comandas. Solo serializers y vistas especializadas.
"""

from django.utils import timezone
from rest_framework import serializers

from apps.comandas.models import Comanda, EstadoCocina, ItemComanda
from apps.common.utils import nombre_item_catalogo, nombre_usuario


class ItemCocinaSerializer(serializers.ModelSerializer):
    """Ítem individual para el panel de cocina."""

    nombre = serializers.SerializerMethodField()
    estado_cocina_display = serializers.CharField(
        source="get_estado_cocina_display", read_only=True
    )

    class Meta:
        model = ItemComanda
        fields = (
            "id",
            "nombre",
            "cantidad",
            "observaciones",
            "estado_cocina",
            "estado_cocina_display",
            "creado_en",
        )

    def get_nombre(self, obj):
        return nombre_item_catalogo(obj)


class ComandaCocinaSerializer(serializers.ModelSerializer):
    """
    Vista de comanda para la pantalla de cocina.
    Solo muestra los ítems enviados y no cancelados.
    """

    mesa_etiqueta = serializers.SerializerMethodField()
    mozo_nombre = serializers.SerializerMethodField()
    items_cocina = serializers.SerializerMethodField()
    minutos_espera = serializers.SerializerMethodField()

    class Meta:
        model = Comanda
        fields = (
            "id",
            "numero",
            "mesa_etiqueta",
            "mozo_nombre",
            "estado",
            "observaciones",
            "items_cocina",
            "minutos_espera",
            "creado_en",
        )

    def get_mesa_etiqueta(self, obj):
        return obj.mesa.etiqueta if obj.mesa else "Sin mesa"

    def get_mozo_nombre(self, obj):
        return nombre_usuario(obj.mozo)

    def get_items_cocina(self, obj):
        items = [
            item
            for item in obj.items.all()
            if item.enviado_cocina
            and not item.cancelado
            and item.estado_cocina != EstadoCocina.ENTREGADO
        ]
        return ItemCocinaSerializer(items, many=True).data

    def get_minutos_espera(self, obj):
        delta = timezone.now() - obj.creado_en
        return int(delta.total_seconds() / 60)
