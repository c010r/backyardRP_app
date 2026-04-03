from django.urls import path
from .views import (
    AgregarItemOrdenView,
    AjusteStockView,
    CambiarEstadoOrdenView,
    DetalleMateriaPrimaView,
    DetalleOrdenCompraView,
    DetalleProveedorView,
    DetalleRecetaView,
    ListaMateriaPrimaView,
    ListaMovimientoStockView,
    ListaOrdenCompraView,
    ListaProveedorView,
    ListaRecetaView,
    ListaUnidadMedidaView,
)

urlpatterns = [
    path("unidades/", ListaUnidadMedidaView.as_view()),
    path("materias-primas/", ListaMateriaPrimaView.as_view()),
    path("materias-primas/<int:pk>/", DetalleMateriaPrimaView.as_view()),
    path("ajuste/", AjusteStockView.as_view()),
    path("movimientos/", ListaMovimientoStockView.as_view()),
    path("recetas/", ListaRecetaView.as_view()),
    path("recetas/<int:pk>/", DetalleRecetaView.as_view()),
    path("proveedores/", ListaProveedorView.as_view()),
    path("proveedores/<int:pk>/", DetalleProveedorView.as_view()),
    path("ordenes/", ListaOrdenCompraView.as_view()),
    path("ordenes/<int:pk>/", DetalleOrdenCompraView.as_view()),
    path("ordenes/<int:pk>/estado/", CambiarEstadoOrdenView.as_view()),
    path("ordenes/<int:pk>/items/", AgregarItemOrdenView.as_view()),
]
