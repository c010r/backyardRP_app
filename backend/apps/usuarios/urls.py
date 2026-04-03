from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    # Autenticación
    path("login/", views.LoginView.as_view(), name="auth-login"),
    path("logout/", views.LogoutView.as_view(), name="auth-logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
    # Perfil propio
    path("perfil/", views.PerfilView.as_view(), name="auth-perfil"),
    path(
        "cambiar-contrasena/",
        views.CambiarContrasenaView.as_view(),
        name="auth-cambiar-contrasena",
    ),
    # Gestión de usuarios (admin/supervisor)
    path("usuarios/", views.ListaUsuariosView.as_view(), name="usuarios-lista"),
    path(
        "usuarios/<int:pk>/",
        views.DetalleUsuarioView.as_view(),
        name="usuarios-detalle",
    ),
]
