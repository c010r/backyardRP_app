"""
Vistas de facturación.

v1: Registro local de comprobantes, sin integración real con DGI.
v2: Implementar llamadas al webservice DGI (e-Factura) para obtener CAE.
"""

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.usuarios.permissions import EsAdminOSupervisor, EsCajero
from .models import Comprobante, EstadoComprobante
from .serializers import ComprobanteSerializer, EmitirComprobanteSerializer


class ListaComprobanteView(generics.ListAPIView):
    """GET /api/facturacion/  — Listado de comprobantes emitidos."""

    serializer_class = ComprobanteSerializer
    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def get_queryset(self):
        qs = Comprobante.objects.select_related(
            "comanda", "pedido", "emitido_por"
        ).prefetch_related("items")
        tipo = self.request.query_params.get("tipo")
        estado = self.request.query_params.get("estado")
        if tipo:
            qs = qs.filter(tipo=tipo)
        if estado:
            qs = qs.filter(estado=estado)
        return qs


class DetalleComprobanteView(generics.RetrieveAPIView):
    """GET /api/facturacion/<id>/"""

    queryset = Comprobante.objects.prefetch_related("items")
    serializer_class = ComprobanteSerializer
    permission_classes = [IsAuthenticated, EsAdminOSupervisor]


class EmitirComprobanteView(APIView):
    """
    POST /api/facturacion/emitir/
    Crea un comprobante local. En v2 se enviará a DGI para obtener CAE.
    """

    permission_classes = [IsAuthenticated, EsCajero]

    def post(self, request):
        serializer = EmitirComprobanteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Obtener la comanda o pedido y calcular totales
        comanda = pedido = None
        total = subtotal = iva = 0

        if data.get("comanda_id"):
            from apps.comandas.models import Comanda

            try:
                comanda = Comanda.objects.get(pk=data["comanda_id"])
            except Comanda.DoesNotExist:
                return Response({"detalle": "Comanda no encontrada."}, status=404)
            total = comanda.total
        else:
            from apps.pedidos.models import Pedido

            try:
                pedido = Pedido.objects.get(pk=data["pedido_id"])
            except Pedido.DoesNotExist:
                return Response({"detalle": "Pedido no encontrado."}, status=404)
            total = pedido.total

        # Cálculo simplificado: IVA 22% incluido en el precio
        from decimal import Decimal
        iva_rate = Decimal("22")
        subtotal = round(total / (1 + iva_rate / 100), 2)
        iva = total - subtotal

        # Próximo número de comprobante para este tipo y punto de venta
        ultimo = (
            Comprobante.objects.filter(tipo=data["tipo"], punto_venta=1)
            .order_by("-numero")
            .first()
        )
        numero = (ultimo.numero + 1) if (ultimo and ultimo.numero) else 1

        comprobante = Comprobante.objects.create(
            tipo=data["tipo"],
            estado=EstadoComprobante.PENDIENTE,  # DGI integration pending
            punto_venta=1,
            numero=numero,
            razon_social_receptor=data["razon_social_receptor"],
            documento_receptor=data.get("documento_receptor", ""),
            tipo_documento_receptor=data.get(
                "tipo_documento_receptor", "Consumidor Final"
            ),
            subtotal=subtotal,
            iva=iva,
            total=total,
            comanda=comanda,
            pedido=pedido,
            emitido_por=request.user,
        )

        # TODO v2: llamar a servicio DGI para obtener CAE
        # from .services import dgi_obtener_cae
        # dgi_obtener_cae(comprobante)

        return Response(
            ComprobanteSerializer(comprobante).data,
            status=status.HTTP_201_CREATED,
        )
