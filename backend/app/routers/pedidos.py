from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.deps import admin_required, cashier_required, staff_required
from app.core.tiempo import fecha_local
from app.database import get_db, safe_commit
from app.models import DetallePedido, Mesa, Pedido, Preparado, Producto, Usuario
from app.schemas import (
    DetallePedidoIn,
    DetallePedidoOut,
    MesaEstadoUpdate,
    MesaOut,
    PedidoCancelarIn,
    PedidoCreate,
    PedidoOut,
    RondaIn,
)
from app.services.disponibilidad import verificar_lineas
from app.services.historial import registrar
from app.services.pedidos import calcular_totales, siguiente_consecutivo
from app.services.preparados import cancelar_pedido
from app.services.websocket import ws_manager

router = APIRouter(prefix="/pedidos", tags=["pedidos"])

# Roles que pueden registrar/completar operaciones de dinero o de apertura
CREAN_PEDIDO = {"admin", "mesero", "cajero"}


# ============================================================
# MESAS
# ============================================================
@router.get("/mesas", response_model=list[MesaOut], tags=["mesas"])
def listar_mesas(db: Session = Depends(get_db), _: Usuario = Depends(staff_required)):
    return db.query(Mesa).filter(Mesa.activo.is_(True)).order_by(Mesa.numero).all()


@router.put("/mesas/{mesa_id}/estado", response_model=MesaOut, tags=["mesas"])
async def cambiar_estado_mesa(
    mesa_id: int,
    data: MesaEstadoUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(cashier_required),
):
    """La mesa se abre al crear el pedido (OCUPADA) y se libera al pagar/cerrar.
    EN_CURSO lo pone el sistema cuando cocina empieza a producir; no se libera una
    mesa que todavía tiene un pedido abierto."""
    mesa = db.get(Mesa, mesa_id)
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    if data.estado == "DISPONIBLE" and _mesa_con_pedido_abierto(db, mesa.id):
        raise HTTPException(status_code=409, detail=f"Mesa {mesa.numero} tiene un pedido abierto; ciérralo antes de liberarla")
    mesa.estado = data.estado
    safe_commit(db)
    db.refresh(mesa)
    await await_broadcast("mesa_update", {"mesa_id": mesa.id, "numero": mesa.numero, "estado": mesa.estado})
    return mesa


# ============================================================
# PEDIDOS
# ============================================================
def pedido_out(db: Session, pedido: Pedido, usuario: Usuario) -> PedidoOut:
    ver_dinero = usuario.rol.nombre in {"admin", "cajero", "mesero"}
    return PedidoOut(
        id=pedido.id,
        consecutivo=pedido.consecutivo,
        fecha_dia=pedido.fecha_dia,
        canal=pedido.canal,
        tipo_consumo=getattr(pedido, "tipo_consumo", "LOCAL") or "LOCAL",
        mesa_id=pedido.mesa_id,
        mesa_numero=pedido.mesa.numero if pedido.mesa else None,
        estado=pedido.estado,
        cliente=pedido.cliente,
        telefono=pedido.telefono,
        direccion=pedido.direccion,
        nota_interna=pedido.nota_interna,
        didi_orden_id=pedido.didi_orden_id,
        subtotal=pedido.subtotal if ver_dinero else None,
        iva=pedido.iva if ver_dinero else None,
        recargo_empaque=getattr(pedido, "recargo_empaque", Decimal("0")) if ver_dinero else None,
        total=pedido.total if ver_dinero else None,
        creado_en=pedido.creado_en,
        enviado_en=pedido.enviado_en,
        finalizado_en=pedido.finalizado_en,
        pagado_en=pedido.pagado_en,
        pagado=pedido.pagado_en is not None,
        cancelado_en=pedido.cancelado_en,
        motivo_cancelacion=pedido.motivo_cancelacion,
        detalles=[
            DetallePedidoOut(
                id=d.id,
                producto_id=d.producto_id,
                producto_nombre=d.producto.nombre,
                cantidad=d.cantidad,
                precio_unitario=d.precio_unitario if ver_dinero else None,
                variacion_snapshot=d.variacion_snapshot,
                ronda=d.ronda,
                estado=d.estado,
                preparado_en=d.preparado_en,
                listo_en=d.listo_en,
                entregado_en=d.entregado_en,
                cancelado_en=d.cancelado_en,
            )
            for d in pedido.detalles
        ],
    )


