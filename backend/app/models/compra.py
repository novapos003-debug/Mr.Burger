from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Compra(Base):
    __tablename__ = "compra"

    id = Column(Integer, primary_key=True)
    proveedor_id = Column(Integer, ForeignKey("proveedor.id"))
    usuario_id = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    descripcion = Column(Text)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    proveedor = relationship("Proveedor")
    usuario = relationship("Usuario")
    detalles = relationship(
        "DetalleCompra",
        back_populates="compra",
        cascade="all, delete-orphan",
        order_by="DetalleCompra.id",
    )


class DetalleCompra(Base):
    __tablename__ = "detalle_compra"

    id = Column(Integer, primary_key=True)
    compra_id = Column(Integer, ForeignKey("compra.id", ondelete="CASCADE"), nullable=False)
    ingrediente_id = Column(Integer, ForeignKey("ingrediente.id"), nullable=False)
    cantidad = Column(Numeric(12, 4), nullable=False)
    costo_unitario = Column(Numeric(12, 4), nullable=False)
    costo_total = Column(Numeric(12, 4), nullable=False)

    compra = relationship("Compra", back_populates="detalles")
    ingrediente = relationship("Ingrediente")
