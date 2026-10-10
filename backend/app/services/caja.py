from app.database import safe_commit
from decimal import Decimal

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models import (
    Categoria,
    Cierre,
    DetallePedido,
    MovimientoCaja,
    Pago,
    Pedido,
    Preparado,
    Producto,
    TipoCategoria,
    Vale,
)
from app.schemas.caja import CobroIn, PagoIn
from app.services.historial import registrar
from app.services.inventario import descontar_insumos_de_producto
from app.services.sync import encolar_sync


def _monto(valor: Decimal | None) -> Decimal:
    return (valor or Decimal("0")).quantize(Decimal("0.01"))


def pagos_validos(db: Session, pedido_id: int) -> list[Pago]:
    return (
        db.query(Pago)
        .filter(Pago.pedido_id == pedido_id, Pago.estado == "VALIDO")
        .order_by(Pago.id)
        .all()
    )


def total_cobrado(db: Session, pedido: Pedido) -> Decimal:
    return sum((_monto(p.monto) for p in pagos_validos(db, pedido.id)), Decimal("0"))


def liberar_mesa(db: Session, pedido: Pedido) -> None:
    if pedido.canal == "MESA" and pedido.mesa is not None:
        pedido.mesa.estado = "DISPONIBLE"


def cerrar_lineas_sin_cocina(db: Session, pedido: Pedido, usuario) -> None:
    """Deducción universal: da por entregadas las líneas del pedido y descuenta del inventario
    las que nunca fueron aceptadas por cocina (así ningún producto vendido queda sin descontar).
    Los preparados reutilizados no descuentan: su insumo ya se consumió."""
    for detalle in pedido.detalles:
        if detalle.estado != "CANCELADO" and detalle.preparado_en is None:
            es_prep = detalle.variacion_snapshot and (
                detalle.variacion_snapshot.get("es_preparado")
                or detalle.variacion_snapshot.get("preparado_id")
            )
            if not es_prep:
                nombre_prod = detalle.producto.nombre if detalle.producto else f"Item {detalle.producto_id}"
                descontar_insumos_de_producto(
                    db=db,
                    producto_id=detalle.producto_id,
                    cantidad=detalle.cantidad,
                    usuario_id=usuario.id,
                    pedido_id=pedido.id,
                    referencia_base=f"Cobro en Caja Pedido #{pedido.consecutivo} - {nombre_prod}",
                    es_llevar=bool(getattr(pedido, "tipo_consumo", "LOCAL") == "LLEVAR"),
                )
            detalle.preparado_en = func.now()
            detalle.listo_en = detalle.listo_en or func.now()
            detalle.entregado_en = detalle.entregado_en or func.now()
            detalle.estado = "ENTREGADO"
        elif detalle.estado in ("PREPARANDO", "LISTO"):
            detalle.listo_en = detalle.listo_en or func.now()
            detalle.entregado_en = detalle.entregado_en or func.now()
            detalle.estado = "ENTREGADO"


