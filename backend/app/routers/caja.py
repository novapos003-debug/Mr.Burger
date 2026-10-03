from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.deps import admin_required, cashier_required
from app.database import get_db
from app.models import Cierre, DetallePedido, MovimientoCaja, Pago, Pedido, Usuario, Vale
from app.schemas import (
    CierreCerrarIn,
    CierreOut,
    CobroIn,
    CobroOut,
    DevolucionIn,
    MovimientoCajaIn,
    MovimientoCajaOut,
    PagoOut,
    TurnoAperturaIn,
    ValeCobroIn,
    ValeOut,
)
from app.services.caja import (
    abrir_turno,
    cerrar_turno,
    cobrar_pedido,
    cobrar_vale,
    devolver_pago,
    registrar_movimiento,
    turno_abierto,
    obtener_turno_actual_con_metricas,
)
from app.services.websocket import ws_manager

router = APIRouter(prefix="/caja", tags=["caja"])


def _get_pedido(db: Session, pedido_id: int, lock: bool = False) -> Pedido:
    q = (
        db.query(Pedido)
        .options(
            joinedload(Pedido.mesa),
            joinedload(Pedido.detalles).joinedload(DetallePedido.producto),
        )
        .filter(Pedido.id == pedido_id)
    )
    if lock:
        q = q.with_for_update(of=Pedido)
    pedido = q.first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return pedido


@router.post("/pedidos/{pedido_id}/cobrar", response_model=CobroOut)
async def cobrar(
    pedido_id: int,
    data: CobroIn,
    db: Session = Depends(get_db),
    cajero: Usuario = Depends(cashier_required),
):
    """Cobra un pedido (uno o varios métodos). Caja es el único rol que ve dinero."""
    pedido = _get_pedido(db, pedido_id, lock=True)
    if not turno_abierto(db):
        raise HTTPException(
            status_code=409,
            detail="No hay un turno de caja abierto. Debe abrir turno con la base inicial antes de cobrar.",
        )
    if pedido.estado == "CANCELADO":
        raise HTTPException(status_code=409, detail="El pedido está cancelado")
    if pedido.estado in ("CERRADO", "PAGADO") or pedido.pagado_en is not None:
        raise HTTPException(status_code=409, detail="El pedido ya fue cobrado o cerrado")

    try:
        resultado = cobrar_pedido(db, pedido, data, cajero)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    pedido = resultado["pedido"]
    await ws_manager.broadcast(
        {
            "evento": "pedido_pagado",
            # Sin montos: el evento llega a TODOS los dispositivos (mesero/cocina no ven dinero).
            "data": {
                "pedido_id": pedido.id,
                "consecutivo": pedido.consecutivo,
                "estado": pedido.estado,
                "pagado": pedido.pagado_en is not None,
            },
        }
    )
    return CobroOut(
        pedido_id=pedido.id,
        consecutivo=pedido.consecutivo,
        total=pedido.total,
        pagado=pedido.pagado_en is not None,
        pagos=[PagoOut.model_validate(p) for p in resultado["pagos"]],
        vales=[ValeOut.model_validate(v) for v in resultado["vales"]],
    )


@router.get("/pedidos/{pedido_id}/pagos", response_model=list[PagoOut])
def listar_pagos(
    pedido_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(cashier_required),
):
    _get_pedido(db, pedido_id)
    return (
        db.query(Pago)
        .filter(Pago.pedido_id == pedido_id)
        .order_by(Pago.id)
        .all()
    )


@router.post("/pagos/{pago_id}/devolver", response_model=PagoOut)
def devolver(
    pago_id: int,
    data: DevolucionIn,
    db: Session = Depends(get_db),
    cajero: Usuario = Depends(cashier_required),
):
    """Devuelve un pago con motivo obligatorio (queda en el historial de caja)."""
    pago = (
        db.query(Pago)
        .options(joinedload(Pago.pedido).joinedload(Pedido.mesa))
        .filter(Pago.id == pago_id)
        .first()
    )
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    try:
        pago = devolver_pago(db, pago, data.motivo, cajero)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return pago


