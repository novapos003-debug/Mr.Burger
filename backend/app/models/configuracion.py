from sqlalchemy import Column, String, Text

from app.database import Base


class Configuracion(Base):
    """Tabla clave/valor del sistema: IVA, temporizador cocina, nombre del local, etc."""

    __tablename__ = "configuracion"

    clave = Column(String(50), primary_key=True)
    valor = Column(Text, nullable=False)
    descripcion = Column(Text)