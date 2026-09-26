from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# ---------- DASHBOARD ----------
class TopProductoItem(BaseModel):
    producto_id: int
    nombre: str
    cantidad: Decimal
    total: Decimal


class AlertaStockItem(BaseModel):
    ingrediente_id: int
    nombre: str
    unidad_base: str
    stock_actual: Decimal
    stock_minimo: Decimal
    deficit: Decimal
    costo_unitario: Decimal
    costo_reabastecer: Decimal
    proveedor_nombre: str | None = None


class DashboardOut(BaseModel):
    fecha: date
    total_ventas: Decimal
    total_pedidos: int
    ticket_promedio: Decimal
    pedidos_por_estado: dict[str, int]
    ventas_por_canal: dict[str, Decimal]
    ventas_por_tipo: dict[str, Decimal]
    pagos_por_metodo: dict[str, Decimal]
    entradas_caja: Decimal
    salidas_caja: Decimal
    devoluciones_caja: Decimal
    vales_pendientes_monto: Decimal
    vales_pendientes_cantidad: int
    preparados_disponibles_count: int
    top_productos: list[TopProductoItem]
    alertas_stock: list[AlertaStockItem]


# ---------- REPORTES ----------
class DesgloseDiaItem(BaseModel):
    fecha: date
    pedidos_count: int
    subtotal: Decimal
    iva: Decimal
    total: Decimal


class ReporteVentasOut(BaseModel):
    desde: date
    hasta: date
    total_ventas: Decimal
    total_pedidos: int
    ticket_promedio: Decimal
    ventas_por_canal: dict[str, Decimal]
    desglose_diario: list[DesgloseDiaItem]


# ---------- COMPRAS / PROVEEDORES ----------
class DetalleCompraIn(BaseModel):
    ingrediente_id: int
    cantidad: Decimal = Field(gt=0)
    costo_unitario: Decimal = Field(ge=0)


class CompraIn(BaseModel):
    proveedor_id: int | None = None
    descripcion: str | None = Field(default=None, max_length=500)
    detalles: list[DetalleCompraIn] = Field(min_length=1)


class DetalleCompraOut(BaseModel):
    id: int
    ingrediente_id: int
    ingrediente_nombre: str | None = None
    cantidad: Decimal
    costo_unitario: Decimal
    costo_total: Decimal

    model_config = ConfigDict(from_attributes=True)


class CompraOut(BaseModel):
    id: int
    proveedor_id: int | None
    proveedor_nombre: str | None = None
    usuario_id: int
    usuario_nombre: str | None = None
    descripcion: str | None
    costo_total: Decimal
    creado_en: datetime
    detalles: list[DetalleCompraOut]

    model_config = ConfigDict(from_attributes=True)


# ---------- AUDITORIA ----------
class HistorialAccionOut(BaseModel):
    id: int
    usuario_id: int | None
    usuario_nombre: str | None = None
    accion: str
    entidad: str | None
    entidad_id: int | None
    detalle: str | None
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- USUARIOS Y SEGURIDAD ----------
class UsuarioAdminOut(BaseModel):
    id: int
    nombre: str
    usuario: str
    rol_id: int
    rol: str
    activo: bool
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)


class UsuarioCreateIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    usuario: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=4, max_length=100)
    rol: str = Field(pattern="^(admin|cajero|mesero|cocina)$")


class UsuarioPasswordUpdateIn(BaseModel):
    nueva_password: str = Field(min_length=4, max_length=100)


class CambiarMiPasswordIn(BaseModel):
    password_actual: str = Field(min_length=1)
    nueva_password: str = Field(min_length=4, max_length=100)


class UsuarioEstadoUpdateIn(BaseModel):
    activo: bool
