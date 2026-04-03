"""
Módulo de reportes.
No tiene modelos propios: agrega datos de los otros módulos con ORM.
Todos los endpoints son solo lectura y requieren admin/supervisor.

Parámetro común: ?desde=YYYY-MM-DD&hasta=YYYY-MM-DD
Si no se envían, por defecto aplica el día actual.
"""

import datetime
from decimal import Decimal

from django.db.models import Count, DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce, TruncDate
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cajas.models import (
    Caja,
    MedioPago,
    MovimientoCaja,
    PagoComanda,
    TipoMovimiento,
)
from apps.catalogo.models import Categoria, Producto
from apps.comandas.models import EstadoComanda, ItemComanda
from apps.mesas.models import Mesa
from apps.pedidos.models import EstadoPedido, Pedido
from apps.reservas.models import EstadoReserva, Reserva
from apps.usuarios.permissions import EsAdminOSupervisor


def _rango_fechas(request):
    hoy = datetime.date.today()
    desde_str = request.query_params.get("desde")
    hasta_str = request.query_params.get("hasta")
    try:
        desde = datetime.date.fromisoformat(desde_str) if desde_str else hoy
        hasta = datetime.date.fromisoformat(hasta_str) if hasta_str else hoy
    except ValueError:
        desde = hasta = hoy
    # Convertir a datetimes para filtrar con auto_now_add
    desde_dt = datetime.datetime.combine(desde, datetime.time.min)
    hasta_dt = datetime.datetime.combine(hasta, datetime.time.max)
    return desde_dt, hasta_dt, desde, hasta


class ResumenDiarioView(APIView):
    """
    GET /api/reportes/resumen/?desde=&hasta=
    Totales del período: ventas, comandas, propinas, pedidos.
    """

    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def get(self, request):
        desde, hasta, desde_d, hasta_d = _rango_fechas(request)

        pagos = PagoComanda.objects.filter(creado_en__range=(desde, hasta))
        total_ventas = pagos.aggregate(t=Coalesce(Sum("monto"), Value(Decimal("0"))))[
            "t"
        ]
        total_propinas = pagos.aggregate(
            t=Coalesce(Sum("propina"), Value(Decimal("0")))
        )["t"]

        comandas_cerradas = (
            ItemComanda.objects.filter(
                comanda__estado=EstadoComanda.CERRADA,
                comanda__cerrada_en__range=(desde, hasta),
            )
            .values("comanda")
            .distinct()
            .count()
        )

        pedidos_entregados = Pedido.objects.filter(
            estado=EstadoPedido.ENTREGADO,
            creado_en__range=(desde, hasta),
        ).count()

        total_pedidos_online = Pedido.objects.filter(
            estado__in=[EstadoPedido.ENTREGADO, EstadoPedido.LISTO],
            creado_en__range=(desde, hasta),
        ).aggregate(t=Coalesce(Sum("total"), Value(Decimal("0"))))["t"]

        return Response(
            {
                "periodo": {"desde": str(desde_d), "hasta": str(hasta_d)},
                "total_ventas_salon": total_ventas,
                "total_propinas": total_propinas,
                "total_ventas_online": total_pedidos_online,
                "total_ventas_general": total_ventas + total_pedidos_online,
                "comandas_cerradas": comandas_cerradas,
                "pedidos_entregados": pedidos_entregados,
            }
        )


class VentasPorDiaView(APIView):
    """
    GET /api/reportes/ventas-por-dia/?desde=&hasta=
    Total cobrado por día en el período.
    """

    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def get(self, request):
        desde, hasta, *_ = _rango_fechas(request)

        ventas = (
            PagoComanda.objects.filter(creado_en__range=(desde, hasta))
            .annotate(dia=TruncDate("creado_en"))
            .values("dia")
            .annotate(total=Sum("monto"), propinas=Sum("propina"))
            .order_by("dia")
        )
        return Response(list(ventas))


class VentasPorProductoView(APIView):
    """
    GET /api/reportes/ventas-por-producto/?desde=&hasta=
    Top de productos más vendidos en el período (cantidad y monto).
    """

    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def get(self, request):
        desde, hasta, *_ = _rango_fechas(request)

        items = (
            ItemComanda.objects.filter(
                comanda__estado=EstadoComanda.CERRADA,
                comanda__cerrada_en__range=(desde, hasta),
                cancelado=False,
                producto__isnull=False,
            )
            .values("producto__id", "producto__nombre", "producto__categoria__nombre")
            .annotate(
                cantidad_vendida=Sum("cantidad"),
                total_recaudado=Sum(F("cantidad") * F("precio_unitario")),
            )
            .order_by("-cantidad_vendida")
        )
        return Response(list(items))


