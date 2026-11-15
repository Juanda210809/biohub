
"""Consultas de fichas públicas en la base de datos """

from sqlalchemy import text
from sqlalchemy.orm import Session
from uuid import UUID


def obtener_ficha_publica(sesion: Session, hallazgo_id: UUID):

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

    return dict(resultado)
