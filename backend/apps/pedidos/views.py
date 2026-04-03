from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auditoria.utils import registrar_accion
from apps.usuarios.models import Usuario
from apps.usuarios.permissions import EsEmpleado
from .models import EstadoPedido, Pedido, TipoPedido
from .serializers import (
    CambiarEstadoPedidoSerializer,
    PedidoListSerializer,
    PedidoPublicoSerializer,
    PedidoSerializer,
)


class PedidoPublicoView(generics.CreateAPIView):
    """
    POST /api/pedidos/nuevo/
    El cliente crea su pedido desde la web. Sin autenticación.
    """

    serializer_class = PedidoPublicoSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pedido = serializer.save()
        return Response(
            {
                "detalle": "Pedido recibido. Te avisamos cuando esté listo.",
                "numero": pedido.numero,
                "total": pedido.total,
            },
            status=status.HTTP_201_CREATED,
        )


class SeguimientoPedidoView(APIView):
    """
    GET /api/pedidos/seguimiento/<numero>/
    El cliente consulta el estado de su pedido con el número recibido.
    Sin autenticación.
    """

    permission_classes = [AllowAny]

    def get(self, request, numero):
        try:
            pedido = Pedido.objects.get(numero=numero)
        except Pedido.DoesNotExist:
            return Response({"detalle": "Pedido no encontrado."}, status=404)
        return Response(
            {
                "numero": pedido.numero,
                "estado": pedido.estado,
                "estado_display": pedido.get_estado_display(),
                "tipo": pedido.tipo,
                "total": pedido.total,
            }
        )


# ── Panel interno ─────────────────────────────────────────────────────────────


class ListaPedidoView(generics.ListAPIView):
    """
    GET /api/pedidos/?estado=recibido&tipo=delivery
    Panel de gestión de pedidos para el staff.
    """

    permission_classes = [IsAuthenticated, EsEmpleado]

    def get_serializer_class(self):
        return PedidoListSerializer

    def get_queryset(self):
        qs = Pedido.objects.select_related("cliente", "repartidor").order_by(
            "-creado_en"
        )
        estado = self.request.query_params.get("estado")
        tipo = self.request.query_params.get("tipo")
        if estado:
            qs = qs.filter(estado=estado)
        if tipo:
            qs = qs.filter(tipo=tipo)
        return qs


class DetallePedidoView(generics.RetrieveAPIView):
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated, EsEmpleado]
    queryset = Pedido.objects.prefetch_related(
        "items__producto", "items__variante__producto", "items__combo"
    ).select_related("cliente", "repartidor", "atendido_por", "comanda_interna")


class CambiarEstadoPedidoView(APIView):
    """
    PATCH /api/pedidos/<id>/estado/
    Avanza el estado del pedido. Si pasa a EN_CAMINO, puede asignar repartidor.
    """

    permission_classes = [IsAuthenticated, EsEmpleado]

    def patch(self, request, pk):
        try:
            pedido = Pedido.objects.get(pk=pk)
        except Pedido.DoesNotExist:
            return Response({"detalle": "Pedido no encontrado."}, status=404)

        serializer = CambiarEstadoPedidoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        estado_anterior = pedido.estado
        pedido.estado = serializer.validated_data["estado"]
        pedido.atendido_por = request.user

        repartidor_id = serializer.validated_data.get("repartidor_id")
        if repartidor_id:
            try:
                pedido.repartidor = Usuario.objects.get(pk=repartidor_id)
            except Usuario.DoesNotExist:
                return Response({"detalle": "Repartidor no encontrado."}, status=400)

        pedido.save()

        registrar_accion(
            usuario=request.user,
            modulo="pedidos",
            accion="editar",
            detalle=f"Pedido #{pedido.numero}: {estado_anterior} → {pedido.estado}",
        )
        return Response(PedidoSerializer(pedido).data)


class MarcarPagadoView(APIView):
    """
    PATCH /api/pedidos/<id>/pagado/
    Registra el pago del pedido (cuando se confirma transferencia o Mercado Pago).
    """

    permission_classes = [IsAuthenticated, EsEmpleado]

    def patch(self, request, pk):
        try:
            pedido = Pedido.objects.get(pk=pk)
        except Pedido.DoesNotExist:
            return Response({"detalle": "Pedido no encontrado."}, status=404)

        pedido.pagado = True
        pedido.atendido_por = request.user
        pedido.save(update_fields=["pagado", "atendido_por"])
        return Response({"detalle": f"Pedido #{pedido.numero} marcado como pagado."})
