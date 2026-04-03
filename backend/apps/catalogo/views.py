from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auditoria.utils import registrar_accion
from apps.usuarios.permissions import EsAdminOSupervisor, EsEmpleado
from .models import (
    Categoria,
    Combo,
    Extra,
    HistorialPrecio,
    ItemCombo,
    Producto,
    VarianteProducto,
)
from .serializers import (
    CategoriaSerializer,
    ComboSerializer,
    ExtraSerializer,
    HistorialPrecioSerializer,
    ItemComboSerializer,
    ProductoDetalleSerializer,
    ProductoEscrituraSerializer,
    ProductoListSerializer,
    VarianteSerializer,
)

# ── Categorías ────────────────────────────────────────────────────────────────


class ListaCategoriaView(generics.ListCreateAPIView):
    """
    GET  /api/catalogo/categorias/         → cualquier empleado
    POST /api/catalogo/categorias/         → admin/supervisor
    """

    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), EsAdminOSupervisor()]


class DetalleCategoriaView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def destroy(self, request, *args, **kwargs):
        categoria = self.get_object()
        if categoria.productos.filter(activo=True).exists():
            return Response(
                {
                    "detalle": "No se puede eliminar una categoría con productos activos."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        categoria.activo = False
        categoria.save()
        return Response({"detalle": "Categoría desactivada."})


# ── Extras ────────────────────────────────────────────────────────────────────


class ListaExtraView(generics.ListCreateAPIView):
    queryset = Extra.objects.filter(activo=True)
    serializer_class = ExtraSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), EsAdminOSupervisor()]


class DetalleExtraView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Extra.objects.all()
    serializer_class = ExtraSerializer
    permission_classes = [IsAuthenticated, EsAdminOSupervisor]


# ── Productos ─────────────────────────────────────────────────────────────────


class ListaProductoView(generics.ListCreateAPIView):
    """
    GET  → lista compacta, filtrable por ?categoria=<id>&disponible=true&activo=true
    POST → crea producto (admin/supervisor)
    """

    def get_queryset(self):
        qs = Producto.objects.select_related("categoria").prefetch_related("extras")
        categoria = self.request.query_params.get("categoria")
        disponible = self.request.query_params.get("disponible")
        activo = self.request.query_params.get("activo")
        if categoria:
            qs = qs.filter(categoria_id=categoria)
        if disponible is not None:
            qs = qs.filter(disponible=disponible.lower() == "true")
        if activo is not None:
            qs = qs.filter(activo=activo.lower() == "true")
        return qs

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProductoEscrituraSerializer
        return ProductoListSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), EsAdminOSupervisor()]

    def perform_create(self, serializer):
        producto = serializer.save()
        registrar_accion(
            usuario=self.request.user,
            modulo="catalogo",
            accion="crear",
            detalle=f"Producto creado: {producto.nombre}",
        )


class DetalleProductoView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Producto.objects.prefetch_related("variantes", "extras")

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return ProductoEscrituraSerializer
        return ProductoDetalleSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), EsAdminOSupervisor()]

    def perform_update(self, serializer):
        precio_anterior = serializer.instance.precio_venta
        producto = serializer.save()

        # Registrar historial con usuario si cambió el precio
        precio_nuevo = producto.precio_venta
        if precio_anterior != precio_nuevo:
            # La señal ya crea el registro sin usuario; aquí lo completamos
            ultimo = producto.historial_precios.order_by("-fecha").first()
            if ultimo and ultimo.modificado_por is None:
                ultimo.modificado_por = self.request.user
                ultimo.save(update_fields=["modificado_por"])

        registrar_accion(
            usuario=self.request.user,
            modulo="catalogo",
            accion="editar",
            detalle=f"Producto editado: {producto.nombre}",
        )

    def destroy(self, request, *args, **kwargs):
        producto = self.get_object()
        producto.activo = False
        producto.disponible = False
        producto.save()
        registrar_accion(
            usuario=request.user,
            modulo="catalogo",
            accion="eliminar",
            detalle=f"Producto desactivado: {producto.nombre}",
        )
        return Response({"detalle": "Producto desactivado."})


# ── Variantes ─────────────────────────────────────────────────────────────────


class ListaVarianteView(generics.ListCreateAPIView):
    """
    GET  /api/catalogo/productos/<producto_id>/variantes/
    POST /api/catalogo/productos/<producto_id>/variantes/
    """

    serializer_class = VarianteSerializer
    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def get_queryset(self):
        return VarianteProducto.objects.filter(producto_id=self.kwargs["producto_id"])

    def perform_create(self, serializer):
        serializer.save(producto_id=self.kwargs["producto_id"])


class DetalleVarianteView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = VarianteSerializer
    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def get_queryset(self):
        return VarianteProducto.objects.filter(producto_id=self.kwargs["producto_id"])


# ── Combos ────────────────────────────────────────────────────────────────────


class ListaComboView(generics.ListCreateAPIView):
    queryset = Combo.objects.prefetch_related("items__producto")
    serializer_class = ComboSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), EsAdminOSupervisor()]


class DetalleComboView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Combo.objects.prefetch_related("items__producto")
    serializer_class = ComboSerializer
    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def destroy(self, request, *args, **kwargs):
        combo = self.get_object()
        combo.activo = False
        combo.save()
        return Response({"detalle": "Combo desactivado."})


# ── Menú público (sin autenticación) ─────────────────────────────────────────


class MenuPublicoView(APIView):
    """
    GET /api/catalogo/menu-publico/
    Devuelve categorías activas con sus productos visibles en menú QR.
    No requiere autenticación — se usa en el menú QR del local.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        from django.db.models import Prefetch

        productos_qs = Producto.objects.filter(
            activo=True, disponible=True, visible_menu_qr=True
        ).prefetch_related("variantes", "extras")

        categorias = (
            Categoria.objects.filter(activo=True, visible_menu_qr=True)
            .prefetch_related(Prefetch("productos", queryset=productos_qs))
            .order_by("orden")
        )

        resultado = []
        for categoria in categorias:
            productos = [
                p
                for p in categoria.productos.all()
                if p.activo and p.disponible and p.visible_menu_qr
            ]
            resultado.append(
                {
                    "id": categoria.id,
                    "nombre": categoria.nombre,
                    "imagen": (
                        request.build_absolute_uri(categoria.imagen.url)
                        if categoria.imagen
                        else None
                    ),
                    "productos": ProductoDetalleSerializer(
                        productos, many=True, context={"request": request}
                    ).data,
                }
            )
        return Response(resultado)


# ── Historial de precios ──────────────────────────────────────────────────────


class HistorialPrecioView(generics.ListAPIView):
    """GET /api/catalogo/productos/<producto_id>/historial-precios/"""

    serializer_class = HistorialPrecioSerializer
    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def get_queryset(self):
        return HistorialPrecio.objects.filter(
            producto_id=self.kwargs["producto_id"]
        ).select_related("modificado_por")
