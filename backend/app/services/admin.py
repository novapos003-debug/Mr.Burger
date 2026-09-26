from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.tiempo import fecha_local
from app.models import (
    Categoria,
    Compra,
    DetalleCompra,
    DetallePedido,
    HistorialAccion,
    Ingrediente,
    MovimientoCaja,
    MovimientoInventario,
    Pago,
    Pedido,
    Preparado,
    Producto,
    Proveedor,
    TipoCategoria,
    Usuario,
    Vale,
)
from app.schemas.admin import (
    AlertaStockItem,
    CompraIn,
    CompraOut,
    DashboardOut,
    DesgloseDiaItem,
    DetalleCompraOut,
    HistorialAccionOut,
    ReporteVentasOut,
    TopProductoItem,
)
from app.services.caja import _monto
from app.services.historial import registrar


def obtener_dashboard(db: Session, fecha: date | None = None) -> DashboardOut:
    """Consolida todas las métricas en tiempo real para el panel del dueño (iPad/Web)."""
    dia = fecha or fecha_local()

    # 1. Pedidos del día
    pedidos_dia = (
        db.query(Pedido)
        .options(
            joinedload(Pedido.detalles).joinedload(DetallePedido.producto).joinedload(Producto.categoria).joinedload(Categoria.tipo),
            joinedload(Pedido.pagos),
        )
        .filter(Pedido.fecha_dia == dia)
        .all()
    )

    pedidos_por_estado: dict[str, int] = {}
    ventas_por_canal: dict[str, Decimal] = {"MESA": Decimal("0"), "MOSTRADOR": Decimal("0"), "DIDI": Decimal("0"), "DOMICILIO": Decimal("0")}
    ventas_por_tipo: dict[str, Decimal] = {"COMIDA": Decimal("0"), "BEBIDA": Decimal("0")}
    total_ventas = Decimal("0")
    pedidos_pagados_count = 0

    for p in pedidos_dia:
        pedidos_por_estado[p.estado] = pedidos_por_estado.get(p.estado, 0) + 1
        # Ventas efectivas: pedidos cobrados o cerrados
        if p.estado in ("PAGADO", "CERRADO") or p.pagado_en is not None:
            total_ventas += _monto(p.total)
            pedidos_pagados_count += 1
            ventas_por_canal[p.canal] = ventas_por_canal.get(p.canal, Decimal("0")) + _monto(p.total)
            for d in p.detalles:
                if d.estado != "CANCELADO" and d.producto and d.producto.categoria and d.producto.categoria.tipo:
                    tipo_nombre = d.producto.categoria.tipo.nombre
                    ventas_por_tipo[tipo_nombre] = ventas_por_tipo.get(tipo_nombre, Decimal("0")) + _monto(d.cantidad * d.precio_unitario)

    ticket_promedio = (total_ventas / pedidos_pagados_count).quantize(Decimal("0.01")) if pedidos_pagados_count > 0 else Decimal("0")

    # 2. Métodos de pago del día
    pedido_ids = [p.id for p in pedidos_dia]
    pagos_por_metodo: dict[str, Decimal] = {
        "EFECTIVO": Decimal("0"),
        "TARJETA": Decimal("0"),
        "TRANSFERENCIA": Decimal("0"),
        "VALE": Decimal("0"),
        "DIDI_TARJETA": Decimal("0"),
        "DIDI_EFECTIVO": Decimal("0"),
    }
    if pedido_ids:
        pagos = db.query(Pago).filter(Pago.pedido_id.in_(pedido_ids), Pago.estado == "VALIDO").all()
        for pg in pagos:
            pagos_por_metodo[pg.metodo] = pagos_por_metodo.get(pg.metodo, Decimal("0")) + _monto(pg.monto)

    # 3. Flujo de caja del día
    movs = db.query(MovimientoCaja).filter(func.date(MovimientoCaja.creado_en) == dia).all()
    entradas_caja = sum((_monto(m.valor) for m in movs if m.tipo == "ENTRADA"), Decimal("0"))
    salidas_caja = sum((_monto(m.valor) for m in movs if m.tipo == "SALIDA"), Decimal("0"))
    devoluciones_caja = sum((_monto(m.valor) for m in movs if m.tipo == "SALIDA" and m.categoria == "DEVOLUCION"), Decimal("0"))

    # 4. Vales pendientes
    vales_pend = db.query(Vale).filter(Vale.estado == "PENDIENTE").all()
    vales_pend_monto = sum((_monto(v.monto) for v in vales_pend), Decimal("0"))
    vales_pend_cant = len(vales_pend)

    # 5. Preparados disponibles
    preparados_count = db.query(func.count(Preparado.id)).filter(Preparado.estado == "DISPONIBLE").scalar() or 0

    # 6. Top productos del día
    top_prods_filas = (
        db.query(
            DetallePedido.producto_id,
            Producto.nombre,
            func.sum(DetallePedido.cantidad).label("cantidad_total"),
            func.sum(DetallePedido.cantidad * DetallePedido.precio_unitario).label("monto_total"),
        )
        .join(Producto, DetallePedido.producto_id == Producto.id)
        .join(Pedido, DetallePedido.pedido_id == Pedido.id)
        .filter(Pedido.fecha_dia == dia, Pedido.estado.in_(["PAGADO", "CERRADO"]), DetallePedido.estado != "CANCELADO")
        .group_by(DetallePedido.producto_id, Producto.nombre)
        .order_by(func.sum(DetallePedido.cantidad).desc())
        .limit(6)
        .all()
    )
    top_productos = [
        TopProductoItem(
            producto_id=fila[0],
            nombre=fila[1],
            cantidad=Decimal(str(fila[2] or 0)),
            total=_monto(Decimal(str(fila[3] or 0))),
        )
        for fila in top_prods_filas
    ]

    # 7. Alertas de stock
    alertas_stock = obtener_stock_critico(db)

    return DashboardOut(
        fecha=dia,
        total_ventas=total_ventas,
        total_pedidos=len(pedidos_dia),
        ticket_promedio=ticket_promedio,
        pedidos_por_estado=pedidos_por_estado,
        ventas_por_canal=ventas_por_canal,
        ventas_por_tipo=ventas_por_tipo,
        pagos_por_metodo=pagos_por_metodo,
        entradas_caja=entradas_caja,
        salidas_caja=salidas_caja,
        devoluciones_caja=devoluciones_caja,
        vales_pendientes_monto=vales_pend_monto,
        vales_pendientes_cantidad=vales_pend_cant,
        preparados_disponibles_count=int(preparados_count),
        top_productos=top_productos,
        alertas_stock=alertas_stock,
    )