async def await_broadcast(evento: str, data: dict) -> None:
    await ws_manager.broadcast({"evento": evento, "data": data})


def _mesa_con_pedido_abierto(db: Session, mesa_id: int) -> bool:
    """Un pedido sigue 'abierto' mientras no esté pagado, cerrado ni cancelado."""
    return (
        db.query(Pedido.id)
        .filter(
            Pedido.mesa_id == mesa_id,
            Pedido.estado.notin_(("PAGADO", "CERRADO", "CANCELADO")),
        )
        .first()
        is not None
    )


def _validar_lineas(db: Session, lineas: list[DetallePedidoIn]) -> None:
    ids = {l.producto_id for l in lineas}
    encontrados = (
        db.query(Producto.id)
        .filter(Producto.id.in_(ids), Producto.activo.is_(True))
        .all()
    )
    if len(encontrados) != len(ids):
        raise HTTPException(status_code=404, detail="Uno o más productos no existen o están inactivos")

    for l in lineas:
        if l.cantidad <= Decimal("0"):
            raise HTTPException(status_code=422, detail="La cantidad de cada producto debe ser mayor a cero")
        if l.preparado_id is not None:
            prep = db.get(Preparado, l.preparado_id)
            if not prep or prep.producto_id != l.producto_id:
                raise HTTPException(status_code=404, detail=f"Preparado {l.preparado_id} no existe para el producto {l.producto_id}")
            if prep.estado != "DISPONIBLE":
                raise HTTPException(status_code=409, detail=f"El preparado {l.preparado_id} ya no está disponible ({prep.estado})")

    try:
        verificar_lineas(db, lineas)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


def _crear_detalles(
    db: Session,
    pedido: Pedido,
    lineas: list[DetallePedidoIn],
    ronda: int,
    usuario: Usuario | None = None,
) -> list[DetallePedido]:
    detalles = []
    for l in lineas:
        producto = db.get(Producto, l.producto_id)
        if not producto or not producto.activo:
            raise HTTPException(status_code=404, detail=f"Producto {l.producto_id} no existe o inactivo")

        snap = dict(l.variacion_snapshot or {})
        if l.preparado_id is not None:
            prep = db.query(Preparado).with_for_update().filter(Preparado.id == l.preparado_id).first()
            if not prep or prep.estado != "DISPONIBLE":
                raise HTTPException(status_code=409, detail=f"El preparado {l.preparado_id} ya no está disponible")
            prep.estado = "ASIGNADO"
            prep.pedido_nuevo_id = pedido.id
            prep.asignado_en = func.now()
            if usuario:
                prep.usuario_id = usuario.id
            if prep.variacion_snapshot:
                for k, v in prep.variacion_snapshot.items():
                    snap.setdefault(k, v)
            snap["es_preparado"] = True
            snap["preparado_id"] = prep.id
            nota = f"USAR PREPARADO ({int(l.cantidad)}x {producto.nombre})"
            if pedido.nota_interna:
                if nota not in pedido.nota_interna:
                    pedido.nota_interna += f" | {nota}"
            else:
                pedido.nota_interna = nota

        extra_adiciones = Decimal("0")
        if snap and "adiciones" in snap and isinstance(snap["adiciones"], list):
            for ad in snap["adiciones"]:
                if isinstance(ad, dict) and "precio" in ad and ad["precio"]:
                    try:
                        extra_adiciones += Decimal(str(ad["precio"]))
                    except Exception:
                        pass

        detalles.append(
            DetallePedido(
                pedido_id=pedido.id,
                ronda=ronda,
                producto_id=producto.id,
                producto=producto,
                cantidad=l.cantidad,
                precio_unitario=producto.precio + extra_adiciones,  # precio congelado al crearse
                variacion_snapshot=snap if snap else None,
            )
        )
    db.add_all(detalles)
    return detalles


