from django.urls import path
from . import views

urlpatterns = [
    path("empresa/", views.EmpresaView.as_view(), name="configuracion-empresa"),
    path("horarios/", views.ListaHorariosView.as_view(), name="configuracion-horarios"),
    path(
        "horarios/<int:pk>/",
        views.DetalleHorarioView.as_view(),
        name="configuracion-horario-detalle",
    ),
]
