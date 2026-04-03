"""
Modelo de usuario central del sistema.

Decisión de diseño: se extiende AbstractUser en lugar de usar un perfil
separado. Todos los endpoints del POS necesitan acceder a rol, estado y
datos del empleado en cada request — un solo modelo evita JOINs innecesarios
y simplifica la autenticación JWT.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class Rol(models.TextChoices):
    ADMINISTRADOR = "administrador", "Administrador"
    SUPERVISOR = "supervisor", "Supervisor"
    CAJERO = "cajero", "Cajero"
    MOZO = "mozo", "Mozo"
    COCINA = "cocina", "Cocina"
    CLIENTE = "cliente", "Cliente"


class Usuario(AbstractUser):
    """
    Usuario del sistema. Unifica empleados internos y clientes registrados.
    El campo 'rol' determina qué puede ver y hacer cada usuario.
    """

    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.CLIENTE,
        verbose_name="Rol",
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Desactivar en lugar de eliminar usuarios.",
    )
    primer_ingreso = models.BooleanField(
        default=True,
        verbose_name="Primer ingreso",
        help_text="Si es True, el sistema obliga a cambiar la contraseña al iniciar sesión.",
    )
    telefono = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Teléfono",
    )
    avatar = models.ImageField(
        upload_to="usuarios/avatares/",
        null=True,
        blank=True,
        verbose_name="Avatar",
    )
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")
    actualizado_en = models.DateTimeField(auto_now=True, verbose_name="Actualizado en")

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        nombre = self.get_full_name() or self.username
        return f"{nombre} ({self.get_rol_display()})"

    @property
    def es_empleado(self):
        return self.rol in (
            Rol.ADMINISTRADOR,
            Rol.SUPERVISOR,
            Rol.CAJERO,
            Rol.MOZO,
            Rol.COCINA,
        )

    @property
    def es_admin(self):
        return self.rol == Rol.ADMINISTRADOR