class VentasPorCategoriaView(APIView):
    """
    GET /api/reportes/ventas-por-categoria/?desde=&hasta=
    """

    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def get(self, request):
        desde, hasta, *_ = _rango_fechas(request)

        items = (
            ItemComanda.objects.filter(
                comanda__estado=EstadoComanda.CERRADA,
                comanda__cerrada_en__range=(desde, hasta),
                cancelado=False,
                producto__isnull=False,
            )
            .values("producto__categoria__id", "producto__categoria__nombre")
            .annotate(
                cantidad_vendida=Sum("cantidad"),
                total_recaudado=Sum(F("cantidad") * F("precio_unitario")),
            )
            .order_by("-total_recaudado")
        )
        return Response(list(items))


class VentasPorMozoView(APIView):
    """
    GET /api/reportes/ventas-por-mozo/?desde=&hasta=
    """

    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def get(self, request):
        desde, hasta, *_ = _rango_fechas(request)

        data = (
            ItemComanda.objects.filter(
                comanda__estado=EstadoComanda.CERRADA,
                comanda__cerrada_en__range=(desde, hasta),
                cancelado=False,
                comanda__mozo__isnull=False,
            )
            .values(
                "comanda__mozo__id",
                "comanda__mozo__first_name",
                "comanda__mozo__last_name",
                "comanda__mozo__username",
            )
            .annotate(
                comandas=Count("comanda", distinct=True),
                total_vendido=Sum(F("cantidad") * F("precio_unitario")),
            )
            .order_by("-total_vendido")
        )
        return Response(list(data))


