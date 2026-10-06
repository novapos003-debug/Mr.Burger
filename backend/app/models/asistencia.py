from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class TurnoLaboral(Base):
    __tablename__ = "turno_laboral"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    rol = Column(String(50), nullable=False)
    entrada_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    salida_en = Column(DateTime(timezone=True), nullable=True)
    motivo_cierre = Column(String(50), nullable=True)  # MANUAL, CIERRE_CAJA, ADMIN
    es_demo = Column(Boolean, nullable=False, default=False, server_default="false", index=True)

    usuario = relationship("Usuario")
