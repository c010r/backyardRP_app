from django.urls import path
from .views import DetalleEmpleadoView, ListaEmpleadoView

urlpatterns = [
    path("", ListaEmpleadoView.as_view()),
    path("<int:pk>/", DetalleEmpleadoView.as_view()),
]
