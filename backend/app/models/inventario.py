from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class MovimientoInventario(Base):
    """Historial de entradas/salidas de insumos. Fuente de verdad del inventario.

    La regla del cliente: el stock se descuenta cuando la cocina ACEPTA el detalle
    (no al enviar ni al pagar). Tipo VENTA = salida por producción de un pedido.
    """

    __tablename__ = "movimiento_inventario"

    id = Column(Integer, primary_key=True)
    ingrediente_id = Column(Integer, ForeignKey("ingrediente.id"), nullable=False)
    pedido_id = Column(Integer, ForeignKey("pedido.id"))
    compra_id = Column(Integer)  # FK a compra se agrega en la fase de compras
    usuario_id = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    cantidad = Column(Numeric(12, 4), nullable=False)  # NEGATIVO = salida (venta); POSITIVO = entrada (compra)
    unidad = Column(String(20), default="u")
    saldo_anterior = Column(Numeric(12, 4))
    saldo_nuevo = Column(Numeric(12, 4))
    costo_unitario_momento = Column(Numeric(12, 4))
    tipo = Column(String(20), nullable=False)
    referencia = Column(Text)
    es_demo = Column(Boolean, nullable=False, default=False, server_default="false", index=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    ingrediente = relationship("Ingrediente")
    pedido = relationship("Pedido")

    __table_args__ = (
        CheckConstraint(
            "tipo IN ('VENTA','COMPRA','MERMA','AJUSTE','DEVOLUCION','DESPERDICIO')",
            name="ck_movimiento_inventario_tipo",
        ),
    )