def cobrar_pedido(db: Session, pedido: Pedido, cobro: CobroIn, cajero) -> dict:
    """Registra los pagos de un pedido. Reglas del dueño:
    - Debe existir un turno de caja abierto con la base de efectivo inicial.
    - La suma de pagos debe cuadrar EXACTAMENTE con el total (`subtotal + iva`).
    - EFECTIVO guarda `recibido` y calcula `cambio`.
    - VALE crea un pagaré PENDIENTE con los datos del cliente.
    - DiDi tarjeta queda como por cobrar; DiDi efectivo entra a caja.
    - Cobro adelantado (mostrador): si la cocina no terminó, el pedido NO se
      saca de la cola; se marca `pagado_en` y pasará a PAGADO al finalizar.
    """
    if turno_abierto(db) is None:
        raise ValueError("No hay un turno de caja abierto. Debe abrir turno con la base de efectivo inicial antes de cobrar.")

    ref = f"pedido {pedido.consecutivo}"
    suma = sum((_monto(p.monto) for p in cobro.pagos), Decimal("0"))
    if suma != _monto(pedido.total):
        raise ValueError(
            f"Los pagos suman {suma} y el total del pedido es {_monto(pedido.total)}"
        )

    pagos: list[Pago] = []
    vales: list[Vale] = []

    for item in cobro.pagos:
        pago = _crear_pago(db, pedido, item, cajero)
        pagos.append(pago)
        if item.metodo == "VALE":
            vales.append(_crear_vale(db, pedido, item, cajero))

    # Cobro adelantado: si el pedido está en la cola de cocina, la caja NO toca sus líneas.
    # El ticket sigue visible para el cocinero, el inventario se descuenta cuando cocina
    # acepta y el pedido pasa a PAGADO al marcar LISTO la última línea (routers/cocina.py).
    en_cocina = pedido.estado in ("ENVIADO_A_COCINA", "EN_PREPARACION") and any(
        d.estado in ("ENVIADO", "PREPARANDO") for d in pedido.detalles
    )

    if not en_cocina:
        cerrar_lineas_sin_cocina(db, pedido, cajero)

    pedido.pagado_en = func.now()
    if en_cocina:
        pass  # conserva su estado de cocina; ya quedó marcado como pagado con pagado_en
    elif pedido.estado in ("FINALIZADO", "ENTREGADO"):
        pedido.estado = "PAGADO"
        liberar_mesa(db, pedido)
    elif pedido.canal in ("MOSTRADOR", "DOMICILIO", "DIDI"):
        pedido.estado = "PAGADO"
    elif pedido.canal == "MESA":
        todos_cerrados = all(d.estado in ("ENTREGADO", "CANCELADO") for d in pedido.detalles)
        if todos_cerrados:
            pedido.estado = "PAGADO"
            liberar_mesa(db, pedido)

    db.flush()
    registrar(
        db, cajero, "COBRAR_PEDIDO", "pedido", pedido.id,
        f"total={_monto(pedido.total)} metodos={','.join(p.metodo for p in pagos)}",
    )

    from app.services.sync import encolar_sync

    for pago in pagos:
        encolar_sync(
            db,
            tipo="COBRO_PEDIDO",
            entidad="pago",
            payload={
                "id": pago.id,
                "pedido_id": pedido.id,
                "consecutivo": pedido.consecutivo,
                "metodo": pago.metodo,
                "monto": float(pago.monto),
                "recibido": float(pago.recibido) if pago.recibido else None,
                "cambio": float(pago.cambio) if pago.cambio else None,
                "didi_orden_id": pago.didi_orden_id,
            },
            entidad_id=pago.id,
            dispositivo_id=f"CAJA_{cajero.id}",
        )
    for vale in vales:
        encolar_sync(
            db,
            tipo="VALE_CREADO",
            entidad="vale",
            payload={
                "id": vale.id,
                "pedido_id": pedido.id,
                "cliente_nombre": vale.cliente_nombre,
                "monto": float(vale.monto),
            },
            entidad_id=vale.id,
            dispositivo_id=f"CAJA_{cajero.id}",
        )

    safe_commit(db)
    for pago in pagos:
        db.refresh(pago)
    for vale in vales:
        db.refresh(vale)
    db.refresh(pedido)
    return {"pedido": pedido, "pagos": pagos, "vales": vales}


