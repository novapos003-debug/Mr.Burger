from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TipoCategoriaOut(BaseModel):
    id: int
    nombre: str

    model_config = ConfigDict(from_attributes=True)


class CategoriaIn(BaseModel):
    tipo_id: int
    nombre: str = Field(min_length=1, max_length=50)
    orden: int = 0


class CategoriaUpdate(BaseModel):
    tipo_id: int | None = None
    nombre: str | None = Field(default=None, min_length=1, max_length=50)
    orden: int | None = None


class CategoriaOut(BaseModel):
    id: int
    tipo_id: int
    nombre: str
    orden: int
    activo: bool

    model_config = ConfigDict(from_attributes=True)


class ProductoIn(BaseModel):
    categoria_id: int
    nombre: str = Field(min_length=1, max_length=100)
    descripcion: str | None = None
    precio: Decimal = Field(ge=0)
    iva_incluido: bool = True
    empaque_llevar_id: int | None = None
    permite_adiciones: bool = True
    imagen_url: str | None = None
    manual_disponible: bool | None = None


class ProductoUpdate(BaseModel):
    categoria_id: int | None = None
    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    descripcion: str | None = None
    precio: Decimal | None = Field(default=None, ge=0)
    iva_incluido: bool | None = None
    empaque_llevar_id: int | None = None
    permite_adiciones: bool | None = None
    imagen_url: str | None = None
    manual_disponible: bool | None = None


from datetime import datetime


class CategoriaInsumoIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=50)
    descripcion: str | None = None


class CategoriaInsumoOut(BaseModel):
    id: int
    nombre: str
    descripcion: str | None = None
    activo: bool

    model_config = ConfigDict(from_attributes=True)


class ComponenteComboIn(BaseModel):
    producto_hijo_id: int
    cantidad: Decimal = Field(default=Decimal("1"), gt=0)


class ComponenteComboOut(BaseModel):
    id: int
    producto_hijo_id: int
    producto_hijo_nombre: str
    cantidad: Decimal
    precio_unitario: Decimal

    model_config = ConfigDict(from_attributes=True)


class ProductoDisponibilidadUpdate(BaseModel):
    manual_disponible: bool | None = None


class ProductoOut(BaseModel):
    id: int
    categoria_id: int
    nombre: str
    descripcion: str | None
    imagen_url: str | None
    precio: Decimal | None  # None para mesero/cocina (NO ven dinero)
    iva_incluido: bool
    empaque_llevar_id: int | None = None
    permite_adiciones: bool = True
    disponible: bool
    activo: bool
    es_cocina: bool = True
    ingredientes_receta: list[str] = []
    # Finanzas de receta (visibles solo cuando se autoriza ver dinero / admin)
    costo_produccion: Decimal | None = None
    utilidad_bruta: Decimal | None = None
    margen_porcentaje: Decimal | None = None
    es_combo: bool = False
    componentes_combo: list[ComponenteComboOut] = []


class IngredienteIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    categoria_insumo_id: int | None = None
    unidad_base: str = Field(pattern="^(GRAMO|MILILITRO|UNIDAD|LONJA|PORCION|PAQUETE)$")
    costo_unitario: Decimal = 0
    costo_proveedor: str | None = None
    stock_actual: Decimal = 0
    stock_minimo: Decimal = 0
    stock_ideal: Decimal | None = None
    proveedor_id: int | None = None


class IngredienteUpdate(BaseModel):
    nombre: str | None = None
    categoria_insumo_id: int | None = None
    unidad_base: str | None = None
    costo_unitario: Decimal | None = None
    costo_proveedor: str | None = None
    stock_actual: Decimal | None = None
    stock_minimo: Decimal | None = None
    stock_ideal: Decimal | None = None
    proveedor_id: int | None = None


class IngredienteOut(BaseModel):
    id: int
    categoria_insumo_id: int | None = None
    categoria_insumo_nombre: str | None = None
    nombre: str
    unidad_base: str
    costo_unitario: Decimal
    costo_proveedor: str | None
    stock_actual: Decimal
    stock_minimo: Decimal
    stock_ideal: Decimal | None
    proveedor_id: int | None
    proveedor_nombre: str | None = None
    stock_bajo: bool  # stock_actual < stock_minimo (alerta a admin)
    activo: bool

    model_config = ConfigDict(from_attributes=True)


class DetalleRecetaIn(BaseModel):
    ingrediente_id: int
    cantidad: Decimal = Field(gt=0)
    unidad: str = Field(min_length=1, max_length=20)


class RecetaOut(BaseModel):
    ingrediente_id: int
    ingrediente_nombre: str
    cantidad: Decimal
    unidad: str
    unidad_base: str
    costo_unitario: Decimal | None = None
    costo_total: Decimal | None = None


class MovimientoInventarioOut(BaseModel):
    id: int
    ingrediente_id: int
    ingrediente_nombre: str | None = None
    pedido_id: int | None = None
    compra_id: int | None = None
    usuario_id: int
    usuario_nombre: str | None = None
    cantidad: Decimal
    unidad: str | None = "u"
    saldo_anterior: Decimal | None = None
    saldo_nuevo: Decimal | None = None
    costo_unitario_momento: Decimal | None = None
    tipo: str
    referencia: str | None = None
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)


class DisponibilidadOut(BaseModel):
    id: int
    nombre: str
    disponible: bool
    motivo: str | None = None