@router.post("", response_model=PedidoOut, status_code=status.HTTP_201_CREATED)
async def crear_pedido(
    data: PedidoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(staff_required),
):
    if usuario.rol.nombre not in CREAN_PEDIDO:
        raise HTTPException(status_code=403, detail="Solo mesero, caja o admin pueden crear pedidos")

    if data.idempotency_key:
        existente = (
            db.query(Pedido)
            .options(joinedload(Pedido.detalles).joinedload(DetallePedido.producto), joinedload(Pedido.mesa))
            .filter(Pedido.idempotency_key == data.idempotency_key)
            .first()
        )
        if existente:
            return pedido_out(db, existente, usuario)

    if data.canal == "MESA":
        mesa = db.query(Mesa).with_for_update().filter(Mesa.id == data.mesa_id).first()
        if not mesa or not mesa.activo:
            raise HTTPException(status_code=404, detail="Mesa no encontrada")
        if mesa.estado != "DISPONIBLE" or _mesa_con_pedido_abierto(db, mesa.id):
            raise HTTPException(status_code=409, detail=f"Mesa {mesa.numero} ya está ocupada")
    elif data.canal == "DIDI" and not data.didi_orden_id:
        raise HTTPException(status_code=422, detail="El canal DIDI requiere didi_orden_id")

    _validar_lineas(db, data.lineas)

    dia = fecha_local()
    consecutivo = siguiente_consecutivo(db, dia)
    tipo_con = getattr(data, "tipo_consumo", "LOCAL") or "LOCAL"
    pedido = Pedido(
        idempotency_key=data.idempotency_key,
        consecutivo=consecutivo,
        fecha_dia=dia,
        canal=data.canal,
        tipo_consumo=tipo_con,
        mesa_id=data.mesa_id if data.canal == "MESA" else None,
        usuario_id=usuario.id,
        cliente=data.cliente,
        telefono=data.telefono,
        direccion=data.direccion,
        nota_interna=data.nota_interna,
        didi_orden_id=data.didi_orden_id,
    )
    db.add(pedido)
    db.flush()  # obtiene pedido.id sin commit

    detalles = _crear_detalles(db, pedido, data.lineas, ronda=1, usuario=usuario)
    totales = calcular_totales(db, detalles)

    recargo_empaque = Decimal("0")
    if tipo_con == "LLEVAR":
        from app.services.inventario import calcular_recargo_empaque
        recargo_empaque, _ = calcular_recargo_empaque(db, data.lineas)

    pedido.recargo_empaque = recargo_empaque
    pedido.subtotal = totales["subtotal"]
    pedido.iva = totales["iva"]
    pedido.total = totales["total"] + recargo_empaque

    if data.canal == "MESA":
        pedido.mesa.estado = "OCUPADA"  # la mesa se bloquea al abrir el pedido

    registrar(
        db, usuario, "CREAR_PEDIDO", "pedido", pedido.id,
        f"canal={pedido.canal} total={pedido.total}",
    )

    from app.services.sync import encolar_sync

    encolar_sync(
        db,
        tipo="CREAR_PEDIDO",
        entidad="pedido",
        payload={
            "id": pedido.id,
            "consecutivo": pedido.consecutivo,
            "fecha_dia": str(pedido.fecha_dia),
            "canal": pedido.canal,
            "mesa_id": pedido.mesa_id,
            "cliente": pedido.cliente,
            "subtotal": float(pedido.subtotal),
            "iva": float(pedido.iva),
            "total": float(pedido.total),
            "estado": pedido.estado,
            "detalles": [
                {
                    "producto_id": d.producto_id,
                    "cantidad": float(d.cantidad),
                    "precio_unitario": float(d.precio_unitario),
                    "ronda": d.ronda,
                    "estado": d.estado,
                }
                for d in detalles
            ],
        },
        entidad_id=pedido.id,
        dispositivo_id=f"USER_{usuario.id}",
    )
    safe_commit(db)
    db.refresh(pedido)

    await await_broadcast("pedido_creado", {"pedido_id": pedido.id, "consecutivo": pedido.consecutivo, "canal": pedido.canal})

    return pedido_out(db, pedido, usuario)


