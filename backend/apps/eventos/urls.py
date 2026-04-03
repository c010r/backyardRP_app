from django.urls import path
from .views import (
    CambiarEstadoEntradaView,
    ComprarEntradaView,
    DetalleEventoAdminView,
    DetalleEventoPublicoView,
    ListaEntradasView,
    ListaEventoAdminView,
    ListaEventoPublicoView,
    ListaTipoEntradaView,
    ValidarEntradaView,
)

urlpatterns = [
    # Públicos (AllowAny)
    path("publicos/", ListaEventoPublicoView.as_view()),
    path("publicos/<int:pk>/", DetalleEventoPublicoView.as_view()),
    path("comprar/", ComprarEntradaView.as_view()),
    path("validar/", ValidarEntradaView.as_view()),
    # Panel interno
    path("", ListaEventoAdminView.as_view()),
    path("<int:pk>/", DetalleEventoAdminView.as_view()),
    path("<int:evento_id>/tipos/", ListaTipoEntradaView.as_view()),
    path("<int:evento_id>/entradas/", ListaEntradasView.as_view()),
    path("entradas/<int:pk>/estado/", CambiarEstadoEntradaView.as_view()),
]
