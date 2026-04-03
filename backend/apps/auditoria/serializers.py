from rest_framework import serializers

from apps.common.utils import nombre_usuario
from .models import RegistroAuditoria


class RegistroAuditoriaSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.SerializerMethodField()

    class Meta:
        model = RegistroAuditoria
        fields = (
            "id",
            "usuario",
            "usuario_nombre",
            "modulo",
            "accion",
            "detalle",
            "ip",
            "fecha",
        )

    def get_usuario_nombre(self, obj):
        return nombre_usuario(obj.usuario) or "sistema"