@router.get("/vales", response_model=list[ValeOut])
def listar_vales(
    estado: str | None = None,
    pedido_id: int | None = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(cashier_required),
):
    q = db.query(Vale)
    if estado:
        q = q.filter(Vale.estado == estado)
    if pedido_id is not None:
        q = q.filter(Vale.pedido_id == pedido_id)
    return q.order_by(Vale.id.desc()).limit(200).all()


@router.post("/vales/{vale_id}/cobrar", response_model=ValeOut)
def cobrar_vale_endpoint(
    vale_id: int,
    data: ValeCobroIn | None = None,
    db: Session = Depends(get_db),
    cajero: Usuario = Depends(cashier_required),
):
    """El cliente paga su pagaré: queda COBRADO e ingresa el dinero a caja."""
    vale = db.get(Vale, vale_id)
    if not vale:
        raise HTTPException(status_code=404, detail="Vale no encontrado")
    descripcion = data.descripcion if data else None
    try:
        cobrar_vale(db, vale, cajero, descripcion)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return vale


@router.get("/movimientos", response_model=list[MovimientoCajaOut])
def listar_movimientos(
    categoria: str | None = None,
    tipo: str | None = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(cashier_required),
):
    q = db.query(MovimientoCaja)
    if categoria:
        q = q.filter(MovimientoCaja.categoria == categoria)
    if tipo:
        q = q.filter(MovimientoCaja.tipo == tipo)
    return q.order_by(MovimientoCaja.id.desc()).limit(200).all()


# ============================================================
# TURNO DE CAJA (apertura + cierre)  /  ENTRADAS-EGRESOS ADMIN
# ============================================================

@router.get("/turno", response_model=CierreOut | None)
def ver_turno(
    db: Session = Depends(get_db),
    _: Usuario = Depends(cashier_required),
):
    """Turno de caja abierto actualmente con métricas acumuladas en vivo (o null si no hay ninguno)."""
    return obtener_turno_actual_con_metricas(db)


@router.post("/turno/abrir", response_model=CierreOut, status_code=201)
def abrir_turno_endpoint(
    data: TurnoAperturaIn,
    db: Session = Depends(get_db),
    cajero: Usuario = Depends(cashier_required),
):
    """Abre el turno de caja. Solo puede existir un turno abierto a la vez."""
    try:
        return abrir_turno(db, cajero, data.monto_inicial)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/turno/cerrar", response_model=CierreOut)
async def cerrar_turno_endpoint(
    data: CierreCerrarIn | None = None,
    db: Session = Depends(get_db),
    cajero: Usuario = Depends(cashier_required),
):
    """Cierra el turno abierto y congela el fotograma del turno."""
    cierre = turno_abierto(db)
    if cierre is None:
        raise HTTPException(status_code=409, detail="No hay un turno de caja abierto")
    try:
        return cerrar_turno(db, cierre, cajero, data.notas if data else None)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/movimientos", response_model=MovimientoCajaOut, status_code=201)
def crear_movimiento(
    data: MovimientoCajaIn,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(admin_required),
):
    """Entrada/egreso manual de caja: SOLO admin (regla del dueño)."""
    return registrar_movimiento(db, admin, data)


@router.get("/cierres", response_model=list[CierreOut])
def listar_cierres(
    db: Session = Depends(get_db),
    _: Usuario = Depends(cashier_required),
):
    return db.query(Cierre).order_by(Cierre.id.desc()).limit(100).all()


@router.get("/cierres/{cierre_id}", response_model=CierreOut)
def obtener_cierre(
    cierre_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(cashier_required),
):
    cierre = db.get(Cierre, cierre_id)
    if not cierre:
        raise HTTPException(status_code=404, detail="Cierre no encontrado")
    return cierre
