"""
Validaciones de disponibilidad para reservas.
Centralizado aquí para reutilizar desde serializers y vistas.
"""

import datetime

from rest_framework.exceptions import ValidationError

from apps.configuracion.models import HorarioNegocio, DiaSemana

# Mapeo entre Python weekday() y nuestros choices
_DIAS = {
    0: DiaSemana.LUNES,
    1: DiaSemana.MARTES,
    2: DiaSemana.MIERCOLES,
    3: DiaSemana.JUEVES,
    4: DiaSemana.VIERNES,
    5: DiaSemana.SABADO,
    6: DiaSemana.DOMINGO,
}


def validar_horario_reserva(fecha: datetime.date, hora: datetime.time):
    """
    Verifica que fecha+hora caigan dentro del horario de apertura del negocio.
    Considera el caso donde el cierre es al día siguiente.
    Lanza ValidationError si no es válido.
    """
    dia_semana = _DIAS.get(fecha.weekday())
    try:
        horario = HorarioNegocio.objects.get(dia=dia_semana, activo=True)
    except HorarioNegocio.DoesNotExist:
        raise ValidationError(
            {
                "hora": f"El negocio no abre los {dia_semana}. Revisá los horarios disponibles."
            }
        )

    apertura = horario.apertura
    cierre = horario.cierre

    if horario.cierre_siguiente_dia:
        # El negocio cierra pasada la medianoche
        # La hora de reserva es válida si está entre apertura y medianoche,
        # o entre medianoche y cierre
        if not (hora >= apertura or hora <= cierre):
            raise ValidationError(
                {
                    "hora": f"El horario de reservas ese día es de {apertura:%H:%M} a {cierre:%H:%M} (siguiente día)."
                }
            )
    else:
        if not (apertura <= hora <= cierre):
            raise ValidationError(
                {
                    "hora": f"El horario de reservas ese día es de {apertura:%H:%M} a {cierre:%H:%M}."
                }
            )
