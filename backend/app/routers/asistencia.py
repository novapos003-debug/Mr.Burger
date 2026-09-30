from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.database import get_db, safe_commit
from app.models.usuario import Usuario
from app.models.asistencia import TurnoLaboral
from app.core.deps import get_current_user, admin_required

router = APIRouter(prefix="/asistencia", tags=["asistencia"])

class TurnoLaboralOut(BaseModel):
    id: int
    usuario_id: int
    nombre_usuario: str
    rol: str
    entrada_en: datetime
    salida_en: Optional[datetime]
    motivo_cierre: Optional[str]

    class Config:
        from_attributes = True

@router.post("/entrada", response_model=TurnoLaboralOut)
def registrar_entrada(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    """Registra la entrada (clock-in) de un usuario si no tiene un turno abierto."""
    if current_user.rol.nombre == "admin":
        raise HTTPException(status_code=400, detail="El administrador no registra turnos de asistencia.")

    # Buscar si ya tiene un turno abierto
    turno_abierto = db.query(TurnoLaboral).filter(
        TurnoLaboral.usuario_id == current_user.id,
        TurnoLaboral.salida_en.is_(None)
    ).first()

    if turno_abierto:
        return {
            "id": turno_abierto.id,
            "usuario_id": turno_abierto.usuario_id,
            "nombre_usuario": current_user.nombre,
            "rol": turno_abierto.rol,
            "entrada_en": turno_abierto.entrada_en,
            "salida_en": turno_abierto.salida_en,
            "motivo_cierre": turno_abierto.motivo_cierre
        }

    # Si no tiene turno, crear uno nuevo
    nuevo_turno = TurnoLaboral(
        usuario_id=current_user.id,
        rol=current_user.rol.nombre
    )
    db.add(nuevo_turno)
    safe_commit(db)
    db.refresh(nuevo_turno)

    return {
        "id": nuevo_turno.id,
        "usuario_id": nuevo_turno.usuario_id,
        "nombre_usuario": current_user.nombre,
        "rol": nuevo_turno.rol,
        "entrada_en": nuevo_turno.entrada_en,
        "salida_en": nuevo_turno.salida_en,
        "motivo_cierre": nuevo_turno.motivo_cierre
    }

@router.post("/salida", response_model=TurnoLaboralOut)
def registrar_salida(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    """Registra la salida (clock-out) explícita de un usuario."""
    turno_abierto = db.query(TurnoLaboral).filter(
        TurnoLaboral.usuario_id == current_user.id,
        TurnoLaboral.salida_en.is_(None)
    ).first()

    if not turno_abierto:
        raise HTTPException(status_code=400, detail="No tienes un turno abierto para cerrar.")

    turno_abierto.salida_en = func.now()
    turno_abierto.motivo_cierre = "MANUAL"
    safe_commit(db)
    db.refresh(turno_abierto)

    return {
        "id": turno_abierto.id,
        "usuario_id": turno_abierto.usuario_id,
        "nombre_usuario": current_user.nombre,
        "rol": turno_abierto.rol,
        "entrada_en": turno_abierto.entrada_en,
        "salida_en": turno_abierto.salida_en,
        "motivo_cierre": turno_abierto.motivo_cierre
    }

@router.get("/mi-turno", response_model=Optional[TurnoLaboralOut])
def mi_turno(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    """Devuelve el turno activo del usuario actual, si lo hay."""
    turno = db.query(TurnoLaboral).filter(
        TurnoLaboral.usuario_id == current_user.id,
        TurnoLaboral.salida_en.is_(None)
    ).first()

    if not turno:
        return None

    return {
        "id": turno.id,
        "usuario_id": turno.usuario_id,
        "nombre_usuario": current_user.nombre,
        "rol": turno.rol,
        "entrada_en": turno.entrada_en,
        "salida_en": turno.salida_en,
        "motivo_cierre": turno.motivo_cierre
    }

@router.get("/admin/activos", response_model=List[TurnoLaboralOut])
def obtener_activos(db: Session = Depends(get_db), admin: Usuario = Depends(admin_required)):
    """Devuelve los turnos de todos los empleados que están trabajando ahora mismo."""
    turnos = db.query(TurnoLaboral, Usuario).join(Usuario).filter(
        TurnoLaboral.salida_en.is_(None)
    ).all()
    
    return [
        {
            "id": t.id,
            "usuario_id": t.usuario_id,
            "nombre_usuario": u.nombre,
            "rol": t.rol,
            "entrada_en": t.entrada_en,
            "salida_en": t.salida_en,
            "motivo_cierre": t.motivo_cierre
        } for t, u in turnos
    ]

@router.get("/admin/historial", response_model=List[TurnoLaboralOut])
def obtener_historial(
    limit: int = 100, 
    offset: int = 0, 
    db: Session = Depends(get_db), 
    admin: Usuario = Depends(admin_required)
):
    """Devuelve el historial de turnos."""
    turnos = db.query(TurnoLaboral, Usuario).join(Usuario).order_by(
        TurnoLaboral.entrada_en.desc()
    ).limit(limit).offset(offset).all()
    
    return [
        {
            "id": t.id,
            "usuario_id": t.usuario_id,
            "nombre_usuario": u.nombre,
            "rol": t.rol,
            "entrada_en": t.entrada_en,
            "salida_en": t.salida_en,
            "motivo_cierre": t.motivo_cierre
        } for t, u in turnos
    ]

@router.post("/admin/{turno_id}/cerrar", response_model=TurnoLaboralOut)
def cerrar_turno_admin(turno_id: int, db: Session = Depends(get_db), admin: Usuario = Depends(admin_required)):
    """Permite al admin cerrar manualmente un turno olvidado."""
    turno = db.query(TurnoLaboral).filter(TurnoLaboral.id == turno_id).first()
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    
    if turno.salida_en is not None:
        raise HTTPException(status_code=400, detail="El turno ya está cerrado")
        
    turno.salida_en = func.now()
    turno.motivo_cierre = "ADMIN"
    safe_commit(db)
    db.refresh(turno)
    
    return {
        "id": turno.id,
        "usuario_id": turno.usuario_id,
        "nombre_usuario": turno.usuario.nombre,
        "rol": turno.rol,
        "entrada_en": turno.entrada_en,
        "salida_en": turno.salida_en,
        "motivo_cierre": turno.motivo_cierre
    }
