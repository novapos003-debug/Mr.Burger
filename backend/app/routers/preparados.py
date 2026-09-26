from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.core.deps import admin_required, staff_required
from app.database import get_db
from app.models import Pedido, Preparado, Usuario
from app.schemas import (
    PreparadoAsignarIn,
    PreparadoDescartarIn,
    PreparadoOut,
    PreparadoSugerenciaOut,
)
from app.services.preparados import (
    asignar_preparado,
    descartar_preparado,
    preparado_a_out,
    sugerir_preparado,
)
from app.services.websocket import ws_manager

router = APIRouter(prefix="/preparados", tags=["preparados"])


@router.get("", response_model=list[PreparadoOut])
def listar_preparados(
    estado: str | None = Query(default="DISPONIBLE"),
    producto_id: int | None = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(staff_required),
):
    """Lista los preparados calientes en espera de reventa o histórico.
    Por defecto muestra los DISPONIBLES con sus minutos de espera calculados."""
    q = (
        db.query(Preparado)
        .options(
            joinedload(Preparado.producto),
            joinedload(Preparado.pedido_origen),
        )
        .order_by(Preparado.creado_en.asc())
    )
    if estado:
        q = q.filter(Preparado.estado == estado)
    if producto_id is not None:
        q = q.filter(Preparado.producto_id == producto_id)
    preparados = q.all()
    return [preparado_a_out(p) for p in preparados]


@router.get("/sugerir", response_model=PreparadoSugerenciaOut)
def obtener_sugerencia(
    producto_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(staff_required),
):
    """Busca si hay un preparado caliente listo para que el mesero gane tiempo."""
    prep = sugerir_preparado(db, producto_id)
    if not prep:
        return PreparadoSugerenciaOut(coincidencia=False, preparado=None, mensaje="No hay preparados disponibles")

    prod_nombre = prep.producto.nombre if prep.producto else "producto"
    return PreparadoSugerenciaOut(
        coincidencia=True,
        preparado=preparado_a_out(prep),
        mensaje=f"Ya existe 1x {prod_nombre} lista de un pedido cancelado. ¿Deseas usarla?",
    )


@router.post("/{preparado_id}/asignar", response_model=PreparadoOut)
async def asignar(
    preparado_id: int,
    data: PreparadoAsignarIn,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(staff_required),
):
    """Asigna un preparado a un pedido en curso (protección de concurrencia con lock).
    - Agrega la línea al pedido sin descontar inventario nuevo.
    - Se cobrará al cliente a precio normal al momento de pagar."""
    if usuario.rol.nombre not in {"admin", "mesero", "cajero"}:
        raise HTTPException(status_code=403, detail="Rol sin permiso para asignar preparados")

    try:
        prep, pedido = asignar_preparado(db, preparado_id, data.pedido_id, usuario)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    await ws_manager.broadcast(
        {
            "evento": "preparado_asignado",
            "data": {
                "preparado_id": prep.id,
                "producto_id": prep.producto_id,
                "pedido_id": pedido.id,
                "consecutivo": pedido.consecutivo,
            },
        }
    )
    return preparado_a_out(prep)


@router.post("/{preparado_id}/descartar", response_model=PreparadoOut)
async def descartar(
    preparado_id: int,
    data: PreparadoDescartarIn,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(admin_required),
):
    """Admin descarta un preparado caliente por exceso de tiempo o desperdicio."""
    try:
        prep = descartar_preparado(db, preparado_id, data.motivo, admin)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    await ws_manager.broadcast(
        {
            "evento": "preparado_descartado",
            "data": {
                "preparado_id": prep.id,
                "producto_id": prep.producto_id,
                "motivo": data.motivo,
            },
        }
    )
    return preparado_a_out(prep)
