"""
Registro de auditoría. Cada acción relevante del sistema queda guardada aquí.
Se usa la función `registrar_accion` desde utils.py para no acoplar la lógica
de negocio a este modelo directamente.
"""

from django.conf import settings
from django.db import models


class RegistroAuditoria(models.Model):

    class TipoAccion(models.TextChoices):
        LOGIN = "login", "Inicio de sesión"
        LOGOUT = "logout", "Cierre de sesión"
        CREAR = "crear", "Creación"
        EDITAR = "editar", "Edición"
        ELIMINAR = "eliminar", "Eliminación"
        DESACTIVAR = "desactivar_usuario", "Desactivar usuario"
        CAMBIO_CONTRASENA = "cambio_contrasena", "Cambio de contraseña"
        COBRO = "cobro", "Cobro"
        APERTURA_CAJA = "apertura_caja", "Apertura de caja"
        CIERRE_CAJA = "cierre_caja", "Cierre de caja"
        ENVIO_COCINA = "envio_cocina", "Envío a cocina"
        OTRO = "otro", "Otro"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registros_auditoria",
        verbose_name="Usuario",
    )
    modulo = models.CharField(max_length=50, verbose_name="Módulo")
    accion = models.CharField(
        max_length=30,
        choices=TipoAccion.choices,
        default=TipoAccion.OTRO,
        verbose_name="Acción",
    )
    detalle = models.TextField(blank=True, verbose_name="Detalle")
    ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y hora")

    class Meta:
        verbose_name = "Registro de auditoría"
        verbose_name_plural = "Registros de auditoría"
        ordering = ["-fecha"]

    def __str__(self):
        usuario_str = self.usuario.username if self.usuario else "sistema"
        return f"[{self.fecha:%d/%m/%Y %H:%M}] {usuario_str} — {self.get_accion_display()} en {self.modulo}"
