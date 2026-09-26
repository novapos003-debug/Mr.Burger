from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.tiempo import fecha_local
from app.database import Base


class Mesa(Base):
    __tablename__ = "mesa"

    id = Column(Integer, primary_key=True)
    numero = Column(Integer, unique=True, nullable=False)
    estado = Column(String(20), nullable=False, default="DISPONIBLE")
    activo = Column(Boolean, nullable=False, default=True)

    pedidos = relationship("Pedido", back_populates="mesa")

    __table_args__ = (
        CheckConstraint("estado IN ('DISPONIBLE','EN_CURSO','OCUPADA')", name="ck_mesa_estado"),
    )


class Pedido(Base):
    __tablename__ = "pedido"

    id = Column(Integer, primary_key=True)
    consecutivo = Column(Integer, nullable=False)
    fecha_dia = Column(Date, nullable=False, default=fecha_local)
    canal = Column(String(20), nullable=False)
    mesa_id = Column(Integer, ForeignKey("mesa.id"))
    usuario_id = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    estado = Column(String(25), nullable=False, default="NUEVO")
    cliente = Column(String(100))
    telefono = Column(String(30))
    direccion = Column(Text)
    nota_interna = Column(Text)
    didi_orden_id = Column(String(50))
    subtotal = Column(Numeric(12, 2), nullable=False, default=0)
    iva = Column(Numeric(12, 2), nullable=False, default=0)
    total = Column(Numeric(12, 2), nullable=False, default=0)
    motivo_cancelacion = Column(Text)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    enviado_en = Column(DateTime(timezone=True))
    finalizado_en = Column(DateTime(timezone=True))
    pagado_en = Column(DateTime(timezone=True))
    cancelado_en = Column(DateTime(timezone=True))

    mesa = relationship("Mesa", back_populates="pedidos")
    usuario = relationship("Usuario")
    detalles = relationship(
        "DetallePedido", back_populates="pedido", cascade="all, delete-orphan", order_by="DetallePedido.id"
    )
    pagos = relationship("Pago", back_populates="pedido", order_by="Pago.id")

    __table_args__ = (
        UniqueConstraint("fecha_dia", "consecutivo", name="uq_pedido_fecha_dia_consecutivo"),
        CheckConstraint(
            "canal IN ('MESA','MOSTRADOR','DIDI','DOMICILIO')", name="ck_pedido_canal"
        ),
        CheckConstraint(
            "estado IN ('NUEVO','ENVIADO_A_COCINA','EN_PREPARACION','FINALIZADO','ENTREGADO','PAGADO','CERRADO','CANCELADO')",
            name="ck_pedido_estado",
        ),
    )


class DetallePedido(Base):
    __tablename__ = "detalle_pedido"

    id = Column(Integer, primary_key=True)
    pedido_id = Column(Integer, ForeignKey("pedido.id", ondelete="CASCADE"), nullable=False)
    ronda = Column(Integer, nullable=False, default=1)
    producto_id = Column(Integer, ForeignKey("producto.id"), nullable=False)
    cantidad = Column(Numeric(10, 2), nullable=False, default=1)
    precio_unitario = Column(Numeric(12, 2), nullable=False)
    variacion_snapshot = Column(JSONB)
    estado = Column(String(20), nullable=False, default="ENVIADO")
    preparado_en = Column(DateTime(timezone=True))
    listo_en = Column(DateTime(timezone=True))
    entregado_en = Column(DateTime(timezone=True))
    cancelado_en = Column(DateTime(timezone=True))

    pedido = relationship("Pedido", back_populates="detalles")
    producto = relationship("Producto")

    __table_args__ = (
        CheckConstraint(
            "estado IN ('ENVIADO','PREPARANDO','LISTO','ENTREGADO','CANCELADO')",
            name="ck_detalle_pedido_estado",
        ),
    )