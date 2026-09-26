from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Rol(Base):
    __tablename__ = "rol"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(30), unique=True, nullable=False)
    descripcion = Column(Text)

    usuarios = relationship("Usuario", back_populates="rol")


class Usuario(Base):
    __tablename__ = "usuario"

    id = Column(Integer, primary_key=True)
    rol_id = Column(Integer, ForeignKey("rol.id"), nullable=False)
    nombre = Column(String(100), nullable=False)
    usuario = Column(String(50), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    rol = relationship("Rol", back_populates="usuarios")