def _crear_pago(db: Session, pedido: Pedido, item: PagoIn, cajero) -> Pago:
    monto = _monto(item.monto)
    if monto <= Decimal("0"):
        raise ValueError("El monto de cada pago debe ser estrictamente mayor a cero")
    recibido = cambio = None
    didi_orden = item.didi_orden_id

    if item.metodo == "EFECTIVO":
        if item.recibido is None:
            raise ValueError("Pago en EFECTIVO requiere el campo 'recibido'")
        recibido = _monto(item.recibido)
        if recibido < monto:
            raise ValueError("El efectivo recibido es menor al monto del pago")
        cambio = recibido - monto
    elif item.metodo in ("DIDI_TARJETA", "DIDI_EFECTIVO"):
        didi_orden = didi_orden or pedido.didi_orden_id
        if not didi_orden:
            raise ValueError(f"Pago {item.metodo} requiere didi_orden_id")
    elif item.metodo == "VALE":
        if not item.vale_cliente_nombre:
            raise ValueError("Pago con VALE requiere vale_cliente_nombre")

    pago = Pago(
        pedido_id=pedido.id,
        metodo=item.metodo,
        monto=monto,
        recibido=recibido,
        cambio=cambio,
        didi_orden_id=didi_orden,
        usuario_id=cajero.id,
    )
    db.add(pago)
    return pago


def _crear_vale(db: Session, pedido: Pedido, item: PagoIn, cajero) -> Vale:
    vale = Vale(
        pedido_id=pedido.id,
        cliente_nombre=item.vale_cliente_nombre,
        cliente_cedula=item.vale_cliente_cedula,
        cliente_telefono=item.vale_cliente_telefono,
        monto=_monto(item.monto),
    )
    db.add(vale)
    return vale


def anular_vales_pendientes(db: Session, pedido_id: int, monto: Decimal | None = None) -> int:
    """Anula los pagarés PENDIENTES de un pedido (devolución o cancelación) para que no quede
    una deuda viva por una venta que ya no existe. Con `monto` anula solo el vale de ese pago."""
    q = db.query(Vale).filter(Vale.pedido_id == pedido_id, Vale.estado == "PENDIENTE").order_by(Vale.id)
    vales = q.all()
    if monto is not None:
        coincidente = next((v for v in vales if _monto(v.monto) == monto), None)
        vales = [coincidente] if coincidente else vales[:1]
    for v in vales:
        v.estado = "ANULADO"
    return len(vales)


def efectivo_esperado(pagos: list[Pago], entradas: Decimal, salidas: Decimal) -> Decimal:
    """Efectivo que debe haber en la gaveta.

    Cuenta TODO el efectivo que entró por ventas, incluso el de pagos luego devueltos, porque
    cada devolución en efectivo ya resta como movimiento SALIDA. Si además se excluyera el pago
    devuelto, la misma plata se restaría dos veces y el arqueo saldría descuadrado.
    """
    ingresado = sum(
        (_monto(p.monto) for p in pagos if p.metodo in ("EFECTIVO", "DIDI_EFECTIVO")), Decimal("0")
    )
    return ingresado + entradas - salidas


def cobrar_vale(db: Session, vale: Vale, cajero, descripcion: str | None = None) -> None:
    """El cliente paga su pagaré: queda COBRADO y entra el dinero a caja."""
    if turno_abierto(db) is None:
        raise ValueError("No hay un turno de caja abierto. Debe abrir turno con la base antes de cobrar vales.")
    if vale.estado != "PENDIENTE":
        raise ValueError("El vale ya fue cobrado o cancelado")
    vale.estado = "COBRADO"
    vale.cobrado_por = cajero.id
    vale.cobrado_en = func.now()
    db.add(
        MovimientoCaja(
            usuario_id=cajero.id,
            tipo="ENTRADA",
            categoria="COBRO_VALE",
            concepto=f"Cobro vale #{vale.id} - {vale.cliente_nombre}",
            descripcion=descripcion or f"Cobro del vale #{vale.id}",
            valor=_monto(vale.monto),
            pedido_id=vale.pedido_id,
            vale_id=vale.id,
        )
    )
    registrar(
        db, cajero, "COBRAR_VALE", "vale", vale.id,
        f"{vale.cliente_nombre} monto={_monto(vale.monto)}",
    )

    from app.services.sync import encolar_sync

    encolar_sync(
        db,
        tipo="VALE_COBRADO",
        entidad="vale",
        payload={
            "id": vale.id,
            "pedido_id": vale.pedido_id,
            "cliente_nombre": vale.cliente_nombre,
            "monto": float(vale.monto),
            "cobrado_en": str(vale.cobrado_en),
        },
        entidad_id=vale.id,
        dispositivo_id=f"CAJA_{cajero.id}",
    )
    safe_commit(db)
    db.refresh(vale)