@router.get("", response_model=list[PedidoOut])
def listar_pedidos(
    estado: str | None = None,
    canal: str | None = None,
    tipo: str = "activos",  # activos | hoy | todos
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(staff_required),
):
    q = (
        db.query(Pedido)
        .options(joinedload(Pedido.detalles).joinedload(DetallePedido.producto), joinedload(Pedido.mesa))
        .order_by(Pedido.id.desc())
    )
    if estado:
        q = q.filter(Pedido.estado == estado)
    if canal:
        q = q.filter(Pedido.canal == canal)
    if tipo == "activos":
        q = q.filter(Pedido.estado.notin_(["CERRADO", "CANCELADO"]))
    elif tipo == "hoy":
        q = q.filter(Pedido.fecha_dia == fecha_local())
    pedidos = q.limit(100).all()
    return [pedido_out(db, p, usuario) for p in pedidos]


@router.get("/{pedido_id}", response_model=PedidoOut)
def obtener_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(staff_required),
):
    pedido = (
        db.query(Pedido)
        .options(joinedload(Pedido.detalles).joinedload(DetallePedido.producto), joinedload(Pedido.mesa))
        .filter(Pedido.id == pedido_id)
        .first()
    )
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return pedido_out(db, pedido, usuario)


@router.post("/{pedido_id}/enviar-a-cocina", response_model=PedidoOut)
async def enviar_a_cocina(
    pedido_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(staff_required),
):
    """El mesero envía el pedido a cocina. Regla del cliente:
    - NO descuenta inventario aquí: se descuenta cuando cocina ACEPTA (preparado_en).
    - La cocina recibe el ticket al instante vía WebSocket."""
    if usuario.rol.nombre not in CREAN_PEDIDO:
        raise HTTPException(status_code=403, detail="Solo mesero, caja o admin pueden enviar a cocina")

    pedido = (
        db.query(Pedido)
        .options(joinedload(Pedido.detalles).joinedload(DetallePedido.producto), joinedload(Pedido.mesa))
        .filter(Pedido.id == pedido_id)
        .first()
    )
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    if pedido.estado != "NUEVO":
        # Si ya fue enviado o está en preparación (caso de reintento offline tras corte Wi-Fi), devolver OK idempotente
        if pedido.estado in ("ENVIADO_A_COCINA", "EN_PREPARACION"):
            return pedido_out(db, pedido, usuario)
        raise HTTPException(
            status_code=409,
            detail=f"No se puede enviar un pedido en estado {pedido.estado}. Ya fue procesado.",
        )

    pedido.estado = "ENVIADO_A_COCINA"
    pedido.enviado_en = func.now()
    registrar(db, usuario, "ENVIAR_COCINA", "pedido", pedido.id, f"consecutivo={pedido.consecutivo}")
    safe_commit(db)
    db.refresh(pedido)

    await await_broadcast(
        "pedido_enviado",
        {
            "pedido_id": pedido.id,
            "consecutivo": pedido.consecutivo,
            "canal": pedido.canal,
            "mesa": pedido.mesa.numero if pedido.mesa else None,
        },
    )
    return pedido_out(db, pedido, usuario)


