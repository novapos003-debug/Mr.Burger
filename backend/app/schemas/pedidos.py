from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------- MESAS ----------
class MesaOut(BaseModel):
    id: int
    numero: int
    estado: str  # DISPONIBLE | EN_CURSO | OCUPADA
    activo: bool

    model_config = ConfigDict(from_attributes=True)


class MesaEstadoUpdate(BaseModel):
    estado: str = Field(pattern="^(DISPONIBLE|EN_CURSO|OCUPADA)$")


# ---------- DETALLE PEDIDO ----------
class DetallePedidoIn(BaseModel):
    producto_id: int
    cantidad: Decimal = Field(default=Decimal("1"), gt=0)
    variacion_snapshot: dict | None = None  # modificaciones: {"sin_tomate": true, "doble_carne": true}
    preparado_id: int | None = None  # id del preparado reusable si aplica


class RondaIn(BaseModel):
    ronda: int = Field(gt=0)
    lineas: list[DetallePedidoIn] = Field(min_length=1)


class DetallePedidoOut(BaseModel):
    id: int
    producto_id: int
    producto_nombre: str | None = None
    cantidad: Decimal
    precio_unitario: Decimal | None  # oculto para cocina (no ven dinero)
    variacion_snapshot: dict | None
    ronda: int
    estado: str
    preparado_en: datetime | None
    listo_en: datetime | None
    entregado_en: datetime | None
    cancelado_en: datetime | None


# ---------- PEDIDO ----------
class PedidoCreate(BaseModel):
    canal: str = Field(pattern="^(MESA|MOSTRADOR|DIDI|DOMICILIO)$")
    mesa_id: int | None = Field(default=None, validate_default=True)
    cliente: str | None = None
    telefono: str | None = None
    direccion: str | None = None
    nota_interna: str | None = None
    didi_orden_id: str | None = None
    lineas: list[DetallePedidoIn] = Field(min_length=1)

    @field_validator("mesa_id")
    @classmethod
    def mesa_requerida(cls, v, info):
        if info.data.get("canal") == "MESA" and v is None:
            raise ValueError("Canal MESA requiere mesa_id")
        if info.data.get("canal") != "MESA" and v is not None:
            raise ValueError("mesa_id solo aplica a canal MESA")
        return v


class PedidoOut(BaseModel):
    id: int
    consecutivo: int
    fecha_dia: date
    canal: str
    mesa_id: int | None
    mesa_numero: int | None = None
    estado: str
    cliente: str | None
    telefono: str | None
    direccion: str | None
    nota_interna: str | None
    didi_orden_id: str | None
    subtotal: Decimal | None  # oculto para cocina
    iva: Decimal | None
    total: Decimal | None
    creado_en: datetime
    enviado_en: datetime | None
    finalizado_en: datetime | None
    pagado_en: datetime | None
    pagado: bool = False
    cancelado_en: datetime | None
    motivo_cancelacion: str | None = None
    detalles: list[DetallePedidoOut]

    model_config = ConfigDict(from_attributes=True)