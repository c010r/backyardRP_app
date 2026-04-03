from rest_framework import serializers

from apps.common.utils import nombre_usuario
from .models import (
    EstadoOrdenCompra,
    ItemOrdenCompra,
    MateriaPrima,
    MovimientoStock,
    OrdenCompra,
    Proveedor,
    Receta,
    TipoMovimiento,
    UnidadMedida,
)


class UnidadMedidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnidadMedida
        fields = ("id", "nombre", "simbolo")


class MateriaPrimaListSerializer(serializers.ModelSerializer):
    unidad_simbolo = serializers.CharField(source="unidad.simbolo", read_only=True)
    bajo_stock = serializers.ReadOnlyField()

    class Meta:
        model = MateriaPrima
        fields = (
            "id",
            "nombre",
            "unidad",
            "unidad_simbolo",
            "stock_actual",
            "stock_minimo",
            "bajo_stock",
            "costo_unitario",
            "activo",
        )


class MateriaPrimaSerializer(serializers.ModelSerializer):
    unidad_nombre = serializers.CharField(source="unidad.nombre", read_only=True)
    bajo_stock = serializers.ReadOnlyField()

    class Meta:
        model = MateriaPrima
        fields = (
            "id",
            "nombre",
            "descripcion",
            "unidad",
            "unidad_nombre",
            "stock_actual",
            "stock_minimo",
            "bajo_stock",
            "costo_unitario",
            "activo",
            "creado_en",
            "actualizado_en",
        )
        read_only_fields = ("creado_en", "actualizado_en")


class MovimientoStockSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    materia_prima_nombre = serializers.CharField(
        source="materia_prima.nombre", read_only=True
    )
    registrado_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = MovimientoStock
        fields = (
            "id",
            "tipo",
            "tipo_display",
            "materia_prima",
            "materia_prima_nombre",
            "cantidad",
            "stock_anterior",
            "stock_nuevo",
            "motivo",
            "registrado_por",
            "registrado_por_nombre",
            "creado_en",
        )
        read_only_fields = (
            "stock_anterior",
            "stock_nuevo",
            "registrado_por",
            "creado_en",
        )

    def get_registrado_por_nombre(self, obj):
        return nombre_usuario(obj.registrado_por)


class AjusteStockSerializer(serializers.Serializer):
    """
    Payload para ajuste manual de stock.
    - ENTRADA: suma cantidad al stock actual.
    - SALIDA: resta cantidad al stock actual.
    - AJUSTE: establece el stock actual al valor indicado.
    """

    materia_prima_id = serializers.IntegerField()
    cantidad = serializers.DecimalField(max_digits=12, decimal_places=3)
    tipo = serializers.ChoiceField(choices=TipoMovimiento.choices)
    motivo = serializers.CharField(max_length=200)


class RecetaSerializer(serializers.ModelSerializer):
    materia_prima_nombre = serializers.CharField(
        source="materia_prima.nombre", read_only=True
    )
    unidad_simbolo = serializers.CharField(
        source="materia_prima.unidad.simbolo", read_only=True
    )

    class Meta:
        model = Receta
        fields = (
            "id",
            "producto",
            "materia_prima",
            "materia_prima_nombre",
            "unidad_simbolo",
            "cantidad",
        )


class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = (
            "id",
            "nombre",
            "contacto",
            "telefono",
            "email",
            "direccion",
            "activo",
            "notas",
            "creado_en",
        )
        read_only_fields = ("creado_en",)


class ItemOrdenCompraSerializer(serializers.ModelSerializer):
    materia_prima_nombre = serializers.CharField(
        source="materia_prima.nombre", read_only=True
    )
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = ItemOrdenCompra
        fields = (
            "id",
            "materia_prima",
            "materia_prima_nombre",
            "cantidad",
            "precio_unitario",
            "subtotal",
        )


class OrdenCompraSerializer(serializers.ModelSerializer):
    items = ItemOrdenCompraSerializer(many=True, read_only=True)
    total = serializers.ReadOnlyField()
    proveedor_nombre = serializers.CharField(source="proveedor.nombre", read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    registrado_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = OrdenCompra
        fields = (
            "id",
            "proveedor",
            "proveedor_nombre",
            "estado",
            "estado_display",
            "fecha_emision",
            "fecha_recepcion",
            "observaciones",
            "total",
            "registrado_por",
            "registrado_por_nombre",
            "items",
            "creado_en",
        )
        read_only_fields = ("fecha_emision", "registrado_por", "creado_en")

    def get_registrado_por_nombre(self, obj):
        return nombre_usuario(obj.registrado_por)


class CambiarEstadoOrdenSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=EstadoOrdenCompra.choices)
    fecha_recepcion = serializers.DateField(required=False, allow_null=True)