def devolver_pago(db: Session, pago: Pago, motivo: str, usuario) -> Pago:
    """Devuelve un pago en caja. Registra la salida de dinero y recalcula si el
    pedido sigue cubierto; si no, vuelve a quedar por pagar."""
    if pago.estado != "VALIDO":
        raise ValueError("El pago ya fue devuelto")
    if turno_abierto(db) is None:
        raise ValueError("No hay un turno de caja abierto para registrar la devolución")
    pedido = pago.pedido
    pago.estado = "DEVUELTO"
    pago.devuelto_por = usuario.id
    pago.devuelto_en = func.now()
    pago.motivo_devolucion = motivo

    # Solo generar salida física de dinero del cajón si el cliente pagó en efectivo
    if pago.metodo in ("EFECTIVO", "DIDI_EFECTIVO"):
        db.add(
            MovimientoCaja(
                usuario_id=usuario.id,
                tipo="SALIDA",
                categoria="DEVOLUCION",
                concepto=f"Devolución pago #{pago.id} ({pago.metodo}) - pedido {pedido.consecutivo}",
                descripcion=motivo,
                valor=_monto(pago.monto),
                pedido_id=pedido.id,
            )
        )
    elif pago.metodo == "VALE":
        anular_vales_pendientes(db, pedido.id, monto=_monto(pago.monto))
    db.flush()
    if total_cobrado(db, pedido) < _monto(pedido.total):
        pedido.pagado_en = None
        if pedido.estado == "PAGADO":
            pedido.estado = "FINALIZADO"
    registrar(
        db, usuario, "DEVOLVER_PAGO", "pago", pago.id,
        f"pedido={pedido.consecutivo} monto={_monto(pago.monto)} motivo={motivo}",
    )

    encolar_sync(
        db,
        tipo="DEVOLUCION_PAGO",
        entidad="pago",
        payload={
            "pago_id": pago.id,
            "pedido_id": pedido.id,
            "monto": float(pago.monto),
            "motivo": motivo,
        },
        entidad_id=pago.id,
        dispositivo_id=f"CAJA_{usuario.id}",
    )
    safe_commit(db)
    db.refresh(pago)
    return pago


# ============================================================
# TURNO DE CAJA (apertura / cierre / fotograma inmutable)
# ============================================================

def turno_abierto(db: Session) -> Cierre | None:
    return (
        db.query(Cierre)
        .filter(Cierre.cerrado_en.is_(None))
        .order_by(Cierre.id.desc())
        .first()
    )


def obtener_turno_actual_con_metricas(db: Session) -> Cierre | None:
    cierre = turno_abierto(db)
    if not cierre:
        return None

    # Métricas en vivo del turno en curso (sin cerrar en base de datos)
    pagos_turno = (
        db.query(Pago)
        .filter(
            or_(Pago.cierre_id == cierre.id, Pago.cierre_id.is_(None)),
            Pago.pagado_en >= cierre.abierto_en,
        )
        .all()
    )
    pagos = [p for p in pagos_turno if p.estado == "VALIDO"]
    movimientos = (
        db.query(MovimientoCaja)
        .filter(
            or_(MovimientoCaja.cierre_id == cierre.id, MovimientoCaja.cierre_id.is_(None)),
            MovimientoCaja.creado_en >= cierre.abierto_en,
        )
        .all()
    )

    por_metodo: dict[str, Decimal] = {}
    for p in pagos:
        por_metodo[p.metodo] = por_metodo.get(p.metodo, Decimal("0")) + _monto(p.monto)

    cierre.total_pedidos = len({p.pedido_id for p in pagos})
    cierre.total_efectivo = por_metodo.get("EFECTIVO", Decimal("0"))
    cierre.total_tarjeta = por_metodo.get("TARJETA", Decimal("0"))
    cierre.total_transferencia = por_metodo.get("TRANSFERENCIA", Decimal("0"))
    cierre.total_vale = por_metodo.get("VALE", Decimal("0"))
    cierre.total_didi_tarjeta = por_metodo.get("DIDI_TARJETA", Decimal("0"))
    cierre.total_didi_efectivo = por_metodo.get("DIDI_EFECTIVO", Decimal("0"))
    cierre.total_ventas = sum((_monto(p.monto) for p in pagos), Decimal("0"))
    cierre.total_entradas_caja = sum((_monto(m.valor) for m in movimientos if m.tipo == "ENTRADA"), Decimal("0"))
    cierre.total_salidas_caja = sum((_monto(m.valor) for m in movimientos if m.tipo == "SALIDA"), Decimal("0"))
    cierre.total_efectivo_final = efectivo_esperado(
        pagos_turno, cierre.total_entradas_caja, cierre.total_salidas_caja
    )
    return cierre


