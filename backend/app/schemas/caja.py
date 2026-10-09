from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PagoIn(BaseModel):
    metodo: str = Field(pattern="^(EFECTIVO|TARJETA|TRANSFERENCIA|VALE|DIDI_TARJETA|DIDI_EFECTIVO)$")
    monto: Decimal = Field(gt=0)
    recibido: Decimal | None = Field(default=None, ge=0)  # solo efectivo (para calcular cambio)
    didi_orden_id: str | None = None  # para los métodos DIDI
    # Datos del pagaré cuando metodo == VALE
    vale_cliente_nombre: str | None = None
    vale_cliente_cedula: str | None = None
    vale_cliente_telefono: str | None = None


class CobroIn(BaseModel):
    pagos: list[PagoIn] = Field(min_length=1)


class PagoOut(BaseModel):
    id: int
    pedido_id: int
    metodo: str
    monto: Decimal
    recibido: Decimal | None
    cambio: Decimal | None
    didi_orden_id: str | None
    estado: str
    usuario_id: int | None
    pagado_en: datetime
    devuelto_en: datetime | None
    motivo_devolucion: str | None

    model_config = ConfigDict(from_attributes=True)


class ValeOut(BaseModel):
    id: int
    pedido_id: int
    cliente_nombre: str
    cliente_cedula: str | None
    cliente_telefono: str | None
    monto: Decimal
    estado: str
    cobrado_por: int | None
    cobrado_en: datetime | None
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)


class CobroOut(BaseModel):
    pedido_id: int
    consecutivo: int
    total: Decimal
    pagado: bool
    pagos: list[PagoOut]
    vales: list[ValeOut]


class DevolucionIn(BaseModel):
    motivo: str = Field(min_length=3, max_length=500)


class ValeCobroIn(BaseModel):
    descripcion: str | None = Field(default=None, max_length=500)


class MovimientoCajaOut(BaseModel):
    id: int
    usuario_id: int
    tipo: str
    categoria: str
    concepto: str
    descripcion: str
    valor: Decimal
    pedido_id: int | None
    vale_id: int | None
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)


class MovimientoCajaIn(BaseModel):
    tipo: str = Field(pattern="^(ENTRADA|SALIDA)$")
    categoria: str = Field(
        pattern="^(PAGO_TURNO|PRESTAMO|ADELANTO|PROVEEDOR|DEVOLUCION|COBRO_VALE|CAMBIO_INICIAL|GASTO_OPERATIVO|OTRO)$"
    )
    valor: Decimal = Field(gt=0)
    descripcion: str = Field(min_length=3, max_length=500)  # obligatoria (regla del dueño)
    concepto: str | None = Field(default=None, max_length=100)


class TurnoAperturaIn(BaseModel):
    monto_inicial: Decimal = Field(default=Decimal("0"), ge=0)


class CierreOut(BaseModel):
    id: int
    usuario_id: int
    usuario_nombre: str | None = None
    monto_inicial: Decimal = Decimal("0")
    abierto_en: datetime
    cerrado_en: datetime | None
    total_pedidos: int
    total_venta_comida: Decimal
    total_venta_bebida: Decimal
    total_efectivo: Decimal
    total_tarjeta: Decimal
    total_transferencia: Decimal
    total_vale: Decimal
    cantidad_vales: int
    total_didi_tarjeta: Decimal
    total_didi_efectivo: Decimal
    total_entradas_caja: Decimal
    total_salidas_caja: Decimal
    cantidad_egresos: int
    total_devoluciones: Decimal
    preparados_reutilizados: int
    preparados_descartados: int
    total_ventas: Decimal
    total_efectivo_final: Decimal
    total_por_cobrar: Decimal
    notas: str | None

    model_config = ConfigDict(from_attributes=True)


class CierreCerrarIn(BaseModel):
    notas: str | None = Field(default=None, max_length=1000)