def obtener_stock_critico(db: Session) -> list[AlertaStockItem]:
    """Obtiene insumos cuyo stock está en o por debajo del mínimo."""
    ings = (
        db.query(Ingrediente)
        .options(joinedload(Ingrediente.proveedor))
        .filter(Ingrediente.activo.is_(True), Ingrediente.stock_actual <= Ingrediente.stock_minimo)
        .order_by(Ingrediente.stock_actual.asc())
        .all()
    )
    resultado = []
    for i in ings:
        deficit = max(Decimal("0"), _monto(i.stock_minimo - i.stock_actual))
        costo_reab = (deficit * _monto(i.costo_unitario)).quantize(Decimal("0.01"))
        resultado.append(
            AlertaStockItem(
                ingrediente_id=i.id,
                nombre=i.nombre,
                unidad_base=i.unidad_base,
                stock_actual=_monto(i.stock_actual),
                stock_minimo=_monto(i.stock_minimo),
                deficit=deficit,
                costo_unitario=_monto(i.costo_unitario),
                costo_reabastecer=costo_reab,
                proveedor_nombre=i.proveedor.nombre if i.proveedor else None,
            )
        )
    return resultado


def reporte_ventas(
    db: Session,
    desde: date,
    hasta: date,
    canal: str | None = None,
) -> ReporteVentasOut:
    """Reporte histórico agrupado por fecha y canal para el admin."""
    q = db.query(Pedido).filter(Pedido.fecha_dia >= desde, Pedido.fecha_dia <= hasta, Pedido.estado.in_(["PAGADO", "CERRADO"]))
    if canal:
        q = q.filter(Pedido.canal == canal)
    pedidos = q.order_by(Pedido.fecha_dia.asc()).all()

    por_dia: dict[date, dict] = {}
    ventas_canal: dict[str, Decimal] = {"MESA": Decimal("0"), "MOSTRADOR": Decimal("0"), "DIDI": Decimal("0"), "DOMICILIO": Decimal("0")}
    total_ventas = Decimal("0")

    for p in pedidos:
        sub = _monto(p.subtotal)
        iva = _monto(p.iva)
        tot = _monto(p.total)
        total_ventas += tot
        ventas_canal[p.canal] = ventas_canal.get(p.canal, Decimal("0")) + tot

        if p.fecha_dia not in por_dia:
            por_dia[p.fecha_dia] = {"pedidos_count": 0, "subtotal": Decimal("0"), "iva": Decimal("0"), "total": Decimal("0")}
        por_dia[p.fecha_dia]["pedidos_count"] += 1
        por_dia[p.fecha_dia]["subtotal"] += sub
        por_dia[p.fecha_dia]["iva"] += iva
        por_dia[p.fecha_dia]["total"] += tot

    desglose = [
        DesgloseDiaItem(
            fecha=f,
            pedidos_count=datos["pedidos_count"],
            subtotal=datos["subtotal"],
            iva=datos["iva"],
            total=datos["total"],
        )
        for f, datos in sorted(por_dia.items())
    ]

    ticket_promedio = (total_ventas / len(pedidos)).quantize(Decimal("0.01")) if pedidos else Decimal("0")

    return ReporteVentasOut(
        desde=desde,
        hasta=hasta,
        total_ventas=total_ventas,
        total_pedidos=len(pedidos),
        ticket_promedio=ticket_promedio,
        ventas_por_canal=ventas_canal,
        desglose_diario=desglose,
    )


