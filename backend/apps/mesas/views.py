from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auditoria.utils import registrar_accion
from apps.usuarios.permissions import EsAdminOSupervisor, EsEmpleado
from .models import Mesa, Ubicacion
from .serializers import (
    MesaEstadoSerializer,
    MesaPosicionSerializer,
    MesaSerializer,
    UbicacionSerializer,
)

# ── Ubicaciones ───────────────────────────────────────────────────────────────


class ListaUbicacionView(generics.ListCreateAPIView):
    queryset = Ubicacion.objects.filter(activo=True)
    serializer_class = UbicacionSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), EsAdminOSupervisor()]


class DetalleUbicacionView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Ubicacion.objects.all()
    serializer_class = UbicacionSerializer
    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def destroy(self, request, *args, **kwargs):
        ubicacion = self.get_object()
        if ubicacion.mesas.filter(activo=True).exists():
            return Response(
                {"detalle": "No se puede desactivar una ubicación con mesas activas."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ubicacion.activo = False
        ubicacion.save()
        return Response({"detalle": "Ubicación desactivada."})


# ── Mesas ─────────────────────────────────────────────────────────────────────


class ListaMesaView(generics.ListCreateAPIView):
    """
    GET  /api/mesas/?ubicacion=<id>&estado=libre
    POST /api/mesas/
    """

    serializer_class = MesaSerializer

    def get_queryset(self):
        qs = Mesa.objects.select_related("ubicacion").filter(activo=True)
        ubicacion = self.request.query_params.get("ubicacion")
        estado = self.request.query_params.get("estado")
        if ubicacion:
            qs = qs.filter(ubicacion_id=ubicacion)
        if estado:
            qs = qs.filter(estado=estado)
        return qs

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), EsAdminOSupervisor()]

    def perform_create(self, serializer):
        mesa = serializer.save()
        registrar_accion(
            usuario=self.request.user,
            modulo="mesas",
            accion="crear",
            detalle=f"Mesa {mesa.numero} creada en {mesa.ubicacion.nombre}",
        )


class DetalleMesaView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Mesa.objects.select_related("ubicacion")
    serializer_class = MesaSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), EsAdminOSupervisor()]

    def destroy(self, request, *args, **kwargs):
        mesa = self.get_object()
        mesa.activo = False
        mesa.save()
        return Response({"detalle": "Mesa desactivada."})


# ── Acciones rápidas (operación en tiempo real) ───────────────────────────────


class CambiarEstadoMesaView(generics.UpdateAPIView):
    """
    PATCH /api/mesas/<id>/estado/
    Permite a mozos y cajeros cambiar el estado de una mesa rápidamente.
    """

    queryset = Mesa.objects.all()
    serializer_class = MesaEstadoSerializer
    permission_classes = [IsAuthenticated, EsEmpleado]
    http_method_names = ["patch"]


class ActualizarPosicionMesaView(generics.UpdateAPIView):
    """
    PATCH /api/mesas/<id>/posicion/
    Actualiza la posición visual de una mesa (drag & drop desde el frontend).
    """

    queryset = Mesa.objects.all()
    serializer_class = MesaPosicionSerializer
    permission_classes = [IsAuthenticated, EsAdminOSupervisor]
    http_method_names = ["patch"]


class MapaSalonView(APIView):
    """
    GET /api/mesas/mapa/
    Devuelve todas las ubicaciones activas con sus mesas activas agrupadas.
    Es el endpoint principal del panel de mesas del POS.
    """

    permission_classes = [IsAuthenticated, EsEmpleado]

    def get(self, request):
        ubicaciones = Ubicacion.objects.filter(activo=True).order_by("orden")
        resultado = []
        for ubicacion in ubicaciones:
            mesas = (
                Mesa.objects.filter(ubicacion=ubicacion, activo=True)
                .select_related("ubicacion")
                .order_by("numero")
            )
            resultado.append(
                {
                    "id": ubicacion.id,
                    "nombre": ubicacion.nombre,
                    "orden": ubicacion.orden,
                    "mesas": MesaSerializer(mesas, many=True).data,
                }
            )
        return Response(resultado)
