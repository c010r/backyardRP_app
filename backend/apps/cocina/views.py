from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auditoria.utils import registrar_accion
from apps.comandas.models import Comanda, EstadoComanda, EstadoCocina, ItemComanda
from apps.usuarios.permissions import EsEmpleado
from .serializers import ComandaCocinaSerializer, ItemCocinaSerializer


class PanelCocinaView(APIView):
    """
    GET /api/cocina/
    Panel principal de cocina: comandas activas con ítems enviados y no entregados.
    Diseñado para hacer polling cada N segundos desde el frontend.
    Ordena por tiempo de espera (más antiguas primero).
    """

    permission_classes = [IsAuthenticated, EsEmpleado]

    def get(self, request):
        estado_filtro = request.query_params.get("estado_cocina")

        # Comandas que tienen al menos un ítem enviado a cocina y no entregado
        comandas = (
            Comanda.objects.filter(
                estado__in=[EstadoComanda.ENVIADA, EstadoComanda.ABIERTA],
                items__enviado_cocina=True,
                items__cancelado=False,
            )
            .exclude(items__estado_cocina=EstadoCocina.ENTREGADO)
            .distinct()
            .select_related("mesa", "mozo")
            .prefetch_related(
                "items__producto",
                "items__variante__producto",
                "items__combo",
            )
            .order_by("creado_en")
        )

        if estado_filtro:
            comandas = comandas.filter(items__estado_cocina=estado_filtro)

        return Response(ComandaCocinaSerializer(comandas, many=True).data)


class ActualizarEstadoItemView(APIView):
    """
    PATCH /api/cocina/items/<item_id>/estado/
    La cocina actualiza el estado de un ítem individual.
    Cuando todos los ítems de una comanda están listos, la comanda pasa a LISTA.
    """

    permission_classes = [IsAuthenticated, EsEmpleado]

    def patch(self, request, item_id):
        try:
            item = ItemComanda.objects.select_related("comanda").get(
                pk=item_id, enviado_cocina=True, cancelado=False
            )
        except ItemComanda.DoesNotExist:
            return Response({"detalle": "Ítem no encontrado."}, status=404)

        nuevo_estado = request.data.get("estado_cocina")
        if nuevo_estado not in EstadoCocina.values:
            return Response(
                {"detalle": f"Estado inválido. Opciones: {EstadoCocina.values}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item.estado_cocina = nuevo_estado
        item.save(update_fields=["estado_cocina"])

        # Si todos los ítems de la comanda están listos → comanda LISTA
        comanda = item.comanda
        items_activos = comanda.items.filter(enviado_cocina=True, cancelado=False)
        todos_listos = all(
            i.estado_cocina in (EstadoCocina.LISTO, EstadoCocina.ENTREGADO)
            for i in items_activos
        )
        if todos_listos and comanda.estado == EstadoComanda.ENVIADA:
            comanda.estado = EstadoComanda.LISTA
            comanda.save(update_fields=["estado"])

        return Response(ItemCocinaSerializer(item).data)


class MarcarComandaListaView(APIView):
    """
    POST /api/cocina/comandas/<id>/lista/
    Marca todos los ítems de una comanda como LISTO de una sola vez.
    """

    permission_classes = [IsAuthenticated, EsEmpleado]

    def post(self, request, pk):
        try:
            comanda = Comanda.objects.get(pk=pk)
        except Comanda.DoesNotExist:
            return Response({"detalle": "Comanda no encontrada."}, status=404)

        comanda.items.filter(
            enviado_cocina=True,
            cancelado=False,
            estado_cocina=EstadoCocina.EN_PREPARACION,
        ).update(estado_cocina=EstadoCocina.LISTO)

        comanda.estado = EstadoComanda.LISTA
        comanda.save(update_fields=["estado"])

        registrar_accion(
            usuario=request.user,
            modulo="cocina",
            accion="editar",
            detalle=f"Comanda #{comanda.numero} marcada como lista",
        )
        return Response({"detalle": f"Comanda #{comanda.numero} marcada como lista."})
