from rest_framework import serializers

from apps.pedidos.models import Pedido
from .models import Cliente


class ClienteListSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.ReadOnlyField()

    class Meta:
        model = Cliente
        fields = (
            "id",
            "nombre",
            "apellido",
            "nombre_completo",
            "telefono",
            "email",
            "activo",
        )


class ClienteSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.ReadOnlyField()
    total_pedidos = serializers.SerializerMethodField()

    class Meta:
        model = Cliente
        fields = (
            "id",
            "usuario",
            "nombre",
            "apellido",
            "nombre_completo",
            "telefono",
            "email",
            "documento",
            "direccion",
            "fecha_nacimiento",
            "activo",
            "notas",
            "total_pedidos",
            "creado_en",
            "actualizado_en",
        )
        read_only_fields = ("creado_en", "actualizado_en")

    def get_total_pedidos(self, obj):
        if obj.usuario_id:
            return Pedido.objects.filter(cliente=obj.usuario_id).count()
        return 0
