import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

raw_db_url = os.getenv(
    "DATABASE_URL",
    "postgresql://restaurante:restaurante_dev@localhost:5432/restaurante"
)
# Elimina cualquier salto de línea, retorno de carro o espacio accidental introducido al copiar/pegar
DATABASE_URL = "".join(raw_db_url.split())

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
if not is_sqlite:
    engine_kwargs.update({
        "pool_size": 15,
        "max_overflow": 10,
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