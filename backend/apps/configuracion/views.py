from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.usuarios.permissions import EsAdminOSupervisor
from .models import Empresa, HorarioNegocio
from .serializers import EmpresaSerializer, HorarioNegocioSerializer


class EmpresaView(APIView):
    """
    GET  /api/configuracion/empresa/  → lee la configuración
    PATCH /api/configuracion/empresa/ → actualiza (admin/supervisor)
    """

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), EsAdminOSupervisor()]

    def get(self, request):
        empresa = Empresa.objects.first()
        if not empresa:
            return Response(
                {"detalle": "No hay configuración de empresa cargada."}, status=404
            )
        return Response(EmpresaSerializer(empresa).data)

    def patch(self, request):
        empresa = Empresa.objects.first()
        if not empresa:
            return Response(
                {"detalle": "No hay configuración de empresa cargada."}, status=404
            )
        serializer = EmpresaSerializer(empresa, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ListaHorariosView(generics.ListCreateAPIView):
    """
    GET  /api/configuracion/horarios/
    POST /api/configuracion/horarios/
    """

    serializer_class = HorarioNegocioSerializer
    queryset = HorarioNegocio.objects.all()

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), EsAdminOSupervisor()]


class DetalleHorarioView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PATCH/DELETE /api/configuracion/horarios/<id>/
    """

    serializer_class = HorarioNegocioSerializer
    queryset = HorarioNegocio.objects.all()
    permission_classes = [IsAuthenticated, EsAdminOSupervisor]
