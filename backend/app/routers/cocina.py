from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.deps import kitchen_required
from app.database import get_db
from app.models import DetallePedido, Pedido, Usuario
from app.schemas import TicketOut
from app.services.cocina import cola_cocina, descontar_inventario, minutos_cocina
from app.services.historial import registrar
from app.services.websocket import ws_manager

router = APIRouter(prefix="/cocina", tags=["cocina"])


def _get_detalle(db: Session, detalle_id: int) -> DetallePedido:
    detalle = (
        db.query(DetallePedido)
        .options(
            joinedload(DetallePedido.pedido),
            joinedload(DetallePedido.producto),
        )
        .filter(DetallePedido.id == detalle_id)
        .first()
    )
    if not detalle:
        raise HTTPException(status_code=404, detail="Detalle no encontrado")
    return detalle


def _ticket_solo(db: Session, pedido_id: int):
    for t in cola_cocina(db):
        if t["pedido_id"] == pedido_id:
            return t
    return None


@router.get("/cola", response_model=list[TicketOut])
def ver_cola_cocina(
    db: Session = Depends(get_db),
    _: Usuario = Depends(kitchen_required),
):
    """Cola de tickets activos (ENVIADO_A_COCINA / EN_PREPARACION), por ronda.
    La cocina NO ve precios ni totales."""
    return cola_cocina(db)


@router.post("/detalles/{detalle_id}/aceptar", response_model=TicketOut)
async def aceptar_detalle(
    detalle_id: int,
    db: Session = Depends(get_db),
    cocinero: Usuario = Depends(kitchen_required),
):
    """La cocina acepta el detalle => PREPARANDO con preparado_en + descuenta el
    inventario según la receta. Regla del cliente: el stock baja al aceptar, no al
    enviar ni al pagar."""
    detalle = _get_detalle(db, detalle_id)
    if detalle.estado != "ENVIADO":
        raise HTTPException(status_code=409, detail=f"Detalle en estado {detalle.estado}; solo se acepta desde ENVIADO")

    pedido = detalle.pedido
    if pedido.estado not in ("ENVIADO_A_COCINA", "EN_PREPARACION"):
        raise HTTPException(status_code=409, detail=f"Pedido en estado {pedido.estado}; no está activo en cocina")

    descontar_inventario(db, detalle, cocinero)

    detalle.estado = "PREPARANDO"
    detalle.preparado_en = func.now()
    pedido.estado = "EN_PREPARACION"
    if pedido.canal == "MESA" and pedido.mesa is not None:
        pedido.mesa.estado = "EN_CURSO"  # la mesa refleja que la comida está en producción
    registrar(
        db, cocinero, "ACEPTAR_PREPARACION", "detalle", detalle.id,
        f"pedido={pedido.consecutivo} producto={detalle.producto.nombre}",
    )
    db.commit()
    db.refresh(detalle)

    await ws_manager.broadcast(
        {
            "evento": "detalle_aceptado",
            "data": {
                "detalle_id": detalle.id,
                "pedido_id": pedido.id,
                "producto_id": detalle.producto_id,
                "ronda": detalle.ronda,
            },
        }
    )

    ticket = _ticket_solo(db, pedido.id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Pedido ya no está activo en cocina")
    return ticket


@router.post("/detalles/{detalle_id}/listo", response_model=TicketOut)
async def marcar_listo(
    detalle_id: int,
    db: Session = Depends(get_db),
    cocinero: Usuario = Depends(kitchen_required),
):
    """Con el detalle PREPARANDO, la cocina lo da por listo (LISTO con listo_en).
    Si era el último pendiente, el pedido pasa a FINALIZADO (cocina terminó)."""
    detalle = _get_detalle(db, detalle_id)
    if detalle.estado != "PREPARANDO":
        raise HTTPException(status_code=409, detail=f"Detalle en estado {detalle.estado}; solo se marca LISTO desde PREPARANDO")

    pedido = detalle.pedido
    detalle.estado = "LISTO"
    detalle.listo_en = func.now()
    registrar(
        db, cocinero, "MARCAR_LISTO", "detalle", detalle.id,
        f"pedido={pedido.consecutivo} producto={detalle.producto.nombre}",
    )
    db.commit()
    db.refresh(detalle)

    restantes = (
        db.query(DetallePedido.id)
        .filter(
            DetallePedido.pedido_id == pedido.id,
            DetallePedido.estado.in_(("ENVIADO", "PREPARANDO")),
        )
        .count()
    )
    if restantes == 0:
        pedido.finalizado_en = func.now()
        if pedido.pagado_en is not None:
            # Cobro adelantado (mostrador/DiDi): la cocina terminó y ya estaba pagado.
            pedido.estado = "PAGADO"
            if pedido.canal == "MESA" and pedido.mesa is not None:
                pedido.mesa.estado = "DISPONIBLE"
        else:
            pedido.estado = "FINALIZADO"
        db.commit()

    await ws_manager.broadcast(
        {
            "evento": "detalle_listo",
            "data": {"detalle_id": detalle.id, "pedido_id": pedido.id, "ronda": detalle.ronda},
        }
    )
    if pedido.estado in ("FINALIZADO", "PAGADO"):
        await ws_manager.broadcast(
            {"evento": "pedido_finalizado", "data": {"pedido_id": pedido.id, "consecutivo": pedido.consecutivo}}
        )

    ticket = _ticket_solo(db, pedido.id)
    if ticket is None:
        if pedido.estado in ("FINALIZADO", "PAGADO"):
            return {
                "pedido_id": pedido.id,
                "consecutivo": pedido.consecutivo,
                "canal": pedido.canal,
                "mesa_numero": pedido.mesa.numero if pedido.mesa else None,
                "cliente": pedido.cliente,
                "telefono": pedido.telefono,
                "direccion": pedido.direccion,
                "nota_interna": pedido.nota_interna,
                "minutos_temporizador": minutos_cocina(db),
                "tiempo_excedido": False,
                "segundos_transcurridos": 0,
                "rondas": [],
            }
        raise HTTPException(status_code=404, detail="Pedido ya no está activo en cocina")
    return ticket