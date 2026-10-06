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
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
METODOS_PAGO = ("EFECTIVO", "TARJETA", "TRANSFERENCIA", "VALE", "DIDI_TARJETA", "DIDI_EFECTIVO")
CATEGORIAS_CAJA = (
    "PAGO_TURNO",
    "PRESTAMO",
    "ADELANTO",
    "PROVEEDOR",
    "DEVOLUCION",
    "COBRO_VALE",
    "CAMBIO_INICIAL",
    "OTRO",
)


class Cierre(Base):
    """Fotograma inmutable del turno de caja (se completa en la fase de cierre)."""

    __tablename__ = "cierre"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    abierto_en = Column(DateTime(timezone=True), nullable=False, index=True)
    cerrado_en = Column(DateTime(timezone=True))  # NULL mientras el turno está abierto
    total_pedidos = Column(Integer, nullable=False, default=0)
    total_venta_comida = Column(Numeric(12, 2), nullable=False, default=0)
    total_venta_bebida = Column(Numeric(12, 2), nullable=False, default=0)
    total_efectivo = Column(Numeric(12, 2), nullable=False, default=0)
    total_tarjeta = Column(Numeric(12, 2), nullable=False, default=0)
    total_transferencia = Column(Numeric(12, 2), nullable=False, default=0)
    total_vale = Column(Numeric(12, 2), nullable=False, default=0)
    cantidad_vales = Column(Integer, nullable=False, default=0)
    total_didi_tarjeta = Column(Numeric(12, 2), nullable=False, default=0)
    total_didi_efectivo = Column(Numeric(12, 2), nullable=False, default=0)
    total_entradas_caja = Column(Numeric(12, 2), nullable=False, default=0)
    total_salidas_caja = Column(Numeric(12, 2), nullable=False, default=0)
    cantidad_egresos = Column(Integer, nullable=False, default=0)
    total_devoluciones = Column(Numeric(12, 2), nullable=False, default=0)
    preparados_reutilizados = Column(Integer, nullable=False, default=0)
    preparados_descartados = Column(Integer, nullable=False, default=0)
    total_ventas = Column(Numeric(12, 2), nullable=False, default=0)
    total_efectivo_final = Column(Numeric(12, 2), nullable=False, default=0)
    total_por_cobrar = Column(Numeric(12, 2), nullable=False, default=0)
    notas = Column(Text)
    es_demo = Column(Boolean, nullable=False, default=False, server_default="false", index=True)


class Pago(Base):
    """Cobro de un pedido. Regla del cliente: identidad subtotal + iva = total;
    el efectivo calcula cambio; vale crea un pagaré; DiDi tarjeta queda por cobrar."""

    __tablename__ = "pago"

    id = Column(Integer, primary_key=True)
    pedido_id = Column(Integer, ForeignKey("pedido.id"), nullable=False)
    cierre_id = Column(Integer, ForeignKey("cierre.id"), index=True)
    metodo = Column(String(20), nullable=False)
    monto = Column(Numeric(12, 2), nullable=False)
    recibido = Column(Numeric(12, 2))
    cambio = Column(Numeric(12, 2))
    didi_orden_id = Column(String(50))
    estado = Column(String(15), nullable=False, default="VALIDO")
    usuario_id = Column(Integer, ForeignKey("usuario.id"))
    devuelto_por = Column(Integer, ForeignKey("usuario.id"))
    devuelto_en = Column(DateTime(timezone=True))
    motivo_devolucion = Column(Text)
    pagado_en = Column(DateTime(timezone=True), server_default=func.now())
    es_demo = Column(Boolean, nullable=False, default=False, server_default="false", index=True)

    pedido = relationship("Pedido", back_populates="pagos")
    usuario = relationship("Usuario", foreign_keys=[usuario_id])
    devuelto_usuario = relationship("Usuario", foreign_keys=[devuelto_por])

    __table_args__ = (
        CheckConstraint(
            "metodo IN ('EFECTIVO','TARJETA','TRANSFERENCIA','VALE','DIDI_TARJETA','DIDI_EFECTIVO')",
            name="ck_pago_metodo",
        ),
        CheckConstraint("estado IN ('VALIDO','DEVUELTO')", name="ck_pago_estado"),
    )


class Vale(Base):
    """Pagaré de persona de confianza: queda PENDIENTE hasta que se cobra en caja."""

    __tablename__ = "vale"

    id = Column(Integer, primary_key=True)
    pedido_id = Column(Integer, ForeignKey("pedido.id"), nullable=False)
    cliente_nombre = Column(String(100), nullable=False)
    cliente_cedula = Column(String(20))
    cliente_telefono = Column(String(30))
    monto = Column(Numeric(12, 2), nullable=False)
    estado = Column(String(15), nullable=False, default="PENDIENTE")
    cobrado_por = Column(Integer, ForeignKey("usuario.id"))
    cobrado_en = Column(DateTime(timezone=True))
    es_demo = Column(Boolean, nullable=False, default=False, server_default="false", index=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    pedido = relationship("Pedido")
    usuario = relationship("Usuario", foreign_keys=[cobrado_por])

    __table_args__ = (
        CheckConstraint("estado IN ('PENDIENTE','COBRADO')", name="ck_vale_estado"),
    )


class MovimientoCaja(Base):
    """Entradas/salidas de dinero. La descripción es obligatoria (regla del dueño)."""

    __tablename__ = "movimiento_caja"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    tipo = Column(String(10), nullable=False)
    categoria = Column(String(20), nullable=False)
    concepto = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=False)
    valor = Column(Numeric(12, 2), nullable=False)
    pedido_id = Column(Integer, ForeignKey("pedido.id"))
    vale_id = Column(Integer, ForeignKey("vale.id"))
    cierre_id = Column(Integer, ForeignKey("cierre.id"), index=True)
    es_demo = Column(Boolean, nullable=False, default=False, server_default="false", index=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    usuario = relationship("Usuario")
    pedido = relationship("Pedido")
    vale = relationship("Vale")

    __table_args__ = (
        CheckConstraint("tipo IN ('ENTRADA','SALIDA')", name="ck_movcaja_tipo"),
        CheckConstraint(
            "categoria IN ('PAGO_TURNO','PRESTAMO','ADELANTO','PROVEEDOR','DEVOLUCION','COBRO_VALE','CAMBIO_INICIAL','GASTO_OPERATIVO','OTRO')",
            name="ck_movcaja_categoria",
        ),
    )