class TipoConsumoIn(BaseModel):
    tipo_consumo: str = Field(pattern="^(LOCAL|LLEVAR)$")


@router.patch("/{pedido_id}/tipo-consumo", response_model=PedidoOut)
async def cambiar_tipo_consumo(
    pedido_id: int,
    data: TipoConsumoIn,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(staff_required),
):
    """Conmuta un pedido abierto entre 'Comer aquí' y 'Para llevar' y recalcula el total
    (suma o quita los empaques marcados 'solo llevar' de las recetas). Solo antes de cobrar."""
    if usuario.rol.nombre not in CREAN_PEDIDO:
        raise HTTPException(status_code=403, detail="Solo mesero, caja o admin")

    pedido = (
        db.query(Pedido)
        .options(joinedload(Pedido.detalles).joinedload(DetallePedido.producto), joinedload(Pedido.mesa))
        .filter(Pedido.id == pedido_id)
        .first()
    )
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    if pedido.estado in ("CERRADO", "CANCELADO", "PAGADO") or pedido.pagado_en is not None:
        raise HTTPException(status_code=409, detail="El pedido ya fue cobrado, cerrado o cancelado")

    activos = [d for d in pedido.detalles if d.estado != "CANCELADO"]
    totales = calcular_totales(db, activos)

    recargo_empaque = Decimal("0")
    if data.tipo_consumo == "LLEVAR":
        from app.services.inventario import calcular_recargo_empaque
        recargo_empaque, _ = calcular_recargo_empaque(db, activos)

    anterior = pedido.tipo_consumo
    pedido.tipo_consumo = data.tipo_consumo
    pedido.recargo_empaque = recargo_empaque
    pedido.subtotal = totales["subtotal"]
    pedido.iva = totales["iva"]
    pedido.total = totales["total"] + recargo_empaque

    registrar(
        db, usuario, "CAMBIAR_TIPO_CONSUMO", "pedido", pedido.id,
        f"{anterior}->{data.tipo_consumo} recargo={recargo_empaque} total={pedido.total}",
    )
    safe_commit(db)
    db.refresh(pedido)

    await await_broadcast(
        "pedido_actualizado",
        {"pedido_id": pedido.id, "consecutivo": pedido.consecutivo, "tipo_consumo": pedido.tipo_consumo},
    )
    return pedido_out(db, pedido, usuario)


