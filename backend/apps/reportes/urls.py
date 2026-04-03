from django.urls import path
from . import views

urlpatterns = [
    path("resumen/", views.ResumenDiarioView.as_view(), name="reportes-resumen"),
    path(
        "ventas-por-dia/", views.VentasPorDiaView.as_view(), name="reportes-ventas-dia"
    ),
    path(
        "ventas-por-producto/",
        views.VentasPorProductoView.as_view(),
        name="reportes-ventas-producto",
    ),
    path(
        "ventas-por-categoria/",
        views.VentasPorCategoriaView.as_view(),
        name="reportes-ventas-categoria",
    ),
    path(
        "ventas-por-mozo/",
        views.VentasPorMozoView.as_view(),
        name="reportes-ventas-mozo",
    ),
    path(
        "movimientos-caja/", views.MovimientosCajaView.as_view(), name="reportes-caja"
    ),
    path("reservas/", views.ReporteReservasView.as_view(), name="reportes-reservas"),
    path(
        "pedidos-online/",
        views.ReportePedidosOnlineView.as_view(),
        name="reportes-pedidos-online",
    ),
    path("stock/", views.ReporteStockView.as_view(), name="reportes-stock"),
    path(
        "rentabilidad/",
        views.ReporteRentabilidadView.as_view(),
        name="reportes-rentabilidad",
    ),
    path("clientes/", views.ReporteClientesView.as_view(), name="reportes-clientes"),
    path("eventos/", views.ReporteEventosView.as_view(), name="reportes-eventos"),
]
