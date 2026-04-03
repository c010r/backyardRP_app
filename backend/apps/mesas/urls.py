from django.urls import path
from . import views

urlpatterns = [
    # Mapa operativo del salón
    path("mapa/", views.MapaSalonView.as_view(), name="mesas-mapa"),
    # Ubicaciones
    path("ubicaciones/", views.ListaUbicacionView.as_view(), name="mesas-ubicaciones"),
    path(
        "ubicaciones/<int:pk>/",
        views.DetalleUbicacionView.as_view(),
        name="mesas-ubicacion-detalle",
    ),
    # Mesas
    path("", views.ListaMesaView.as_view(), name="mesas-lista"),
    path("<int:pk>/", views.DetalleMesaView.as_view(), name="mesas-detalle"),
    path(
        "<int:pk>/estado/", views.CambiarEstadoMesaView.as_view(), name="mesas-estado"
    ),
    path(
        "<int:pk>/posicion/",
        views.ActualizarPosicionMesaView.as_view(),
        name="mesas-posicion",
    ),
]