@router.post("/{pedido_id}/rondas", response_model=PedidoOut, status_code=status.HTTP_201_CREATED)
async def agregar_ronda(
    pedido_id: int,
    data: RondaIn,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(staff_required),
):
    """El mesero agrega otra ronda al pedido abierto (comida que salió después del primer envío)."""
    if usuario.rol.nombre not in CREAN_PEDIDO:
        raise HTTPException(status_code=403, detail="Solo mesero, caja o admin")

    pedido = (
        db.query(Pedido)
        .options(joinedload(Pedido.mesa))
        .filter(Pedido.id == pedido_id)
        .first()
    )
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    if pedido.estado in ("CERRADO", "CANCELADO", "PAGADO") or pedido.pagado_en is not None:
        raise HTTPException(status_code=409, detail="El pedido ya fue cobrado, cerrado o cancelado; no admite más rondas")

    _validar_lineas(db, data.lineas)
    detalles = _crear_detalles(db, pedido, data.lineas, ronda=data.ronda, usuario=usuario)
    totales = calcular_totales(db, pedido.detalles + detalles)

    if data.tipo_consumo:
        pedido.tipo_consumo = data.tipo_consumo

    recargo_empaque = Decimal("0")
    if getattr(pedido, "tipo_consumo", "LOCAL") == "LLEVAR":
        from app.services.inventario import calcular_recargo_empaque
        recargo_empaque, _ = calcular_recargo_empaque(db, pedido.detalles + detalles)

    pedido.recargo_empaque = recargo_empaque
    pedido.subtotal = totales["subtotal"]
    pedido.iva = totales["iva"]
    pedido.total = totales["total"] + recargo_empaque

    # Regla del dueño: cada ronda es un ticket PROPIO para cocina. Si la cocina ya
    # había terminado/entregado el pedido, la ronda nueva lo reactiva como ticket
    # nuevo (excepto si el pedido aún no se ha enviado: NUEVO).
    reactivo = False
    if pedido.estado not in ("NUEVO", "ENVIADO_A_COCINA", "EN_PREPARACION"):
        pedido.estado = "ENVIADO_A_COCINA"
        pedido.enviado_en = func.now()
        reactivo = True

    registrar(
        db, usuario, "AGREGAR_RONDA", "pedido", pedido.id,
        f"consecutivo={pedido.consecutivo} ronda={data.ronda}",
    )

    from app.services.sync import encolar_sync

    encolar_sync(
        db,
        tipo="AGREGAR_RONDA",
        entidad="detalle_pedido",
        payload={
            "pedido_id": pedido.id,
            "consecutivo": pedido.consecutivo,
            "ronda": data.ronda,
            "nuevo_total": float(pedido.total),
            "detalles": [
                {
                    "producto_id": d.producto_id,
                    "cantidad": float(d.cantidad),
                    "precio_unitario": float(d.precio_unitario),
                    "ronda": d.ronda,
                }
                for d in detalles
            ],
        },
        entidad_id=pedido.id,
        dispositivo_id=f"USER_{usuario.id}",
    )
    safe_commit(db)
    db.refresh(pedido)

    await await_broadcast(
        "ronda_agregada",
        {"pedido_id": pedido.id, "consecutivo": pedido.consecutivo, "ronda": data.ronda},
    )
    if reactivo:
        await await_broadcast(
            "pedido_enviado",
            {
                "pedido_id": pedido.id,
                "consecutivo": pedido.consecutivo,
                "canal": pedido.canal,
                "mesa": pedido.mesa.numero if pedido.mesa else None,
            },
        )
    return pedido_out(db, pedido, usuario)


@router.post("/{pedido_id}/cancelar", response_model=PedidoOut)
async def cancelar_pedido_endpoint(
    pedido_id: int,
    data: PedidoCancelarIn,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(admin_required),
):
    """Cancela un pedido (SOLO ADMIN, regla del dueño).
    - Motivo obligatorio registrado en historial_accion.
    - Si ya pagó: genera devolución en caja (SALIDA).
    - Si ya se produjo en cocina: insumos quedan descontados y pasan a PREPARADOS para reventa.
    - Si no se produjo: no se descuenta nada.
    - Si tiene mesa: la libera si no hay otros pedidos abiertos en ella."""
    pedido = (
        db.query(Pedido)
        .options(
            joinedload(Pedido.detalles).joinedload(DetallePedido.producto),
            joinedload(Pedido.mesa),
            joinedload(Pedido.pagos),
        )
        .filter(Pedido.id == pedido_id)
        .first()
    )
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    try:
        pedido, preparados = cancelar_pedido(db, pedido, data.motivo, admin)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    await await_broadcast(
        "pedido_cancelado",
        {
            "pedido_id": pedido.id,
            "consecutivo": pedido.consecutivo,
            "motivo": data.motivo,
            "mesa": pedido.mesa.numero if pedido.mesa else None,
            "preparados_creados": len(preparados),
        },
    )
    if pedido.mesa:
        await await_broadcast(
            "mesa_update",
            {"mesa_id": pedido.mesa.id, "numero": pedido.mesa.numero, "estado": pedido.mesa.estado},
        )
    if preparados:
        await await_broadcast(
            "preparados_actualizados",
            {"cantidad_nuevos": len(preparados)},
        )

    return pedido_out(db, pedido, admin)