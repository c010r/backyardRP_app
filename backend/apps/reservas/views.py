import datetime

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auditoria.utils import registrar_accion
from apps.usuarios.permissions import EsAdminOSupervisor, EsEmpleado
from .models import EstadoReserva, OrigenReserva, Reserva
from .serializers import (
    CambiarEstadoReservaSerializer,
    ReservaInternaSerializer,
    ReservaPublicaSerializer,
)


class ReservaPublicaView(generics.CreateAPIView):
    """
    POST /api/reservas/publica/
    Formulario web de reservas. Sin autenticación.
    Crea la reserva en estado PENDIENTE para que el staff la confirme.
    """

    serializer_class = ReservaPublicaSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reserva = serializer.save()
        return Response(
            {
                "detalle": "Reserva recibida. Te contactaremos para confirmar.",
                "id": reserva.id,
            },
            status=status.HTTP_201_CREATED,
        )


class DisponibilidadView(APIView):
    """
    GET /api/reservas/disponibilidad/?fecha=2024-12-21
    Devuelve el horario del negocio para esa fecha y el total de reservas existentes.
    Público — para que el formulario web muestre si hay disponibilidad.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        from apps.configuracion.models import DiaSemana, HorarioNegocio

        fecha_str = request.query_params.get("fecha")
        if not fecha_str:
            return Response({"detalle": "Parámetro 'fecha' requerido."}, status=400)

        try:
            fecha = datetime.date.fromisoformat(fecha_str)
        except ValueError:
            return Response(
                {"detalle": "Formato de fecha inválido. Use YYYY-MM-DD."}, status=400
            )

        dias = {
            0: DiaSemana.LUNES,
            1: DiaSemana.MARTES,
            2: DiaSemana.MIERCOLES,
            3: DiaSemana.JUEVES,
            4: DiaSemana.VIERNES,
            5: DiaSemana.SABADO,
            6: DiaSemana.DOMINGO,
        }
        dia = dias.get(fecha.weekday())
        try:
            horario = HorarioNegocio.objects.get(dia=dia, activo=True)
            abierto = True
            apertura = str(horario.apertura)
            cierre = str(horario.cierre)
        except HorarioNegocio.DoesNotExist:
            abierto = False
            apertura = cierre = None

        total_reservas = Reserva.objects.filter(
            fecha=fecha, estado__in=[EstadoReserva.PENDIENTE, EstadoReserva.CONFIRMADA]
        ).count()

        return Response(
            {
                "fecha": fecha_str,
                "abierto": abierto,
                "apertura": apertura,
                "cierre": cierre,
                "reservas_existentes": total_reservas,
            }
        )


# ── Panel interno ─────────────────────────────────────────────────────────────


class ListaReservaView(generics.ListCreateAPIView):
    """
    GET  /api/reservas/?fecha=2024-12-21&estado=pendiente
    POST /api/reservas/   → carga interna de reserva
    """

    serializer_class = ReservaInternaSerializer
    permission_classes = [IsAuthenticated, EsEmpleado]

    def get_queryset(self):
        qs = Reserva.objects.select_related("mesa", "gestionada_por", "usuario")
        fecha = self.request.query_params.get("fecha")
        estado = self.request.query_params.get("estado")
        if fecha:
            qs = qs.filter(fecha=fecha)
        if estado:
            qs = qs.filter(estado=estado)
        return qs.order_by("fecha", "hora")

    def perform_create(self, serializer):
        reserva = serializer.save(
            gestionada_por=self.request.user,
            origen=OrigenReserva.INTERNO,
        )
        registrar_accion(
            usuario=self.request.user,
            modulo="reservas",
            accion="crear",
            detalle=f"Reserva creada: {reserva.nombre_contacto} {reserva.fecha} {reserva.hora}",
        )


class DetalleReservaView(generics.RetrieveUpdateAPIView):
    serializer_class = ReservaInternaSerializer
    permission_classes = [IsAuthenticated, EsEmpleado]
    queryset = Reserva.objects.select_related("mesa", "gestionada_por", "usuario")

    def perform_update(self, serializer):
        serializer.save(gestionada_por=self.request.user)


class CambiarEstadoReservaView(APIView):
    """
    PATCH /api/reservas/<id>/estado/
    Cambia el estado de una reserva con observación opcional.
    """

    permission_classes = [IsAuthenticated, EsEmpleado]

    def patch(self, request, pk):
        try:
            reserva = Reserva.objects.get(pk=pk)
        except Reserva.DoesNotExist:
            return Response({"detalle": "Reserva no encontrada."}, status=404)

        serializer = CambiarEstadoReservaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        estado_anterior = reserva.estado
        reserva.estado = serializer.validated_data["estado"]
        if serializer.validated_data.get("observaciones"):
            reserva.observaciones = (
                f"{reserva.observaciones}\n[{request.user.username}] "
                f"{serializer.validated_data['observaciones']}"
            ).strip()
        reserva.gestionada_por = request.user
        reserva.save()

        registrar_accion(
            usuario=request.user,
            modulo="reservas",
            accion="editar",
            detalle=f"Reserva #{pk}: {estado_anterior} → {reserva.estado}",
        )
        return Response(ReservaInternaSerializer(reserva).data)
