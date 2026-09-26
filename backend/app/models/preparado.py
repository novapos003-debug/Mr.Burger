from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Preparado(Base):
    __tablename__ = "preparado"

    id = Column(Integer, primary_key=True)
    producto_id = Column(Integer, ForeignKey("producto.id"), nullable=False)
    pedido_origen_id = Column(Integer, ForeignKey("pedido.id"), nullable=False)
    detalle_origen_id = Column(Integer, ForeignKey("detalle_pedido.id"), nullable=False)
    variacion_snapshot = Column(JSONB)
    cantidad = Column(Numeric(10, 2), nullable=False, default=1)
    estado = Column(String(15), nullable=False, default="DISPONIBLE")
    pedido_nuevo_id = Column(Integer, ForeignKey("pedido.id"))
    usuario_id = Column(Integer, ForeignKey("usuario.id"))
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    asignado_en = Column(DateTime(timezone=True))
    descartado_en = Column(DateTime(timezone=True))
    motivo_descarte = Column(Text)

    producto = relationship("Producto")
    pedido_origen = relationship("Pedido", foreign_keys=[pedido_origen_id])
    detalle_origen = relationship("DetallePedido", foreign_keys=[detalle_origen_id])
    pedido_nuevo = relationship("Pedido", foreign_keys=[pedido_nuevo_id])
    usuario = relationship("Usuario", foreign_keys=[usuario_id])

    __table_args__ = (
        CheckConstraint(
            "estado IN ('DISPONIBLE','ASIGNADO','DESCARTADO')",
            name="ck_preparado_estado",
        ),
    )
