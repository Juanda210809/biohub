"""Conexión a la base de datos con SQLAlchemy.

Uso dentro de una ruta:
    from app.db import obtener_sesion
    def mi_ruta(sesion = Depends(obtener_sesion)): ...
"""
from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from app.config import DATABASE_URL


@lru_cache
def motor():
    return create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"connect_timeout": 3})


def obtener_sesion():
    sesion = sessionmaker(bind=motor())()
    try:
        yield sesion
    finally:
        sesion.close()


def estado_bd() -> str:
    """Devuelve 'ok' si la base responde. Lo usa la ruta /salud."""
    if not DATABASE_URL:
        return "no configurada"
    try:
        with motor().connect() as conexion:
            conexion.execute(text("SELECT 1"))
        return "ok"
    except SQLAlchemyError:
        return "sin conexion"


def filas_publicas() -> int | None:
    """Cuántas filas tiene la copia de hallazgo_publico. Sirve para comprobar la replicación."""
    if not DATABASE_URL:
        return None
    try:
        with motor().connect() as conexion:
            return conexion.execute(text("SELECT count(*) FROM campo.hallazgo_publico")).scalar_one()
    except SQLAlchemyError:
        return None
