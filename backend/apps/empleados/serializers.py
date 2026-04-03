from rest_framework import serializers

from apps.common.utils import nombre_usuario
from .models import Empleado


class EmpleadoListSerializer(serializers.ModelSerializer):
    nombre = serializers.SerializerMethodField()
    rol = serializers.CharField(source="usuario.rol", read_only=True)
    activo = serializers.BooleanField(source="usuario.activo", read_only=True)

    class Meta:
        model = Empleado
        fields = (
            "id",
            "usuario",
            "nombre",
            "rol",
            "activo",
            "tipo_contrato",
            "costo",
            "fecha_ingreso",
        )

    def get_nombre(self, obj):
        return nombre_usuario(obj.usuario)


class EmpleadoSerializer(serializers.ModelSerializer):
    nombre = serializers.SerializerMethodField()
    rol = serializers.CharField(source="usuario.rol", read_only=True)
    email = serializers.EmailField(source="usuario.email", read_only=True)
    activo = serializers.BooleanField(source="usuario.activo", read_only=True)
    tipo_contrato_display = serializers.CharField(
        source="get_tipo_contrato_display", read_only=True
    )

    class Meta:
        model = Empleado
        fields = (
            "id",
            "usuario",
            "nombre",
            "rol",
            "email",
            "activo",
            "documento",
            "direccion",
            "telefono_emergencia",
            "contacto_emergencia",
            "fecha_nacimiento",
            "fecha_ingreso",
            "tipo_contrato",
            "tipo_contrato_display",
            "costo",
            "notas",
            "creado_en",
            "actualizado_en",
        )
        read_only_fields = ("creado_en", "actualizado_en")

    def get_nombre(self, obj):
        return nombre_usuario(obj.usuario)
