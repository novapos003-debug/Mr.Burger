from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class TicketDetalleOut(BaseModel):
    detalle_id: int
    producto_id: int
    producto_nombre: str
    cantidad: Decimal
    variacion_snapshot: dict | None
    estado: str
    preparado_en: datetime | None
    listo_en: datetime | None


class TicketRondaOut(BaseModel):
    ronda: int
    detalles: list[TicketDetalleOut]


class TicketOut(BaseModel):
    """Ticket para la cocina: SIN precios ni totales (regla: cocina no ve dinero)."""

    pedido_id: int
    consecutivo: int
    canal: str
    mesa_numero: int | None
    cliente: str | None
    telefono: str | None
    direccion: str | None
    nota_interna: str | None
    minutos_temporizador: int
    tiempo_excedido: bool
    segundos_transcurridos: int
    rondas: list[TicketRondaOut]