
"""Consultas de fichas p├║blicas en la base de datos."""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


def obtener_ficha_publica(sesion: Session, hallazgo_id: UUID):
    """Busca un hallazgo y devuelve ├║nicamente sus datos p├║blicos."""

    consulta = text("""
        SELECT
            hallazgo_id,
            especie,
            region,
            departamento,
            ecosistema,
            fecha_hallazgo,
            atributos_publicos,
            version,
            actualizado_en
        FROM campo.hallazgo_publico
        WHERE hallazgo_id = :hallazgo_id
    """)

    resultado = sesion.execute(
        consulta,
        {"hallazgo_id": hallazgo_id}
    ).mappings().first()

    if resultado is None:
        return None

    campos_publicos = {
        "hallazgo_id",
        "especie",
        "region",
        "departamento",
        "ecosistema",
        "fecha_hallazgo",
        "atributos_publicos",
        "version",
        "actualizado_en",
    }

    return {
        campo: valor
        for campo, valor in resultado.items()
        if campo in campos_publicos
    }
