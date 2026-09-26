from decimal import Decimal
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class TipoCategoria(Base):
    __tablename__ = "tipo_categoria"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(20), unique=True, nullable=False)

    categorias = relationship("Categoria", back_populates="tipo")


class Categoria(Base):
    __tablename__ = "categoria"

    id = Column(Integer, primary_key=True)
    tipo_id = Column(Integer, ForeignKey("tipo_categoria.id"), nullable=False)
    nombre = Column(String(50), nullable=False)
    orden = Column(Integer, nullable=False, default=0)
    activo = Column(Boolean, nullable=False, default=True)

    tipo = relationship("TipoCategoria", back_populates="categorias")
    productos = relationship(
        "Producto", back_populates="categoria", order_by="Producto.nombre"
    )


class Producto(Base):
    __tablename__ = "producto"

    id = Column(Integer, primary_key=True)
    categoria_id = Column(Integer, ForeignKey("categoria.id"), nullable=False)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    imagen_url = Column(Text)
    precio = Column(Numeric(12, 2), nullable=False, default=0)
    iva_incluido = Column(Boolean, nullable=False, default=True)
    manual_disponible = Column(Boolean)  # NULL=auto por stock, TRUE/FALSE=forzado
    activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    categoria = relationship("Categoria", back_populates="productos")
    receta = relationship(
        "DetalleReceta",
        back_populates="producto",
        cascade="all, delete-orphan",
        order_by="DetalleReceta.id",
    )
    componentes_combo = relationship(
        "ComponenteCombo",
        foreign_keys="ComponenteCombo.combo_producto_id",
        back_populates="combo_producto",
        cascade="all, delete-orphan",
    )


class Proveedor(Base):
    __tablename__ = "proveedor"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    contacto = Column(String(100))
    telefono = Column(String(30))
    activo = Column(Boolean, nullable=False, default=True)

    ingredientes = relationship("Ingrediente", back_populates="proveedor")


class CategoriaInsumo(Base):
    """Categorías para agrupar materias primas / insumos (Carnes, Verduras, Lácteos, etc.)"""
    __tablename__ = "categoria_insumo"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)
    activo = Column(Boolean, nullable=False, default=True)

    ingredientes = relationship("Ingrediente", back_populates="categoria_insumo")


class Ingrediente(Base):
    __tablename__ = "ingrediente"

    id = Column(Integer, primary_key=True)
    categoria_insumo_id = Column(Integer, ForeignKey("categoria_insumo.id"))
    nombre = Column(String(100), nullable=False)
    unidad_base = Column(String(20), nullable=False)
    costo_unitario = Column(Numeric(12, 4), nullable=False, default=0)
    costo_proveedor = Column(Text)
    stock_actual = Column(Numeric(12, 4), nullable=False, default=0)
    stock_minimo = Column(Numeric(12, 4), nullable=False, default=0)
    stock_ideal = Column(Numeric(12, 4))
    proveedor_id = Column(Integer, ForeignKey("proveedor.id"))
    activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    proveedor = relationship("Proveedor", back_populates="ingredientes")
    categoria_insumo = relationship("CategoriaInsumo", back_populates="ingredientes")
    receta = relationship("DetalleReceta", back_populates="ingrediente")

    __table_args__ = (
        CheckConstraint(
            "unidad_base IN ('GRAMO','MILILITRO','UNIDAD','LONJA','PORCION','PAQUETE')",
            name="ck_ingrediente_unidad_base",
        ),
    )


class DetalleReceta(Base):
    __tablename__ = "detalle_receta"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("producto.id", ondelete="CASCADE"), nullable=False)
    ingrediente_id = Column(Integer, ForeignKey("ingrediente.id"), nullable=False)
    cantidad = Column(Numeric(12, 4), nullable=False)
    unidad = Column(String(20), nullable=False)

    producto = relationship("Producto", back_populates="receta")
    ingrediente = relationship("Ingrediente", back_populates="receta")

    __table_args__ = (
        UniqueConstraint("product_id", "ingrediente_id", name="uq_detalle_receta_producto_ingrediente"),
    )


class ComponenteCombo(Base):
    """Permite que un producto compuesto / combo contenga múltiples productos simples."""
    __tablename__ = "componente_combo"

    id = Column(Integer, primary_key=True)
    combo_producto_id = Column(Integer, ForeignKey("producto.id", ondelete="CASCADE"), nullable=False)
    producto_hijo_id = Column(Integer, ForeignKey("producto.id", ondelete="CASCADE"), nullable=False)
    cantidad = Column(Numeric(10, 2), nullable=False, default=1)

    combo_producto = relationship("Producto", foreign_keys=[combo_producto_id], back_populates="componentes_combo")
    producto_hijo = relationship("Producto", foreign_keys=[producto_hijo_id])

    __table_args__ = (
        UniqueConstraint("combo_producto_id", "producto_hijo_id", name="uq_componente_combo_hijo"),
    )