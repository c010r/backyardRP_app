from django.urls import path
from . import views

urlpatterns = [
    # Públicos (sin auth)
    path("publica/", views.ReservaPublicaView.as_view(), name="reservas-publica"),
    path(
        "disponibilidad/",
        views.DisponibilidadView.as_view(),
        name="reservas-disponibilidad",
    ),
    # Panel interno
    path("", views.ListaReservaView.as_view(), name="reservas-lista"),
    path("<int:pk>/", views.DetalleReservaView.as_view(), name="reservas-detalle"),
    path(
        "<int:pk>/estado/",
        views.CambiarEstadoReservaView.as_view(),
        name="reservas-estado",
    ),
]
