from django.utils import timezone
from rest_framework import filters, generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auditoria.utils import registrar_accion
from apps.usuarios.permissions import EsAdminOSupervisor, EsEmpleado
from .models import Entrada, EstadoEntrada, Evento, TipoEntrada
from .serializers import (
    CambiarEstadoEntradaSerializer,
    EntradaPublicaSerializer,
    EntradaSerializer,
    EventoListSerializer,
    EventoSerializer,
    TipoEntradaSerializer,
    ValidarEntradaSerializer,
)


class ListaEventoPublicoView(generics.ListAPIView):
    """GET /api/eventos/publicos/  — Sin autenticación."""

    permission_classes = [AllowAny]
    serializer_class = EventoListSerializer

    def get_queryset(self):
        return Evento.objects.filter(activo=True, visible_publico=True)


class DetalleEventoPublicoView(generics.RetrieveAPIView):
    """GET /api/eventos/publicos/<id>/"""

    permission_classes = [AllowAny]
    serializer_class = EventoSerializer

    def get_queryset(self):
        return Evento.objects.filter(
            activo=True, visible_publico=True
        ).prefetch_related("tipos_entrada")


class ListaEventoAdminView(generics.ListCreateAPIView):
    """GET/POST /api/eventos/"""

    permission_classes = [IsAuthenticated, EsAdminOSupervisor]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nombre"]
    ordering_fields = ["fecha", "nombre"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return EventoSerializer
        return EventoListSerializer

    def get_queryset(self):
        return Evento.objects.prefetch_related("tipos_entrada")


class DetalleEventoAdminView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH/DELETE /api/eventos/<id>/"""

    queryset = Evento.objects.prefetch_related("tipos_entrada")
    serializer_class = EventoSerializer
    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def perform_destroy(self, instance):
        instance.activo = False
        instance.save(update_fields=["activo"])


class ListaTipoEntradaView(generics.ListCreateAPIView):
    """GET/POST /api/eventos/<evento_id>/tipos/"""

    serializer_class = TipoEntradaSerializer
    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def get_queryset(self):
        return TipoEntrada.objects.filter(evento_id=self.kwargs["evento_id"])

    def perform_create(self, serializer):
        evento = Evento.objects.get(pk=self.kwargs["evento_id"])
        serializer.save(evento=evento)


class ComprarEntradaView(generics.CreateAPIView):
    """POST /api/eventos/comprar/  — Público, sin autenticación requerida."""

    permission_classes = [AllowAny]
    serializer_class = EntradaPublicaSerializer

    def perform_create(self, serializer):
        cliente = self.request.user if self.request.user.is_authenticated else None
        serializer.save(cliente=cliente)


class ListaEntradasView(generics.ListAPIView):
    """GET /api/eventos/<evento_id>/entradas/  — Panel interno."""

    serializer_class = EntradaSerializer
    permission_classes = [IsAuthenticated, EsEmpleado]

    def get_queryset(self):
        return Entrada.objects.filter(
            tipo_entrada__evento_id=self.kwargs["evento_id"]
        ).select_related("tipo_entrada__evento", "cliente", "validada_por")


class ValidarEntradaView(APIView):
    """
    POST /api/eventos/validar/
    Escanea el código QR y marca la entrada como validada (control de acceso).
    """

    permission_classes = [IsAuthenticated, EsEmpleado]

    def post(self, request):
        serializer = ValidarEntradaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        codigo = serializer.validated_data["codigo_qr"]

        try:
            entrada = Entrada.objects.select_related("tipo_entrada__evento").get(
                codigo_qr=codigo
            )
        except Entrada.DoesNotExist:
            return Response({"detalle": "Código QR inválido."}, status=404)

        if entrada.estado == EstadoEntrada.VALIDADA:
            return Response(
                {
                    "detalle": "Esta entrada ya fue validada.",
                    "entrada": EntradaSerializer(entrada).data,
                },
                status=status.HTTP_409_CONFLICT,
            )
        if entrada.estado not in (EstadoEntrada.PAGADA, EstadoEntrada.PENDIENTE):
            return Response(
                {
                    "detalle": f"No se puede validar una entrada {entrada.get_estado_display()}."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        entrada.estado = EstadoEntrada.VALIDADA
        entrada.validada_por = request.user
        entrada.validada_en = timezone.now()
        entrada.save(update_fields=["estado", "validada_por", "validada_en"])

        registrar_accion(
            usuario=request.user,
            modulo="eventos",
            accion="editar",
            detalle=(
                f"Entrada validada: {entrada.nombre_comprador} "
                f"— {entrada.tipo_entrada.evento.nombre}"
            ),
            request=request,
        )
        return Response(
            {
                "detalle": "Entrada validada correctamente.",
                "entrada": EntradaSerializer(entrada).data,
            }
        )


class CambiarEstadoEntradaView(APIView):
    """PATCH /api/eventos/entradas/<id>/estado/  — Confirmar pago, cancelar, etc."""

    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def patch(self, request, pk):
        try:
            entrada = Entrada.objects.get(pk=pk)
        except Entrada.DoesNotExist:
            return Response({"detalle": "Entrada no encontrada."}, status=404)

        serializer = CambiarEstadoEntradaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entrada.estado = serializer.validated_data["estado"]
        entrada.save(update_fields=["estado"])
        return Response(EntradaSerializer(entrada).data)
