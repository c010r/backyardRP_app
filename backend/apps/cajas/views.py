from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auditoria.utils import registrar_accion
from apps.comandas.models import Comanda, EstadoComanda
from apps.mesas.utils import liberar_mesa_si_libre
from apps.usuarios.permissions import EsAdminOSupervisor, EsEmpleado
from .models import Caja, CierreCaja, MovimientoCaja, PagoComanda, TipoMovimiento
from .serializers import (
    AperturaCajaSerializer,
    ArqueoCajaSerializer,
    CajaSerializer,
    CierreCajaSerializer,
    CobrarComandaSerializer,
    MovimientoCajaSerializer,
    PagoComandaSerializer,
)


class AbrirCajaView(APIView):
    """
    POST /api/cajas/abrir/
    El cajero abre su caja. Solo puede haber una abierta por cajero.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if Caja.objects.filter(cajero=request.user, abierta=True).exists():
            return Response(
                {"detalle": "Ya tenés una caja abierta."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = AperturaCajaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        caja = Caja.objects.create(cajero=request.user, **serializer.validated_data)
        registrar_accion(
            usuario=request.user,
            modulo="cajas",
            accion="apertura_caja",
            detalle=f"Caja #{caja.id} abierta con ${caja.monto_inicial}",
            request=request,
        )
        return Response(CajaSerializer(caja).data, status=status.HTTP_201_CREATED)


class CerrarCajaView(APIView):
    """
    POST /api/cajas/<id>/cerrar/
    Cierra la caja, genera el resumen por medio de pago y registra el arqueo.
    """

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        try:
            caja = Caja.objects.get(pk=pk, cajero=request.user, abierta=True)
        except Caja.DoesNotExist:
            return Response(
                {"detalle": "Caja no encontrada o no te pertenece."}, status=404
            )

        serializer = ArqueoCajaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Resumen por medio de pago: una sola query con GROUP BY
        resumen = (
            PagoComanda.objects.filter(caja=caja)
            .values("medio_pago")
            .annotate(total_cobrado=Sum("monto"), total_propinas=Sum("propina"))
        )
        CierreCaja.objects.bulk_create(
            [
                CierreCaja(
                    caja=caja,
                    medio_pago=row["medio_pago"],
                    total_cobrado=row["total_cobrado"] or Decimal("0"),
                    total_propinas=row["total_propinas"] or Decimal("0"),
                )
                for row in resumen
            ]
        )

        # Calcular saldo antes de guardar el cierre (mientras aún podemos leer movimientos)
        saldo_esperado = caja.saldo_esperado

        caja.abierta = False
        caja.monto_final_declarado = serializer.validated_data["monto_final_declarado"]
        caja.cerrada_en = timezone.now()
        caja.save()

        diferencia = caja.monto_final_declarado - saldo_esperado

        registrar_accion(
            usuario=request.user,
            modulo="cajas",
            accion="cierre_caja",
            detalle=f"Caja #{caja.id} cerrada. Diferencia: ${diferencia}",
            request=request,
        )
        return Response(
            {
                "caja": CajaSerializer(caja).data,
                "resumen_medios": CierreCajaSerializer(
                    CierreCaja.objects.filter(caja=caja), many=True
                ).data,
                "diferencia": diferencia,
            }
        )


class MiCajaView(APIView):
    """
    GET /api/cajas/mi-caja/
    Devuelve la caja actualmente abierta del usuario autenticado.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            caja = Caja.objects.get(cajero=request.user, abierta=True)
        except Caja.DoesNotExist:
            return Response({"detalle": "No tenés una caja abierta."}, status=404)
        return Response(CajaSerializer(caja, context={"request": request}).data)


class ListaCajaView(generics.ListAPIView):
    """GET /api/cajas/  → historial de cajas (admin/supervisor)"""

    serializer_class = CajaSerializer
    permission_classes = [IsAuthenticated, EsAdminOSupervisor]
    queryset = Caja.objects.select_related("cajero").order_by("-creado_en")


class DetalleCajaView(generics.RetrieveAPIView):
    serializer_class = CajaSerializer
    permission_classes = [IsAuthenticated, EsAdminOSupervisor]
    queryset = Caja.objects.select_related("cajero")


class CobrarComandaView(APIView):
    """
    POST /api/cajas/cobrar/
    Cobra una comanda. Soporta múltiples medios de pago.
    Cierra la comanda y libera la mesa.
    """

    permission_classes = [IsAuthenticated, EsEmpleado]

    @transaction.atomic
    def post(self, request):
        try:
            caja = Caja.objects.get(cajero=request.user, abierta=True)
        except Caja.DoesNotExist:
            return Response({"detalle": "No tenés una caja abierta."}, status=400)

        serializer = CobrarComandaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            comanda = Comanda.objects.select_related("mesa").get(
                pk=serializer.validated_data["comanda_id"]
            )
        except Comanda.DoesNotExist:
            return Response({"detalle": "Comanda no encontrada."}, status=404)

        if comanda.estado == EstadoComanda.CERRADA:
            return Response({"detalle": "La comanda ya fue cobrada."}, status=400)

        pagos_creados = []
        for pago_data in serializer.validated_data["pagos"]:
            pago = PagoComanda.objects.create(
                caja=caja,
                comanda=comanda,
                medio_pago=pago_data["medio_pago"],
                monto=pago_data["monto"],
                propina=pago_data.get("propina", 0),
                registrado_por=request.user,
            )
            MovimientoCaja.objects.create(
                caja=caja,
                tipo=TipoMovimiento.INGRESO,
                medio_pago=pago_data["medio_pago"],
                monto=pago_data["monto"],
                descripcion=f"Cobro comanda #{comanda.numero}",
                registrado_por=request.user,
            )
            pagos_creados.append(pago)

        total = comanda.total  # una sola query aggregate antes de cerrar

        comanda.estado = EstadoComanda.CERRADA
        comanda.cerrada_en = timezone.now()
        comanda.save(update_fields=["estado", "cerrada_en"])

        liberar_mesa_si_libre(comanda.mesa, excluir_comanda_pk=comanda.pk)

        registrar_accion(
            usuario=request.user,
            modulo="cajas",
            accion="cobro",
            detalle=f"Comanda #{comanda.numero} cobrada. Total: ${total}",
            request=request,
        )
        return Response(
            {
                "detalle": f"Comanda #{comanda.numero} cobrada correctamente.",
                "pagos": PagoComandaSerializer(pagos_creados, many=True).data,
            }
        )


class MovimientosView(generics.ListCreateAPIView):
    """
    GET  /api/cajas/<caja_id>/movimientos/
    POST /api/cajas/<caja_id>/movimientos/   → ingreso/egreso manual
    """

    serializer_class = MovimientoCajaSerializer
    permission_classes = [IsAuthenticated, EsEmpleado]

    def get_queryset(self):
        return MovimientoCaja.objects.filter(caja_id=self.kwargs["caja_id"])

    def perform_create(self, serializer):
        caja = Caja.objects.get(pk=self.kwargs["caja_id"], abierta=True)
        serializer.save(caja=caja, registrado_por=self.request.user)