def registrar_compra(db: Session, data: CompraIn, admin: Usuario) -> Compra:
    """Registra una compra de insumos a proveedor, incrementando stock y ajustando costo."""
    if data.proveedor_id is not None:
        prov = db.get(Proveedor, data.proveedor_id)
        if not prov:
            raise ValueError(f"Proveedor con ID {data.proveedor_id} no existe")

    compra = Compra(
        proveedor_id=data.proveedor_id,
        usuario_id=admin.id,
        descripcion=data.descripcion,
    )
    db.add(compra)
    db.flush()

    costo_total_compra = Decimal("0")
    for det in data.detalles:
        ing = db.get(Ingrediente, det.ingrediente_id)
        if not ing or not ing.activo:
            raise ValueError(f"Ingrediente {det.ingrediente_id} no existe o inactivo")

        costo_linea = (det.cantidad * det.costo_unitario).quantize(Decimal("0.0001"))
        costo_total_compra += costo_linea

        # Actualizar stock del ingrediente
        ing.stock_actual = (ing.stock_actual or Decimal("0")) + det.cantidad
        if det.costo_unitario > 0:
            ing.costo_unitario = det.costo_unitario

        detalle_db = DetalleCompra(
            compra_id=compra.id,
            ingrediente_id=ing.id,
            cantidad=det.cantidad,
            costo_unitario=det.costo_unitario,
            costo_total=costo_linea,
        )
        db.add(detalle_db)
        db.flush()

        # Registrar movimiento de inventario positivo (COMPRA)
        db.add(
            MovimientoInventario(
                ingrediente_id=ing.id,
                compra_id=compra.id,
                usuario_id=admin.id,
                cantidad=det.cantidad,
                tipo="COMPRA",
                referencia=f"Compra #{compra.id} - {ing.nombre}",
            )
        )

    registrar(
        db,
        admin,
        "REGISTRAR_COMPRA",
        "compra",
        compra.id,
        f"proveedor_id={compra.proveedor_id} total={costo_total_compra}",
    )

    db.commit()
    db.refresh(compra)
    return compra


def listar_compras(db: Session, limit: int = 50, offset: int = 0) -> list[CompraOut]:
    """Lista las compras registradas con proveedores y totales."""
    compras = (
        db.query(Compra)
        .options(
            joinedload(Compra.proveedor),
            joinedload(Compra.usuario),
            joinedload(Compra.detalles).joinedload(DetalleCompra.ingrediente),
        )
        .order_by(Compra.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    resultado = []
    for c in compras:
        total_compra = sum((_monto(d.costo_total) for d in c.detalles), Decimal("0"))
        detalles_out = [
            DetalleCompraOut(
                id=d.id,
                ingrediente_id=d.ingrediente_id,
                ingrediente_nombre=d.ingrediente.nombre if d.ingrediente else None,
                cantidad=d.cantidad,
                costo_unitario=d.costo_unitario,
                costo_total=d.costo_total,
            )
            for d in c.detalles
        ]
        resultado.append(
            CompraOut(
                id=c.id,
                proveedor_id=c.proveedor_id,
                proveedor_nombre=c.proveedor.nombre if c.proveedor else None,
                usuario_id=c.usuario_id,
                usuario_nombre=c.usuario.nombre if c.usuario else None,
                descripcion=c.descripcion,
                costo_total=total_compra,
                creado_en=c.creado_en,
                detalles=detalles_out,
            )
        )
    return resultado


def consultar_auditoria(
    db: Session,
    usuario_id: int | None = None,
    accion: str | None = None,
    entidad: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[HistorialAccionOut]:
    """Consulta la bitácora inmutable de auditoría."""
    q = db.query(HistorialAccion).options(joinedload(HistorialAccion.usuario)).order_by(HistorialAccion.id.desc())
    if usuario_id is not None:
        q = q.filter(HistorialAccion.usuario_id == usuario_id)
    if accion:
        q = q.filter(HistorialAccion.accion == accion)
    if entidad:
        q = q.filter(HistorialAccion.entidad == entidad)

    acciones = q.offset(offset).limit(limit).all()
    return [
        HistorialAccionOut(
            id=a.id,
            usuario_id=a.usuario_id,
            usuario_nombre=a.usuario.nombre if a.usuario else None,
            accion=a.accion,
            entidad=a.entidad,
            entidad_id=a.entidad_id,
            detalle=a.detalle,
            creado_en=a.creado_en,
        )
        for a in acciones
    ]
