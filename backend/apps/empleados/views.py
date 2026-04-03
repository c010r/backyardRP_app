from rest_framework import filters, generics
from rest_framework.permissions import IsAuthenticated

from apps.usuarios.permissions import EsAdminOSupervisor
from .models import Empleado
from .serializers import EmpleadoListSerializer, EmpleadoSerializer


class ListaEmpleadoView(generics.ListCreateAPIView):
    """
    GET  /api/empleados/
    POST /api/empleados/  → el usuario referenciado debe existir previamente
    """

    permission_classes = [IsAuthenticated, EsAdminOSupervisor]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "usuario__first_name",
        "usuario__last_name",
        "usuario__username",
        "documento",
    ]
    ordering_fields = ["usuario__last_name", "fecha_ingreso"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return EmpleadoSerializer
        return EmpleadoListSerializer

    def get_queryset(self):
        return Empleado.objects.select_related("usuario").filter(usuario__activo=True)


class DetalleEmpleadoView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH /api/empleados/<id>/
    DELETE → desactiva el usuario asociado
    """

    queryset = Empleado.objects.select_related("usuario")
    serializer_class = EmpleadoSerializer
    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def perform_destroy(self, instance):
        instance.usuario.activo = False
        instance.usuario.save(update_fields=["activo"])
