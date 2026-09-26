from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.database import Base


class RegistroSync(Base):
    __tablename__ = "registro_sync"

    id = Column(Integer, primary_key=True)
    op_id = Column(String(64), unique=True, nullable=False, index=True)
    sucursal_id = Column(String(20), nullable=False, default="SUC-01")
    dispositivo_id = Column(String(50), nullable=False, index=True)
    tipo = Column(String(50), nullable=False)
    entidad = Column(String(50), nullable=False)
    entidad_id = Column(Integer)
    entidad_uuid = Column(String(64))
    payload = Column(JSONB, nullable=False)
    origen = Column(String(10), nullable=False, default="LOCAL")
    estado = Column(String(20), nullable=False, default="APLICADO")
    reintentos = Column(Integer, nullable=False, default=0)
    ultimo_error = Column(Text)
    resolucion_nota = Column(Text)
    creado_en = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    sincronizado_en = Column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint("origen IN ('LOCAL','NUBE')", name="ck_sync_origen"),
        CheckConstraint("estado IN ('PENDIENTE','APLICADO','CONFLICTO','ERROR')", name="ck_sync_estado"),
    )