class MovimientosCajaView(APIView):
    """
    GET /api/reportes/movimientos-caja/?desde=&hasta=&cajero=<id>
    Movimientos e ingresos por caja en el período.
    """

    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def get(self, request):
        desde, hasta, *_ = _rango_fechas(request)
        cajero_id = request.query_params.get("cajero")

        cajas = Caja.objects.filter(creado_en__range=(desde, hasta)).select_related(
            "cajero"
        )
        if cajero_id:
            cajas = cajas.filter(cajero_id=cajero_id)

        ids_cajas = list(cajas.values_list("id", flat=True))

        # Saldo esperado por caja en una sola query (en lugar de N queries por caja)
        saldos_qs = (
            MovimientoCaja.objects.filter(caja_id__in=ids_cajas)
            .values("caja_id")
            .annotate(
                ingresos=Coalesce(
                    Sum("monto", filter=Q(tipo=TipoMovimiento.INGRESO)),
                    Decimal("0"),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
                egresos=Coalesce(
                    Sum("monto", filter=Q(tipo=TipoMovimiento.EGRESO)),
                    Decimal("0"),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
            )
        )
        saldos_map = {row["caja_id"]: row for row in saldos_qs}

        # Una sola query para todos los totales + detalle por medio, agrupado por caja
        pagos_por_caja = (
            PagoComanda.objects.filter(caja_id__in=ids_cajas)
            .values("caja_id", "medio_pago")
            .annotate(total=Sum("monto"), propinas=Sum("propina"))
            .order_by("caja_id", "medio_pago")
        )

        # Indexar por caja_id para acceso O(1)
        detalle_map: dict = {}
        totales_map: dict = {}
        for row in pagos_por_caja:
            cid = row["caja_id"]
            detalle_map.setdefault(cid, []).append(row)
            t = totales_map.setdefault(
                cid, {"total_cobrado": Decimal("0"), "total_propinas": Decimal("0")}
            )
            t["total_cobrado"] += row["total"] or Decimal("0")
            t["total_propinas"] += row["propinas"] or Decimal("0")

        resultado = []
        for caja in cajas:
            totales = totales_map.get(
                caja.id, {"total_cobrado": Decimal("0"), "total_propinas": Decimal("0")}
            )
            saldo_data = saldos_map.get(
                caja.id, {"ingresos": Decimal("0"), "egresos": Decimal("0")}
            )
            saldo_esperado = (
                caja.monto_inicial + saldo_data["ingresos"] - saldo_data["egresos"]
            )
            resultado.append(
                {
                    "caja_id": caja.id,
                    "cajero": caja.cajero.get_full_name() or caja.cajero.username,
                    "abierta": str(caja.creado_en),
                    "cerrada": str(caja.cerrada_en) if caja.cerrada_en else None,
                    "monto_inicial": caja.monto_inicial,
                    "total_cobrado": totales["total_cobrado"],
                    "total_propinas": totales["total_propinas"],
                    "saldo_esperado": saldo_esperado,
                    "monto_final_declarado": caja.monto_final_declarado,
                    "diferencia": (
                        caja.monto_final_declarado - saldo_esperado
                        if caja.monto_final_declarado is not None
                        else None
                    ),
                    "detalle_por_medio": detalle_map.get(caja.id, []),
                }
            )
        return Response(resultado)


class ReporteReservasView(APIView):
    """
    GET /api/reportes/reservas/?desde=&hasta=
    """

    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def get(self, request):
        desde, hasta, desde_d, hasta_d = _rango_fechas(request)

        reservas = Reserva.objects.filter(fecha__range=(desde_d, hasta_d))
        por_estado = list(
            reservas.values("estado").annotate(total=Count("id")).order_by("estado")
        )
        return Response(
            {
                "periodo": {"desde": str(desde_d), "hasta": str(hasta_d)},
                "total": reservas.count(),
                "por_estado": por_estado,
            }
        )


class ReportePedidosOnlineView(APIView):
    """
    GET /api/reportes/pedidos-online/?desde=&hasta=
    """

    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def get(self, request):
        desde, hasta, desde_d, hasta_d = _rango_fechas(request)

        pedidos = Pedido.objects.filter(creado_en__range=(desde, hasta))
        por_estado = list(
            pedidos.values("estado").annotate(total=Count("id")).order_by("estado")
        )
        por_tipo = list(
            pedidos.values("tipo").annotate(
                total=Count("id"),
                monto=Coalesce(Sum("total"), Value(Decimal("0"))),
            )
        )
        return Response(
            {
                "periodo": {"desde": str(desde_d), "hasta": str(hasta_d)},
                "total_pedidos": pedidos.count(),
                "por_estado": por_estado,
                "por_tipo": por_tipo,
            }
        )


# ─── Reportes de los nuevos módulos ──────────────────────────────────────────


class ReporteStockView(APIView):
    """
    GET /api/reportes/stock/
    Estado actual del inventario: stock, alertas de bajo stock, valor total.
    """

    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def get(self, request):
        from apps.inventario.models import MateriaPrima

        materias = MateriaPrima.objects.select_related("unidad").filter(activo=True)

        items = []
        total_valor = Decimal("0")
        bajo_stock_count = 0

        for mp in materias:
            valor = mp.stock_actual * mp.costo_unitario
            total_valor += valor
            bajo_stock = mp.stock_actual <= mp.stock_minimo
            if bajo_stock:
                bajo_stock_count += 1
            items.append(
                {
                    "id": mp.id,
                    "nombre": mp.nombre,
                    "unidad": mp.unidad.simbolo,
                    "stock_actual": mp.stock_actual,
                    "stock_minimo": mp.stock_minimo,
                    "bajo_stock": bajo_stock,
                    "costo_unitario": mp.costo_unitario,
                    "valor_stock": valor,
                }
            )

        items.sort(key=lambda x: x["bajo_stock"], reverse=True)
        return Response(
            {
                "total_items": len(items),
                "bajo_stock_count": bajo_stock_count,
                "valor_total_inventario": total_valor,
                "items": items,
            }
        )


class ReporteRentabilidadView(APIView):
    """
    GET /api/reportes/rentabilidad/?desde=&hasta=
    Margen bruto por producto: ingresos − costo de ventas.
    """

    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def get(self, request):
        desde, hasta, desde_d, hasta_d = _rango_fechas(request)

        items = (
            ItemComanda.objects.filter(
                comanda__estado=EstadoComanda.CERRADA,
                comanda__cerrada_en__range=(desde, hasta),
                cancelado=False,
                producto__isnull=False,
            )
            .values(
                "producto__id",
                "producto__nombre",
                "producto__precio_costo",
                "producto__precio_venta",
            )
            .annotate(
                cantidad_vendida=Sum("cantidad"),
                total_recaudado=Sum(F("cantidad") * F("precio_unitario")),
                costo_total=Sum(F("cantidad") * F("producto__precio_costo")),
            )
            .order_by("-total_recaudado")
        )

        resultado = []
        total_recaudado = Decimal("0")
        total_costo = Decimal("0")

        for item in items:
            recaudado = item["total_recaudado"] or Decimal("0")
            costo = item["costo_total"] or Decimal("0")
            ganancia = recaudado - costo
            margen = round(ganancia / recaudado * 100, 1) if recaudado else Decimal("0")
            total_recaudado += recaudado
            total_costo += costo
            resultado.append(
                {
                    "producto_id": item["producto__id"],
                    "nombre": item["producto__nombre"],
                    "precio_costo": item["producto__precio_costo"],
                    "precio_venta": item["producto__precio_venta"],
                    "cantidad_vendida": item["cantidad_vendida"],
                    "total_recaudado": recaudado,
                    "costo_total": costo,
                    "ganancia": ganancia,
                    "margen_pct": margen,
                }
            )

        ganancia_bruta = total_recaudado - total_costo
        return Response(
            {
                "periodo": {"desde": str(desde_d), "hasta": str(hasta_d)},
                "total_recaudado": total_recaudado,
                "total_costo": total_costo,
                "ganancia_bruta": ganancia_bruta,
                "margen_pct": (
                    round(ganancia_bruta / total_recaudado * 100, 1)
                    if total_recaudado
                    else 0
                ),
                "productos": resultado,
            }
        )


class ReporteClientesView(APIView):
    """
    GET /api/reportes/clientes/?desde=&hasta=
    Top 20 clientes registrados por gasto en pedidos online.
    """

    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def get(self, request):
        desde, hasta, desde_d, hasta_d = _rango_fechas(request)

        top = (
            Pedido.objects.filter(
                cliente__isnull=False,
                estado=EstadoPedido.ENTREGADO,
                creado_en__range=(desde, hasta),
            )
            .values(
                "cliente__id",
                "cliente__first_name",
                "cliente__last_name",
                "cliente__username",
            )
            .annotate(
                total_pedidos=Count("id"),
                total_gastado=Coalesce(Sum("total"), Value(Decimal("0"))),
            )
            .order_by("-total_gastado")[:20]
        )

        return Response(
            {
                "periodo": {"desde": str(desde_d), "hasta": str(hasta_d)},
                "top_clientes": list(top),
            }
        )


class ReporteEventosView(APIView):
    """
    GET /api/reportes/eventos/?desde=&hasta=
    Asistencia y recaudación por evento en el período.
    """

    permission_classes = [IsAuthenticated, EsAdminOSupervisor]

    def get(self, request):
        desde, hasta, desde_d, hasta_d = _rango_fechas(request)
        from apps.eventos.models import Entrada, EstadoEntrada, Evento

        eventos = Evento.objects.filter(fecha__range=(desde_d, hasta_d))
        ids_eventos = list(eventos.values_list("id", flat=True))

        entradas_qs = (
            Entrada.objects.filter(tipo_entrada__evento_id__in=ids_eventos)
            .values("tipo_entrada__evento_id", "estado")
            .annotate(
                total=Count("id"),
                recaudado=Coalesce(Sum("precio_pagado"), Value(Decimal("0"))),
            )
        )

        stats_map: dict = {}
        for row in entradas_qs:
            eid = row["tipo_entrada__evento_id"]
            s = stats_map.setdefault(
                eid,
                {
                    "total_entradas": 0,
                    "entradas_pagadas": 0,
                    "entradas_validadas": 0,
                    "total_recaudado": Decimal("0"),
                },
            )
            s["total_entradas"] += row["total"]
            if row["estado"] == EstadoEntrada.PAGADA:
                s["entradas_pagadas"] += row["total"]
                s["total_recaudado"] += row["recaudado"]
            elif row["estado"] == EstadoEntrada.VALIDADA:
                s["entradas_validadas"] += row["total"]
                s["total_recaudado"] += row["recaudado"]

        resultado = []
        for evento in eventos:
            s = stats_map.get(
                evento.id,
                {
                    "total_entradas": 0,
                    "entradas_pagadas": 0,
                    "entradas_validadas": 0,
                    "total_recaudado": Decimal("0"),
                },
            )
            resultado.append(
                {
                    "evento_id": evento.id,
                    "nombre": evento.nombre,
                    "fecha": str(evento.fecha),
                    "cupos_totales": evento.cupos_totales,
                    **s,
                }
            )

        return Response(
            {
                "periodo": {"desde": str(desde_d), "hasta": str(hasta_d)},
                "eventos": resultado,
            }
        )
