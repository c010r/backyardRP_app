from django.urls import path
from . import views

urlpatterns = [
    # Caja del usuario actual
    path("mi-caja/", views.MiCajaView.as_view(), name="cajas-mi-caja"),
    path("abrir/", views.AbrirCajaView.as_view(), name="cajas-abrir"),
    path("cobrar/", views.CobrarComandaView.as_view(), name="cajas-cobrar"),
    # Historial (admin/supervisor)
    path("", views.ListaCajaView.as_view(), name="cajas-lista"),
    path("<int:pk>/", views.DetalleCajaView.as_view(), name="cajas-detalle"),
    path("<int:pk>/cerrar/", views.CerrarCajaView.as_view(), name="cajas-cerrar"),
    path(
        "<int:caja_id>/movimientos/",
        views.MovimientosView.as_view(),
        name="cajas-movimientos",
    ),
]