def abrir_turno(db: Session, usuario, monto_inicial: Decimal = Decimal("0")) -> Cierre:
    if turno_abierto(db) is not None:
        raise ValueError("Ya hay un turno de caja abierto")

    cierre = Cierre(usuario_id=usuario.id, abierto_en=func.now())
    db.add(cierre)
    db.flush()
    registrar(db, usuario, "ABRIR_TURNO", "cierre", cierre.id, f"fondo={_monto(monto_inicial)}")

    from app.services.sync import encolar_sync

    encolar_sync(
        db,
        tipo="ABRIR_TURNO",
        entidad="cierre",
        payload={
            "id": cierre.id,
            "usuario_id": usuario.id,
            "fondo_inicial": float(monto_inicial),
            "abierto_en": str(cierre.abierto_en),
        },
        entidad_id=cierre.id,
        dispositivo_id=f"CAJA_{usuario.id}",
    )

    if _monto(monto_inicial) > 0:
        db.add(
            MovimientoCaja(
                usuario_id=usuario.id,
                tipo="ENTRADA",
                categoria="CAMBIO_INICIAL",
                concepto="Fondo inicial de caja",
                descripcion="Monto inicial con el que abre el turno",
                valor=_monto(monto_inicial),
                cierre_id=cierre.id,
            )
        )

    safe_commit(db)
    db.refresh(cierre)
    return cierre


def registrar_movimiento(db: Session, usuario, data) -> MovimientoCaja:
    """Entrada/egreso manual de caja (solo admin). La descripción es obligatoria."""
    abierto = turno_abierto(db)
    if not abierto:
        raise ValueError("No hay un turno de caja abierto. Debe abrir turno con la base antes de registrar movimientos.")
    if _monto(data.valor) <= Decimal("0"):
        raise ValueError("El valor del movimiento debe ser mayor a cero")
    mov = MovimientoCaja(
        usuario_id=usuario.id,
        tipo=data.tipo,
        categoria=data.categoria,
        concepto=data.concepto or f"{data.tipo} de caja",
        descripcion=data.descripcion,
        valor=_monto(data.valor),
        cierre_id=abierto.id,
    )
    db.add(mov)
    db.flush()
    registrar(
        db, usuario, "MOVIMIENTO_CAJA", "movimiento_caja", mov.id,
        f"{data.tipo} {data.categoria} valor={_monto(data.valor)}: {data.descripcion}",
    )

    encolar_sync(
        db,
        tipo="MOVIMIENTO_CAJA",
        entidad="movimiento_caja",
        payload={
            "id": mov.id,
            "tipo": mov.tipo,
            "categoria": mov.categoria,
            "concepto": mov.concepto,
            "descripcion": mov.descripcion,
            "valor": float(mov.valor),
            "cierre_id": mov.cierre_id,
        },
        entidad_id=mov.id,
        dispositivo_id=f"CAJA_{usuario.id}",
    )
    safe_commit(db)
    db.refresh(mov)
    return mov


