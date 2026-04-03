import datetime

from django.db.models import F
from rest_framework import filters, generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auditoria.utils import registrar_accion
from apps.usuarios.permissions import EsAdminOSupervisor, EsEmpleado
from .models import (
    EstadoOrdenCompra,
    MateriaPrima,
    MovimientoStock,
    OrdenCompra,
    Proveedor,
    Receta,
    TipoMovimiento,
    UnidadMedida,
)
from .serializers import (
    AjusteStockSerializer,
    CambiarEstadoOrdenSerializer,
    ItemOrdenCompraSerializer,
    MateriaPrimaListSerializer,
    MateriaPrimaSerializer,
    MovimientoStockSerializer,
    OrdenCompraSerializer,
    ProveedorSerializer,
    RecetaSerializer,
    UnidadMedidaSerializer,
)


class ListaUnidadMedidaView(generics.ListCreateAPIView):
    """GET/POST /api/inventario/unidades/"""

    queryset = UnidadMedida.objects.all()
    serializer_class = UnidadMedidaSerializer
    permission_classes = [IsAuthenticated, EsAdminOSupervisor]


class ListaMateriaPrimaView(generics.ListCreateAPIView):
    """
    GET  /api/inventario/materias-primas/?bajo_stock=1
    POST /api/inventario/materias-primas/
    """

    permission_classes = [IsAuthenticated, EsEmpleado]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nombre"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return MateriaPrimaSerializer
        return MateriaPrimaListSerializer

    def get_queryset(self):
        qs = MateriaPrima.objects.select_related("unidad").filter(activo=True)
        if self.request.query_params.get("bajo_stock"):
            qs = qs.filter(stock_actual__lte=F("stock_minimo"))
        return qs


class DetalleMateriaPrimaView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH/DELETE /api/inventario/materias-primas/<id>/"""

    queryset = MateriaPrima.objects.select_related("unidad")
    serializer_class = MateriaPrimaSerializer
    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def perform_destroy(self, instance):
        instance.activo = False
        instance.save(update_fields=["activo"])


class AjusteStockView(APIView):
    """
    POST /api/inventario/ajuste/
    Ajuste manual de stock: ENTRADA (suma), SALIDA (resta), AJUSTE (valor absoluto).
    """

    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def post(self, request):
        serializer = AjusteStockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            mp = MateriaPrima.objects.select_related("unidad").get(
                pk=data["materia_prima_id"], activo=True
            )
        except MateriaPrima.DoesNotExist:
            return Response({"detalle": "Materia prima no encontrada."}, status=404)

        stock_anterior = mp.stock_actual
        tipo = data["tipo"]
        if tipo == TipoMovimiento.ENTRADA:
            mp.stock_actual += data["cantidad"]
        elif tipo == TipoMovimiento.SALIDA:
            mp.stock_actual -= data["cantidad"]
        else:  # AJUSTE: valor absoluto
            mp.stock_actual = data["cantidad"]
        mp.save(update_fields=["stock_actual"])

        MovimientoStock.objects.create(
            tipo=tipo,
            materia_prima=mp,
            cantidad=data["cantidad"],
            stock_anterior=stock_anterior,
            stock_nuevo=mp.stock_actual,
            motivo=data["motivo"],
            registrado_por=request.user,
        )
        registrar_accion(
            usuario=request.user,
            modulo="inventario",
            accion="editar",
            detalle=f"Ajuste {tipo} de {mp.nombre}: {data['cantidad']} {mp.unidad.simbolo}",
            request=request,
        )
        return Response(MateriaPrimaSerializer(mp).data)


class ListaMovimientoStockView(generics.ListAPIView):
    """GET /api/inventario/movimientos/?materia_prima=<id>"""

    serializer_class = MovimientoStockSerializer
    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def get_queryset(self):
        qs = MovimientoStock.objects.select_related("materia_prima", "registrado_por")
        mp_id = self.request.query_params.get("materia_prima")
        if mp_id:
            qs = qs.filter(materia_prima_id=mp_id)
        return qs


class ListaRecetaView(generics.ListCreateAPIView):
    """GET/POST /api/inventario/recetas/?producto=<id>"""

    serializer_class = RecetaSerializer
    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def get_queryset(self):
        qs = Receta.objects.select_related("materia_prima__unidad", "producto")
        producto_id = self.request.query_params.get("producto")
        if producto_id:
            qs = qs.filter(producto_id=producto_id)
        return qs


class DetalleRecetaView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/DELETE /api/inventario/recetas/<id>/"""

    queryset = Receta.objects.select_related("materia_prima__unidad", "producto")
    serializer_class = RecetaSerializer
    permission_classes = [IsAuthenticated, EsAdminOSupervisor]


class ListaProveedorView(generics.ListCreateAPIView):
    """GET/POST /api/inventario/proveedores/"""

    serializer_class = ProveedorSerializer
    permission_classes = [IsAuthenticated, EsAdminOSupervisor]
    filter_backends = [filters.SearchFilter]
    search_fields = ["nombre", "contacto", "email"]

    def get_queryset(self):
        return Proveedor.objects.filter(activo=True)


class DetalleProveedorView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/DELETE /api/inventario/proveedores/<id>/"""

    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def perform_destroy(self, instance):
        instance.activo = False
        instance.save(update_fields=["activo"])


class ListaOrdenCompraView(generics.ListCreateAPIView):
    """GET/POST /api/inventario/ordenes/"""

    serializer_class = OrdenCompraSerializer
    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def get_queryset(self):
        return OrdenCompra.objects.select_related(
            "proveedor", "registrado_por"
        ).prefetch_related("items__materia_prima")

    def perform_create(self, serializer):
        serializer.save(registrado_por=self.request.user)


class DetalleOrdenCompraView(generics.RetrieveAPIView):
    """GET /api/inventario/ordenes/<id>/"""

    queryset = OrdenCompra.objects.select_related(
        "proveedor", "registrado_por"
    ).prefetch_related("items__materia_prima")
    serializer_class = OrdenCompraSerializer
    permission_classes = [IsAuthenticated, EsAdminOSupervisor]


class CambiarEstadoOrdenView(APIView):
    """
    POST /api/inventario/ordenes/<id>/estado/
    Si pasa a RECIBIDA, el signal actualiza el stock automáticamente.
    """

    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def post(self, request, pk):
        try:
            orden = OrdenCompra.objects.get(pk=pk)
        except OrdenCompra.DoesNotExist:
            return Response({"detalle": "Orden no encontrada."}, status=404)

        serializer = CambiarEstadoOrdenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        orden.estado = data["estado"]
        if data["estado"] == EstadoOrdenCompra.RECIBIDA:
            orden.fecha_recepcion = data.get("fecha_recepcion") or datetime.date.today()
        orden.save()

        registrar_accion(
            usuario=request.user,
            modulo="inventario",
            accion="editar",
            detalle=f"Orden #{orden.id} → {orden.get_estado_display()}",
            request=request,
        )
        return Response(OrdenCompraSerializer(orden).data)


class AgregarItemOrdenView(APIView):
    """
    POST /api/inventario/ordenes/<id>/items/
    Agrega un ítem a una orden en estado BORRADOR.
    """

    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def post(self, request, pk):
        try:
            orden = OrdenCompra.objects.get(pk=pk, estado=EstadoOrdenCompra.BORRADOR)
        except OrdenCompra.DoesNotExist:
            return Response(
                {"detalle": "Orden no encontrada o no está en borrador."}, status=404
            )
        serializer = ItemOrdenCompraSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(orden=orden)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
