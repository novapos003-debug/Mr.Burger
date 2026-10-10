import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

# Orden: variable de entorno -> archivo .env -> base local por defecto de la caja
raw_db_url = (
    os.getenv("DATABASE_URL")
    or settings.DATABASE_URL
    or "postgresql://restaurante:restaurante_dev@127.0.0.1:5432/restaurante"
)
# Elimina cualquier salto de línea, retorno de carro o espacio accidental introducido al copiar/pegar
DATABASE_URL = "".join(raw_db_url.split())

# 1. Normalizar 'localhost' a '127.0.0.1' para evitar el fallo de resolución IPv6 (::1) en Windows
if "@localhost:" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("@localhost:", "@127.0.0.1:")

# 2. Si apunta a 127.0.0.1:5432 pero el puerto 5432 está cerrado y el 5433 está abierto, autoconmutar a 5433
if "@127.0.0.1:5432/" in DATABASE_URL:
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.2)
            if s.connect_ex(("127.0.0.1", 5432)) != 0:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
                    s2.settimeout(0.2)
                    if s2.connect_ex(("127.0.0.1", 5433)) == 0:
                        DATABASE_URL = DATABASE_URL.replace("@127.0.0.1:5432/", "@127.0.0.1:5433/")
    except Exception:
        pass

is_sqlite = DATABASE_URL.startswith("sqlite")
connect_args = {}
if not is_sqlite:
    connect_args["client_encoding"] = "utf8"
if any(cloud_host in DATABASE_URL for cloud_host in ("supabase", "neon", "render", "aws")):
    connect_args["sslmode"] = "require"

import logging

logger = logging.getLogger(__name__)
engine_kwargs = {
    "pool_pre_ping": True,
}
en_nube_gestionada = any(h in DATABASE_URL for h in ("supabase", "neon", "render", "aws"))
if not is_sqlite:
    engine_kwargs.update({
        # El pooler de Supabase admite pocas conexiones por cliente en el plan gratuito: si se
        # piden de más responde "max clients reached". En la caja (PostgreSQL propio) no hay ese límite.
        "pool_size": 5 if en_nube_gestionada else 15,
        "max_overflow": 5 if en_nube_gestionada else 10,
        "pool_timeout": 30,
        "pool_recycle": 1800,
    })

engine = create_engine(DATABASE_URL, connect_args=connect_args, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

def safe_commit(db):
    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Error en safe_commit DB: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflicto de integridad o concurrencia en base de datos. Verifique los datos o reintente."
        )