"""
Función central para registrar acciones en auditoría.
Todas las apps del sistema deben llamar a esta función en lugar de
crear RegistroAuditoria directamente.

Uso:
    from apps.auditoria.utils import registrar_accion

    registrar_accion(
        usuario=request.user,
        modulo="caja",
        accion="apertura_caja",
        detalle=f"Caja #{caja.id} abierta con ${monto_inicial}",
        request=request,   # opcional — captura la IP
    )
"""

import logging

from .models import RegistroAuditoria

logger = logging.getLogger(__name__)


def registrar_accion(
    usuario, modulo: str, accion: str, detalle: str = "", request=None
):
    """
    Registra una acción en la bitácora de auditoría.
    Nunca lanza excepciones para no interrumpir el flujo de negocio.
    """
    ip = None
    if request:
        ip = _obtener_ip(request)

    try:
        RegistroAuditoria.objects.create(
            usuario=usuario,
            modulo=modulo,
            accion=accion,
            detalle=detalle,
            ip=ip,
        )
    except Exception as exc:
        # Auditoria nunca debe romper el sistema
        logger.error("Error al registrar auditoría: %s", exc)


def _obtener_ip(request) -> str:
    """Extrae la IP real considerando proxies."""
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")
