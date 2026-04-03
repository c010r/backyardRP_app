from django.urls import path
from . import views

urlpatterns = [
    path("", views.ListaAuditoriaView.as_view(), name="auditoria-lista"),
]
