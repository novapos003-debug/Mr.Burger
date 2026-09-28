import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

raw_db_url = os.getenv(
    "DATABASE_URL",
    "postgresql://restaurante:restaurante_dev@localhost:5432/restaurante"
)
# Elimina cualquier salto de línea, retorno de carro o espacio accidental introducido al copiar/pegar
DATABASE_URL = "".join(raw_db_url.split())

connect_args = {}
if any(cloud_host in DATABASE_URL for cloud_host in ("supabase", "neon", "render", "aws")):
    connect_args["sslmode"] = "require"

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
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
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Conflicto de transaccion en base de datos: {str(e)}"
        )