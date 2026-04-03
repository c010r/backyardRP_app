"""
URLs raíz del proyecto. Cada app registra sus propias rutas.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    # Autenticación JWT
    path("api/auth/", include("apps.usuarios.urls")),

    # Módulos internos
    path("api/configuracion/", include("apps.configuracion.urls")),
    path("api/auditoria/", include("apps.auditoria.urls")),
    path("api/catalogo/", include("apps.catalogo.urls")),
    path("api/mesas/", include("apps.mesas.urls")),
    path("api/comandas/", include("apps.comandas.urls")),
    path("api/cajas/", include("apps.cajas.urls")),
    path("api/cocina/", include("apps.cocina.urls")),
    path("api/reservas/", include("apps.reservas.urls")),
    path("api/pedidos/", include("apps.pedidos.urls")),
    path("api/reportes/", include("apps.reportes.urls")),
    path("api/clientes/", include("apps.clientes.urls")),
    path("api/empleados/", include("apps.empleados.urls")),
    path("api/inventario/", include("apps.inventario.urls")),
    path("api/eventos/", include("apps.eventos.urls")),
    path("api/facturacion/", include("apps.facturacion.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
