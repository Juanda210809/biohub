"""Conexión a Redis. Aquí va el patrón Decorator de la caché (HU-20): ConsultaCacheada."""
from functools import lru_cache

import redis

from app.config import REDIS_URL


@lru_cache
def cliente_redis():
    return redis.Redis.from_url(REDIS_URL, socket_connect_timeout=2)


def estado_cache() -> str:
    if not REDIS_URL:
        return "no configurada"
    try:
        cliente_redis().ping()
        return "ok"
    except redis.RedisError:
        return "sin conexion"
