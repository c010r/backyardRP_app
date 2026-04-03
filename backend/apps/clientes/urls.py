from django.urls import path
from .views import DetalleClienteView, ListaClienteView

urlpatterns = [
    path("", ListaClienteView.as_view()),
    path("<int:pk>/", DetalleClienteView.as_view()),
]
