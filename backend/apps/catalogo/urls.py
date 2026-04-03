from django.urls import path
from . import views

urlpatterns = [
    # Menú público (sin auth)
    path(
        "menu-publico/", views.MenuPublicoView.as_view(), name="catalogo-menu-publico"
    ),
    # Categorías
    path("categorias/", views.ListaCategoriaView.as_view(), name="catalogo-categorias"),
    path(
        "categorias/<int:pk>/",
        views.DetalleCategoriaView.as_view(),
        name="catalogo-categoria-detalle",
    ),
    # Extras
    path("extras/", views.ListaExtraView.as_view(), name="catalogo-extras"),
    path(
        "extras/<int:pk>/",
        views.DetalleExtraView.as_view(),
        name="catalogo-extra-detalle",
    ),
    # Productos
    path("productos/", views.ListaProductoView.as_view(), name="catalogo-productos"),
    path(
        "productos/<int:pk>/",
        views.DetalleProductoView.as_view(),
        name="catalogo-producto-detalle",
    ),
    path(
        "productos/<int:producto_id>/variantes/",
        views.ListaVarianteView.as_view(),
        name="catalogo-variantes",
    ),
    path(
        "productos/<int:producto_id>/variantes/<int:pk>/",
        views.DetalleVarianteView.as_view(),
        name="catalogo-variante-detalle",
    ),
    path(
        "productos/<int:producto_id>/historial-precios/",
        views.HistorialPrecioView.as_view(),
        name="catalogo-historial-precios",
    ),
    # Combos
    path("combos/", views.ListaComboView.as_view(), name="catalogo-combos"),
    path(
        "combos/<int:pk>/",
        views.DetalleComboView.as_view(),
        name="catalogo-combo-detalle",
    ),
]
