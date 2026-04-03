from rest_framework import filters, generics
from rest_framework.permissions import IsAuthenticated

from apps.usuarios.permissions import EsAdminOSupervisor, EsEmpleado
from .models import Cliente
from .serializers import ClienteListSerializer, ClienteSerializer


class ListaClienteView(generics.ListCreateAPIView):
    """
    GET  /api/clientes/?search=<q>
    POST /api/clientes/
    """

    permission_classes = [IsAuthenticated, EsEmpleado]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nombre", "apellido", "telefono", "email", "documento"]
    ordering_fields = ["apellido", "nombre", "creado_en"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ClienteSerializer
        return ClienteListSerializer

    def get_queryset(self):
        return Cliente.objects.filter(activo=True)


class DetalleClienteView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH /api/clientes/<id>/
    DELETE → desactiva (no elimina)
    """

    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def perform_destroy(self, instance):
        instance.activo = False
        instance.save(update_fields=["activo"])
