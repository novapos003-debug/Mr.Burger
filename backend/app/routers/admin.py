from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import admin_required
from app.database import get_db
from app.models import Usuario
from app.schemas.admin import (
    AlertaStockItem,
    CompraIn,
    CompraOut,
    DashboardOut,
    HistorialAccionOut,
    ReporteVentasOut,
)
from app.services.admin import (
    consultar_auditoria,
    listar_compras,
    obtener_dashboard,
    obtener_stock_critico,
    registrar_compra,
    reporte_ventas,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard", response_model=DashboardOut)
def ver_dashboard(
    fecha: date | None = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_required),
):
    """Dashboard gerencial para el iPad/móvil del dueño.
    Muestra KPIs en vivo, ticket promedio, ventas por canal y métodos, alertas de stock."""
    return obtener_dashboard(db, fecha)


@router.get("/reportes/ventas", response_model=ReporteVentasOut)
def ver_reporte_ventas(
    desde: date = Query(...),
    hasta: date = Query(...),
    canal: str | None = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_required),
):
    """Genera reporte histórico de ventas por rango de fechas y canal."""
    if desde > hasta:
        raise HTTPException(status_code=422, detail="La fecha 'desde' no puede ser posterior a 'hasta'")
    return reporte_ventas(db, desde, hasta, canal)


@router.get("/stock-critico", response_model=list[AlertaStockItem])
def ver_stock_critico(
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_required),
):
    """Lista insumos en nivel crítico con déficit y costo estimado para abastecer."""
    return obtener_stock_critico(db)


@router.get("/auditoria", response_model=list[HistorialAccionOut])
def ver_auditoria(
    usuario_id: int | None = None,
    accion: str | None = None,
    entidad: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_required),
):
    """Consulta paginada del historial inmutable de acciones del sistema."""
    return consultar_auditoria(db, usuario_id, accion, entidad, limit, offset)


@router.post("/compras", response_model=CompraOut, status_code=status.HTTP_201_CREATED)
def crear_compra(
    data: CompraIn,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(admin_required),
):
    """Registra una compra de insumos reabasteciendo el inventario."""
    try:
        compra = registrar_compra(db, data, admin)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    compras = listar_compras(db, limit=1, offset=0)
    return next((c for c in compras if c.id == compra.id), None)


@router.get("/compras", response_model=list[CompraOut])
def ver_compras(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_required),
):
    """Lista el historial de compras a proveedores con sus detalles."""
    return listar_compras(db, limit, offset)


# ============================================================
# CONFIGURACIÓN DEL LOCAL
# ============================================================
from pydantic import BaseModel
from app.models import Configuracion


class ConfiguracionUpdateIn(BaseModel):
    valor: str


@router.get("/configuracion")
def listar_configuracion(
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_required),
):
    """Retorna las configuraciones globales del restaurante."""
    return db.query(Configuracion).all()


@router.put("/configuracion/{clave}")
def actualizar_configuracion(
    clave: str,
    data: ConfiguracionUpdateIn,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(admin_required),
):
    """Actualiza un parámetro de configuración (ej: politica_stock_insuficiente, iva_porcentaje, minutos_cocina)."""
    cfg = db.get(Configuracion, clave)
    if not cfg:
        cfg = Configuracion(clave=clave, valor=data.valor)
        db.add(cfg)
    else:
        cfg.valor = data.valor
    from app.services.historial import registrar
    registrar(db, usuario, "MODIFICAR_CONFIG", "configuracion", None, f"{clave}={data.valor}")
    db.commit()
    db.refresh(cfg)
    return cfg

