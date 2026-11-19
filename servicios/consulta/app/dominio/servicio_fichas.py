
"""Lógica de negocio para consultar fichas públicas."""

import json
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.cache import guardar_cache, obtener_cache
from app.repositorio.fichas import obtener_ficha_publica


def consultar_ficha_publica(sesion: Session, hallazgo_id: UUID):
    """Consulta una ficha pública utilizando Redis y PostgreSQL."""

    clave = f"ficha_publica:{hallazgo_id}"

    # 1. Buscar primero en Redis.
    ficha_cacheada = obtener_cache(clave)

    if ficha_cacheada is not None:
        return json.loads(ficha_cacheada)

    # 2. Si no está en Redis, consultar PostgreSQL.
    ficha = obtener_ficha_publica(sesion, hallazgo_id)

    if ficha is None:
        return None

    # 3. Normalizar los datos para obtener un JSON consistente.
    ficha_serializable = jsonable_encoder(ficha)

    ficha_json = json.dumps(
        ficha_serializable,
        ensure_ascii=False
    )

    # 4. Guardar la ficha durante 300 segundos.
    guardar_cache(clave, ficha_json)

    return ficha_serializable
