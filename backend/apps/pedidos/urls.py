from django.urls import path
from . import views

urlpatterns = [
    # Públicos (sin auth)
    path("nuevo/", views.PedidoPublicoView.as_view(), name="pedidos-nuevo"),
    path(
        "seguimiento/<int:numero>/",
        views.SeguimientoPedidoView.as_view(),
        name="pedidos-seguimiento",
    ),
    # Panel interno
    path("", views.ListaPedidoView.as_view(), name="pedidos-lista"),
    path("<int:pk>/", views.DetallePedidoView.as_view(), name="pedidos-detalle"),
    path(
        "<int:pk>/estado/",
        views.CambiarEstadoPedidoView.as_view(),
        name="pedidos-estado",
    ),
    path("<int:pk>/pagado/", views.MarcarPagadoView.as_view(), name="pedidos-pagado"),
]
