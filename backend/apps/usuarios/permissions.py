"""
Permisos por rol para usar en cualquier vista del sistema.

Uso:
    permission_classes = [EsAdministrador]
    permission_classes = [EsAdministrador | EsSupervisor]
"""

from rest_framework.permissions import BasePermission

from .models import Rol


class EsAdministrador(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.rol == Rol.ADMINISTRADOR
        )


class EsSupervisor(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.rol == Rol.SUPERVISOR
        )


class EsCajero(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.rol == Rol.CAJERO
        )


class EsMozo(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.rol == Rol.MOZO
        )


class EsCocina(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.rol == Rol.COCINA
        )


class EsCliente(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.rol == Rol.CLIENTE
        )


class EsEmpleado(BasePermission):
    """Cualquier rol interno (no cliente)."""

    ROLES_INTERNOS = {
        Rol.ADMINISTRADOR,
        Rol.SUPERVISOR,
        Rol.CAJERO,
        Rol.MOZO,
        Rol.COCINA,
    }

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.rol in self.ROLES_INTERNOS
        )


class EsAdminOSupervisor(BasePermission):
    """Admin o Supervisor — para gestión amplia."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.rol in (Rol.ADMINISTRADOR, Rol.SUPERVISOR)
        )
