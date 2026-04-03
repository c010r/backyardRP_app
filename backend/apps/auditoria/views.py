from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.usuarios.permissions import EsAdminOSupervisor
from .models import RegistroAuditoria
from .serializers import RegistroAuditoriaSerializer


class ListaAuditoriaView(generics.ListAPIView):
    """
    GET /api/auditoria/
    Solo accesible para administradores y supervisores.
    Soporta filtro por módulo y usuario vía query params:
        ?modulo=caja
        ?usuario=3
    """

    serializer_class = RegistroAuditoriaSerializer
    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def get_queryset(self):
        qs = RegistroAuditoria.objects.select_related("usuario").all()
        modulo = self.request.query_params.get("modulo")
        usuario_id = self.request.query_params.get("usuario")
        if modulo:
            qs = qs.filter(modulo=modulo)
        if usuario_id:
            qs = qs.filter(usuario_id=usuario_id)
        return qs
