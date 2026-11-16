
"""Conexión y operaciones de caché con Redis."""
from functools import lru_cache

import redis

from app.config import REDIS_URL

# Tiempo de vida de las fichas públicas: 5 minutos.
TIEMPO_CACHE = 300


@lru_cache
def cliente_redis():
    """Devuelve un cliente Redis reutilizable."""
    return redis.Redis.from_url(
        REDIS_URL,
        socket_connect_timeout=2,
        decode_responses=True
    )


def estado_cache() -> str:
    """Comprueba si Redis está disponible."""
    if not REDIS_URL:
        return "no configurada"

    try:
        cliente_redis().ping()
        return "ok"
    except redis.RedisError:
        return "sin conexion"


def obtener_cache(clave: str):
    """Recupera una ficha almacenada en Redis."""
    try:
        return cliente_redis().get(clave)
    except redis.RedisError:
        return None


def guardar_cache(clave: str, valor: str) -> bool:
    """Guarda una ficha en Redis durante 300 segundos."""
    try:
        cliente_redis().setex(clave, TIEMPO_CACHE, valor)
        return True
    except redis.RedisError:
        return False
