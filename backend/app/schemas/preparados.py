from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PedidoCancelarIn(BaseModel):
    motivo: str = Field(min_length=5, description="Motivo obligatorio de la cancelación")


class PreparadoOut(BaseModel):
    id: int
    producto_id: int
    producto_nombre: str | None = None
    pedido_origen_id: int
    pedido_origen_consecutivo: int | None = None
    detalle_origen_id: int
    variacion_snapshot: dict | None = None
    cantidad: Decimal
    estado: str  # DISPONIBLE | ASIGNADO | DESCARTADO
    pedido_nuevo_id: int | None = None
    usuario_id: int | None = None
    creado_en: datetime
    minutos_espera: int = 0
    asignado_en: datetime | None = None
    descartado_en: datetime | None = None
    motivo_descarte: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PreparadoAsignarIn(BaseModel):
    pedido_id: int


class PreparadoDescartarIn(BaseModel):
    motivo: str | None = Field(default=None, min_length=3)


class PreparadoSugerenciaOut(BaseModel):
    coincidencia: bool
    preparado: PreparadoOut | None = None
    mensaje: str | None = None
