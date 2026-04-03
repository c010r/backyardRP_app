from rest_framework import serializers
from .models import Empresa, HorarioNegocio


class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = "__all__"


class HorarioNegocioSerializer(serializers.ModelSerializer):
    dia_display = serializers.CharField(source="get_dia_display", read_only=True)

    class Meta:
        model = HorarioNegocio
        fields = (
            "id",
            "dia",
            "dia_display",
            "apertura",
            "cierre",
            "cierre_siguiente_dia",
            "activo",
        )
