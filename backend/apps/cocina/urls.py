from django.urls import path
from . import views

urlpatterns = [
    # Panel principal
    path("", views.PanelCocinaView.as_view(), name="cocina-panel"),
    # Actualizar estado por ítem
    path(
        "items/<int:item_id>/estado/",
        views.ActualizarEstadoItemView.as_view(),
        name="cocina-item-estado",
    ),
    # Marcar toda la comanda como lista
    path(
        "comandas/<int:pk>/lista/",
        views.MarcarComandaListaView.as_view(),
        name="cocina-comanda-lista",
    ),
]