def _total_por_tipo(db: Session, pedido_ids: set[int]) -> dict[str, Decimal]:
    """Venta de comida vs bebida según el tipo de categoría de cada producto."""
    result = {"COMIDA": Decimal("0"), "BEBIDA": Decimal("0"), "OTRO": Decimal("0")}
    if not pedido_ids:
        return result
    filas = (
        db.query(
            TipoCategoria.nombre,
            func.coalesce(func.sum(DetallePedido.precio_unitario * DetallePedido.cantidad), 0),
        )
        .select_from(DetallePedido)
        .join(Producto, DetallePedido.producto_id == Producto.id)
        .join(Categoria, Producto.categoria_id == Categoria.id)
        .join(TipoCategoria, Categoria.tipo_id == TipoCategoria.id)
        .filter(DetallePedido.pedido_id.in_(pedido_ids))
        .group_by(TipoCategoria.nombre)
        .all()
    )
    for nombre, total in filas:
        result[nombre] = _monto(Decimal(str(total)))
    return result


def cerrar_turno(db: Session, cierre: Cierre, usuario, notas: str | None = None) -> Cierre:
    """Genera el fotograma inmutable del turno.

    Barre todos los pagos y movimientos de caja que todavía no pertenecen a un
    cierre (los 'suelta' asignándoles este cierre_id) y consolida los totales.
    """
    if cierre.cerrado_en is not None:
        raise ValueError("El turno ya está cerrado")

    pagos = (
        db.query(Pago)
        .filter(
            or_(Pago.cierre_id == cierre.id, Pago.cierre_id.is_(None)),
            Pago.pagado_en >= cierre.abierto_en,
        )
        .all()
    )
    movimientos = (
        db.query(MovimientoCaja)
        .filter(
            or_(MovimientoCaja.cierre_id == cierre.id, MovimientoCaja.cierre_id.is_(None)),
            MovimientoCaja.creado_en >= cierre.abierto_en,
        )
        .all()
    )

    validos = [p for p in pagos if p.estado == "VALIDO"]
    devueltos = [p for p in pagos if p.estado == "DEVUELTO"]

    por_metodo: dict[str, Decimal] = {}
    for p in validos:
        por_metodo[p.metodo] = por_metodo.get(p.metodo, Decimal("0")) + _monto(p.monto)

    pedido_ids = {p.pedido_id for p in validos}
    venta_tipo = _total_por_tipo(db, pedido_ids)

    vales_turno = (
        [v for v in db.query(Vale).filter(Vale.pedido_id.in_(pedido_ids)).all()]
        if pedido_ids
        else []
    )
    vales_pendientes = db.query(Vale).filter(Vale.estado == "PENDIENTE").all()

    entradas = sum((_monto(m.valor) for m in movimientos if m.tipo == "ENTRADA"), Decimal("0"))
    salidas = sum((_monto(m.valor) for m in movimientos if m.tipo == "SALIDA"), Decimal("0"))
    total_devoluciones = sum((_monto(p.monto) for p in devueltos), Decimal("0"))
    egresos_no_devolucion = [
        m for m in movimientos if m.tipo == "SALIDA" and m.categoria != "DEVOLUCION"
    ]

    total_efectivo = por_metodo.get("EFECTIVO", Decimal("0"))
    total_didi_efectivo = por_metodo.get("DIDI_EFECTIVO", Decimal("0"))
    total_ventas = sum((_monto(p.monto) for p in validos), Decimal("0"))

    cierre.total_pedidos = len(pedido_ids)
    cierre.total_venta_comida = venta_tipo.get("COMIDA", Decimal("0"))
    cierre.total_venta_bebida = venta_tipo.get("BEBIDA", Decimal("0"))
    cierre.total_efectivo = total_efectivo
    cierre.total_tarjeta = por_metodo.get("TARJETA", Decimal("0"))
    cierre.total_transferencia = por_metodo.get("TRANSFERENCIA", Decimal("0"))
    cierre.total_vale = por_metodo.get("VALE", Decimal("0"))
    cierre.cantidad_vales = len(vales_turno)
    cierre.total_didi_tarjeta = por_metodo.get("DIDI_TARJETA", Decimal("0"))
    cierre.total_didi_efectivo = total_didi_efectivo
    cierre.total_entradas_caja = entradas
    cierre.total_salidas_caja = salidas
    cierre.cantidad_egresos = len(egresos_no_devolucion)
    cierre.total_devoluciones = total_devoluciones
    # Contabilizar preparados durante el turno (entre abierto_en y ahora)
    reutilizados = (
        db.query(func.count(Preparado.id))
        .filter(
            Preparado.estado == "ASIGNADO",
            Preparado.asignado_en >= cierre.abierto_en,
        )
        .scalar()
        or 0
    )
    descartados = (
        db.query(func.count(Preparado.id))
        .filter(
            Preparado.estado == "DESCARTADO",
            Preparado.descartado_en >= cierre.abierto_en,
        )
        .scalar()
        or 0
    )
    cierre.preparados_reutilizados = int(reutilizados)
    cierre.preparados_descartados = int(descartados)
    cierre.total_ventas = total_ventas
    cierre.total_efectivo_final = efectivo_esperado(pagos, entradas, salidas)
    cierre.total_por_cobrar = (
        por_metodo.get("DIDI_TARJETA", Decimal("0"))
        + sum((_monto(v.monto) for v in vales_pendientes), Decimal("0"))
    )
    cierre.notas = notas
    cierre.cerrado_en = func.now()

    for p in pagos:
        p.cierre_id = cierre.id
    for m in movimientos:
        m.cierre_id = cierre.id

    # CIERRE GLOBAL DE JORNADAS LABORALES
    from app.models.asistencia import TurnoLaboral
    from app.services.websocket import ws_manager
    import asyncio
    
    turnos_abiertos = db.query(TurnoLaboral).filter(TurnoLaboral.salida_en.is_(None)).all()
    for t in turnos_abiertos:
        t.salida_en = func.now()
        t.motivo_cierre = "CIERRE_CAJA"

    # Lanzar notificación asíncrona de cierre general (ignora si falla el loop)
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(ws_manager.broadcast({
            "evento": "cierre_caja_general",
            "data": {"mensaje": "Día laboral finalizado. Se ha realizado el cierre de caja del restaurante."}
        }))
    except RuntimeError:
        pass  # Si no hay loop no lanzamos websocket en este instante

    registrar(
        db, usuario, "CERRAR_TURNO", "cierre", cierre.id,
        f"ventas={cierre.total_ventas} efectivo_final={cierre.total_efectivo_final}",
    )

    encolar_sync(
        db,
        tipo="CIERRE_TURNO",
        entidad="cierre",
        payload={
            "id": cierre.id,
            "usuario_id": cierre.usuario_id,
            "abierto_en": str(cierre.abierto_en),
            "cerrado_en": str(cierre.cerrado_en),
            "total_pedidos": cierre.total_pedidos,
            "total_ventas": float(cierre.total_ventas),
            "total_efectivo": float(cierre.total_efectivo),
            "total_tarjeta": float(cierre.total_tarjeta),
            "total_transferencia": float(cierre.total_transferencia),
            "total_vale": float(cierre.total_vale),
            "total_didi_tarjeta": float(cierre.total_didi_tarjeta),
            "total_didi_efectivo": float(cierre.total_didi_efectivo),
            "total_entradas_caja": float(cierre.total_entradas_caja),
            "total_salidas_caja": float(cierre.total_salidas_caja),
            "total_efectivo_final": float(cierre.total_efectivo_final),
            "total_por_cobrar": float(cierre.total_por_cobrar),
            "notas": cierre.notas,
        },
        entidad_id=cierre.id,
        dispositivo_id=f"CAJA_{usuario.id}",
    )
    safe_commit(db)
    db.refresh(cierre)
    return cierre
