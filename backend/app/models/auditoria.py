from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class HistorialAccion(Base):
    """Bitácora de acciones: 'el historial es la ley' (nada se toca sin registro).

    Se escribe SIEMPRE dentro de la misma transacción de la operación que registra.
    """

    __tablename__ = "historial_accion"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuario.id"), index=True)
    accion = Column(String(100), nullable=False, index=True)
    entidad = Column(String(50))
    entidad_id = Column(Integer)
    detalle = Column(Text)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    usuario = relationship("Usuario")
