"""
Utilidades del módulo de mesas.
"""

from .models import EstadoMesa


def liberar_mesa_si_libre(mesa, excluir_comanda_pk=None):
    """
    Marca la mesa como LIBRE si no tiene comandas activas (abiertas o enviadas).
    Llama a save() solo si realmente cambia el estado.

    Usado en: CobrarComandaView, TransferirMesaView, CancelarComandaView.
    """
    if mesa is None:
        return

    from apps.comandas.models import Comanda, EstadoComanda

    qs = Comanda.objects.filter(
        mesa=mesa,
        estado__in=[EstadoComanda.ABIERTA, EstadoComanda.ENVIADA],
    )
    if excluir_comanda_pk:
        qs = qs.exclude(pk=excluir_comanda_pk)

    if not qs.exists():
        mesa.estado = EstadoMesa.LIBRE
        mesa.save(update_fields=["estado"])
