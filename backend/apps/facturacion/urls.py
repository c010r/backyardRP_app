from django.urls import path
from .views import DetalleComprobanteView, EmitirComprobanteView, ListaComprobanteView

urlpatterns = [
    path("", ListaComprobanteView.as_view()),
    path("<int:pk>/", DetalleComprobanteView.as_view()),
    path("emitir/", EmitirComprobanteView.as_view()),
]
