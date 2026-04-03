"""
Módulo de caja: apertura, movimientos, cobros y cierre.

Decisiones de diseño:
- Una Caja pertenece a un cajero. Solo puede haber una caja abierta por cajero.
- MovimientoCaja cubre ingresos/egresos manuales y cobros de comandas.
- PagoComanda registra cuánto se cobró de cada comanda y con qué medio.
  Una comanda puede pagarse con múltiples medios (dividida: parte efectivo, parte QR).
- La propina se registra en PagoComanda para vincularla al cobro exacto.
- El arqueo de cierre se guarda en CierreCaja con el detalle por medio de pago.
"""

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Sum

from apps.common.models import ModeloBase


class MedioPago(models.TextChoices):
    EFECTIVO = "efectivo", "Efectivo"
    DEBITO = "debito", "Débito"
    CREDITO = "credito", "Crédito"
    TRANSFERENCIA = "transferencia", "Transferencia"
    QR = "qr", "QR"
    MERCADO_PAGO = "mercado_pago", "Mercado Pago"


class TipoMovimiento(models.TextChoices):
    INGRESO = "ingreso", "Ingreso"
    EGRESO = "egreso", "Egreso"


class Caja(ModeloBase):
    cajero = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cajas",
        verbose_name="Cajero",
    )
    abierta = models.BooleanField(default=True, verbose_name="Abierta")
    monto_inicial = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="Monto inicial"
    )
    monto_final_declarado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Monto final declarado",
    )
    observaciones_apertura = models.TextField(
        blank=True, verbose_name="Observaciones de apertura"
    )
    cerrada_en = models.DateTimeField(null=True, blank=True, verbose_name="Cerrada en")

    class Meta:
        verbose_name = "Caja"
        verbose_name_plural = "Cajas"
        ordering = ["-creado_en"]

    def __str__(self):
        estado = "Abierta" if self.abierta else "Cerrada"
        return f"Caja de {self.cajero.get_full_name() or self.cajero.username} [{estado}] — {self.creado_en:%d/%m/%Y}"

    @property
    def total_ingresos(self):
        resultado = self.movimientos.filter(tipo=TipoMovimiento.INGRESO).aggregate(
            total=Sum("monto")
        )
        return resultado["total"] or Decimal("0")

    @property
    def total_egresos(self):
        resultado = self.movimientos.filter(tipo=TipoMovimiento.EGRESO).aggregate(
            total=Sum("monto")
        )
        return resultado["total"] or Decimal("0")

    @property
    def saldo_esperado(self):
        # Una sola query con Sum condicional en lugar de dos queries separadas
        from django.db.models import Case, When, DecimalField as DDF

        resultado = self.movimientos.aggregate(
            ingresos=Sum(
                Case(
                    When(tipo=TipoMovimiento.INGRESO, then="monto"),
                    default=Decimal("0"),
                    output_field=DDF(max_digits=12, decimal_places=2),
                )
            ),
            egresos=Sum(
                Case(
                    When(tipo=TipoMovimiento.EGRESO, then="monto"),
                    default=Decimal("0"),
                    output_field=DDF(max_digits=12, decimal_places=2),
                )
            ),
        )
        ingresos = resultado["ingresos"] or Decimal("0")
        egresos = resultado["egresos"] or Decimal("0")
        return self.monto_inicial + ingresos - egresos


class MovimientoCaja(ModeloBase):
    """Ingreso o egreso manual (fondo de caja, gastos, etc.)."""

    caja = models.ForeignKey(
        Caja, on_delete=models.PROTECT, related_name="movimientos", verbose_name="Caja"
    )
    tipo = models.CharField(
        max_length=8, choices=TipoMovimiento.choices, verbose_name="Tipo"
    )
    medio_pago = models.CharField(
        max_length=15,
        choices=MedioPago.choices,
        default=MedioPago.EFECTIVO,
        verbose_name="Medio de pago",
    )
    monto = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto")
    descripcion = models.CharField(
        max_length=200, blank=True, verbose_name="Descripción"
    )
    recibo = models.ImageField(
        upload_to="cajas/recibos/",
        null=True,
        blank=True,
        verbose_name="Recibo (imagen)",
    )
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name="Registrado por",
    )

    class Meta:
        verbose_name = "Movimiento de caja"
        verbose_name_plural = "Movimientos de caja"
        ordering = ["-creado_en"]

    def __str__(self):
        return f"{self.get_tipo_display()} ${self.monto} — Caja {self.caja_id}"


class PagoComanda(ModeloBase):
    """
    Registro de cobro de una comanda. Puede haber múltiples registros
    por comanda si se pagó con más de un medio.
    """

    caja = models.ForeignKey(
        Caja, on_delete=models.PROTECT, related_name="pagos", verbose_name="Caja"
    )
    comanda = models.ForeignKey(
        "comandas.Comanda",
        on_delete=models.PROTECT,
        related_name="pagos",
        verbose_name="Comanda",
    )
    medio_pago = models.CharField(
        max_length=15, choices=MedioPago.choices, verbose_name="Medio de pago"
    )
    monto = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto")
    propina = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Propina"
    )
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name="Registrado por",
    )

    class Meta:
        verbose_name = "Pago de comanda"
        verbose_name_plural = "Pagos de comandas"
        ordering = ["-creado_en"]

    def __str__(self):
        return f"Pago ${self.monto} ({self.get_medio_pago_display()}) — Comanda #{self.comanda.numero}"


class CierreCaja(models.Model):
    """
    Detalle del arqueo al cerrar caja: resumen por medio de pago.
    Se genera una instancia por cada medio de pago al cierre.
    """

    caja = models.ForeignKey(
        Caja, on_delete=models.CASCADE, related_name="detalles_cierre"
    )
    medio_pago = models.CharField(max_length=15, choices=MedioPago.choices)
    total_cobrado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_propinas = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Detalle de cierre de caja"
        unique_together = ("caja", "medio_pago")
