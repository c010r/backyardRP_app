from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.auditoria.utils import registrar_accion
from .models import Usuario
from .permissions import EsAdminOSupervisor
from .serializers import (
    CambiarContrasenaSerializer,
    PerfilSerializer,
    TokenPersonalizadoSerializer,
    UsuarioAdminSerializer,
)


class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login/
    Devuelve access + refresh token con datos básicos del usuario en el payload.
    Registra el inicio de sesión en auditoría.
    """

    serializer_class = TokenPersonalizadoSerializer

    def post(self, request, *args, **kwargs):
        respuesta = super().post(request, *args, **kwargs)
        if respuesta.status_code == 200:
            # Buscamos el usuario para registrar auditoría
            username = request.data.get("username", "")
            try:
                usuario = Usuario.objects.get(username=username)
                registrar_accion(
                    usuario=usuario,
                    modulo="usuarios",
                    accion="login",
                    detalle=f"Inicio de sesión desde {request.META.get('REMOTE_ADDR', '')}",
                )
            except Usuario.DoesNotExist:
                pass
        return respuesta


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Invalida el refresh token (blacklist). Registra el cierre en auditoría.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detalle": "Se requiere el refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            registrar_accion(
                usuario=request.user,
                modulo="usuarios",
                accion="logout",
                detalle="Cierre de sesión",
            )
            return Response({"detalle": "Sesión cerrada correctamente."})
        except Exception:
            return Response(
                {"detalle": "Token inválido o ya expirado."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class PerfilView(generics.RetrieveUpdateAPIView):
    """
    GET/PATCH /api/auth/perfil/
    El usuario autenticado consulta o actualiza su propio perfil.
    """

    serializer_class = PerfilSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class CambiarContrasenaView(APIView):
    """
    POST /api/auth/cambiar-contrasena/
    Permite cambiar la contraseña propia. Si es primer_ingreso, lo marca como False.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CambiarContrasenaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        usuario = request.user
        if not usuario.check_password(serializer.validated_data["contrasena_actual"]):
            return Response(
                {"contrasena_actual": "La contraseña actual es incorrecta."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        usuario.set_password(serializer.validated_data["contrasena_nueva"])
        if usuario.primer_ingreso:
            usuario.primer_ingreso = False
        usuario.save()

        registrar_accion(
            usuario=usuario,
            modulo="usuarios",
            accion="cambio_contrasena",
            detalle="El usuario cambió su contraseña.",
        )
        return Response({"detalle": "Contraseña actualizada correctamente."})


# ── Gestión de usuarios (solo admin/supervisor) ───────────────────────────────


class ListaUsuariosView(generics.ListCreateAPIView):
    """
    GET  /api/auth/usuarios/       → lista paginada
    POST /api/auth/usuarios/       → crear usuario
    """

    serializer_class = UsuarioAdminSerializer
    permission_classes = [IsAuthenticated, EsAdminOSupervisor]
    queryset = Usuario.objects.all().order_by("last_name", "first_name")


class DetalleUsuarioView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PATCH/DELETE /api/auth/usuarios/<id>/
    Nunca se elimina — se desactiva (activo=False).
    """

    serializer_class = UsuarioAdminSerializer
    permission_classes = [IsAuthenticated, EsAdminOSupervisor]
    queryset = Usuario.objects.all()

    def destroy(self, request, *args, **kwargs):
        usuario = self.get_object()
        usuario.activo = False
        usuario.save()
        registrar_accion(
            usuario=request.user,
            modulo="usuarios",
            accion="desactivar_usuario",
            detalle=f"Usuario desactivado: {usuario.username}",
        )
        return Response({"detalle": "Usuario desactivado."}, status=status.HTTP_200_OK)
