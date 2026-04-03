from django.urls import path
from . import views

urlpatterns = [
    # Comandas
    path("", views.ListaComandaView.as_view(), name="comandas-lista"),
    path("<int:pk>/", views.DetalleComandaView.as_view(), name="comandas-detalle"),
    # Ítems
    path(
        "<int:comanda_id>/items/",
        views.AgregarItemView.as_view(),
        name="comandas-agregar-item",
    ),
    path(
        "<int:comanda_id>/items/<int:item_id>/cancelar/",
        views.CancelarItemView.as_view(),
        name="comandas-cancelar-item",
    ),
    # Acciones
    path(
        "<int:pk>/enviar-cocina/",
        views.EnviarCocinaView.as_view(),
        name="comandas-enviar-cocina",
    ),
    path(
        "<int:pk>/transferir-mesa/",
        views.TransferirMesaView.as_view(),
        name="comandas-transferir-mesa",
    ),
    path(
        "<int:pk>/cancelar/",
        views.CancelarComandaView.as_view(),
        name="comandas-cancelar",
    ),
]
