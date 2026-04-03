from django.utils import timezone
from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auditoria.utils import registrar_accion
from apps.mesas.models import EstadoMesa, Mesa
from apps.mesas.utils import liberar_mesa_si_libre
from apps.usuarios.permissions import EsAdminOSupervisor, EsEmpleado
from .models import Comanda, EstadoComanda, ItemComanda
from .serializers import (
    ComandaListSerializer,
    ComandaSerializer,
    ItemComandaEscrituraSerializer,
    ItemComandaSerializer,
    TransferirMesaSerializer,
)


class ListaComandaView(generics.ListCreateAPIView):
    """
    GET  /api/comandas/?estado=abierta&mesa=<id>&mozo=<id>
    POST /api/comandas/   → abre una comanda nueva
    """

    permission_classes = [IsAuthenticated, EsEmpleado]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ComandaSerializer
        return ComandaListSerializer

    def get_queryset(self):
        qs = Comanda.objects.select_related("mesa", "mozo").prefetch_related("items")
        estado = self.request.query_params.get("estado")
        mesa_id = self.request.query_params.get("mesa")
        mozo_id = self.request.query_params.get("mozo")
        if estado:
            qs = qs.filter(estado=estado)
        if mesa_id:
            qs = qs.filter(mesa_id=mesa_id)
        if mozo_id:
            qs = qs.filter(mozo_id=mozo_id)
        return qs

    def perform_create(self, serializer):
        comanda = serializer.save()
        if comanda.mesa:
            comanda.mesa.estado = EstadoMesa.OCUPADA
            comanda.mesa.save(update_fields=["estado"])
        registrar_accion(
            usuario=self.request.user,
            modulo="comandas",
            accion="crear",
            detalle=f"Comanda #{comanda.numero} abierta",
        )


class DetalleComandaView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/comandas/<id>/
    PATCH /api/comandas/<id>/
    """

    serializer_class = ComandaSerializer
    permission_classes = [IsAuthenticated, EsEmpleado]
    queryset = Comanda.objects.prefetch_related(
        "items__producto", "items__variante", "items__combo"
    ).select_related("mesa", "mozo")


# ── Ítems ─────────────────────────────────────────────────────────────────────


class AgregarItemView(generics.CreateAPIView):
    """
    POST /api/comandas/<comanda_id>/items/
    Agrega un ítem a la comanda. El precio se toma del catálogo automáticamente.
    """

    serializer_class = ItemComandaEscrituraSerializer
    permission_classes = [IsAuthenticated, EsEmpleado]

    def perform_create(self, serializer):
        comanda = Comanda.objects.get(pk=self.kwargs["comanda_id"])
        if comanda.estado in (EstadoComanda.CERRADA, EstadoComanda.CANCELADA):
            raise serializers.ValidationError(
                {
                    "detalle": "No se pueden agregar ítems a una comanda cerrada o cancelada."
                }
            )
        serializer.save(comanda=comanda)


class CancelarItemView(APIView):
    """
    PATCH /api/comandas/<comanda_id>/items/<item_id>/cancelar/
    Cancela un ítem individual. Solo admin puede cancelar ítems ya enviados a cocina.
    """

    permission_classes = [IsAuthenticated, EsEmpleado]

    def patch(self, request, comanda_id, item_id):
        try:
            item = ItemComanda.objects.get(pk=item_id, comanda_id=comanda_id)
        except ItemComanda.DoesNotExist:
            return Response({"detalle": "Ítem no encontrado."}, status=404)

        if item.cancelado:
            return Response({"detalle": "El ítem ya estaba cancelado."})

        if item.enviado_cocina and not request.user.es_admin:
            return Response(
                {
                    "detalle": "Solo un administrador puede cancelar un ítem ya enviado a cocina."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        item.cancelado = True
        item.cancelado_por = request.user
        item.save(update_fields=["cancelado", "cancelado_por"])
        registrar_accion(
            usuario=request.user,
            modulo="comandas",
            accion="editar",
            detalle=f"Ítem cancelado en comanda #{item.comanda.numero}: {item}",
        )
        return Response(ItemComandaSerializer(item).data)


# ── Acciones de comanda ───────────────────────────────────────────────────────


class EnviarCocinaView(APIView):
    """
    POST /api/comandas/<id>/enviar-cocina/
    Marca como enviados todos los ítems pendientes y actualiza el estado.
    """

    permission_classes = [IsAuthenticated, EsEmpleado]

    def post(self, request, pk):
        try:
            comanda = Comanda.objects.get(pk=pk)
        except Comanda.DoesNotExist:
            return Response({"detalle": "Comanda no encontrada."}, status=404)

        pendientes = comanda.items.filter(enviado_cocina=False, cancelado=False)
        # Evaluar la cuenta antes de hacer el update para el mensaje
        cantidad = pendientes.count()
        if not cantidad:
            return Response({"detalle": "No hay ítems pendientes de enviar."})

        pendientes.update(enviado_cocina=True)
        comanda.estado = EstadoComanda.ENVIADA
        comanda.save(update_fields=["estado"])

        registrar_accion(
            usuario=request.user,
            modulo="comandas",
            accion="envio_cocina",
            detalle=f"Comanda #{comanda.numero} enviada a cocina ({cantidad} ítems)",
        )
        return Response({"detalle": f"{cantidad} ítem(s) enviados a cocina."})


class TransferirMesaView(APIView):
    """
    POST /api/comandas/<id>/transferir-mesa/
    Reasigna la comanda a otra mesa.
    """

    permission_classes = [IsAuthenticated, EsEmpleado]

    def post(self, request, pk):
        try:
            comanda = Comanda.objects.select_related("mesa").get(pk=pk)
        except Comanda.DoesNotExist:
            return Response({"detalle": "Comanda no encontrada."}, status=404)

        serializer = TransferirMesaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mesa_destino = Mesa.objects.get(pk=serializer.validated_data["mesa_destino_id"])
        mesa_origen = comanda.mesa

        comanda.mesa = mesa_destino
        comanda.save(update_fields=["mesa"])

        liberar_mesa_si_libre(mesa_origen, excluir_comanda_pk=pk)

        mesa_destino.estado = EstadoMesa.OCUPADA
        mesa_destino.save(update_fields=["estado"])

        registrar_accion(
            usuario=request.user,
            modulo="comandas",
            accion="editar",
            detalle=f"Comanda #{comanda.numero} transferida a {mesa_destino}",
        )
        return Response(ComandaSerializer(comanda).data)


class CancelarComandaView(APIView):
    """
    POST /api/comandas/<id>/cancelar/
    Solo admin/supervisor pueden cancelar comandas.
    """

    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def post(self, request, pk):
        try:
            comanda = Comanda.objects.select_related("mesa").get(pk=pk)
        except Comanda.DoesNotExist:
            return Response({"detalle": "Comanda no encontrada."}, status=404)

        if comanda.estado == EstadoComanda.CERRADA:
            return Response(
                {"detalle": "No se puede cancelar una comanda cerrada."}, status=400
            )

        comanda.estado = EstadoComanda.CANCELADA
        comanda.save(update_fields=["estado"])

        liberar_mesa_si_libre(comanda.mesa)

        registrar_accion(
            usuario=request.user,
            modulo="comandas",
            accion="eliminar",
            detalle=f"Comanda #{comanda.numero} cancelada",
        )
        return Response({"detalle": f"Comanda #{comanda.numero} cancelada."})
