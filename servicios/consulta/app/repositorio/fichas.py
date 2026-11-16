
"""Consultas de fichas públicas en la base de datos."""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


def obtener_ficha_publica(sesion: Session, hallazgo_id: UUID):
    """Busca un hallazgo y devuelve sus datos públicos."""

    consulta = text("""
        SELECT
            hallazgo_id,
            especie,
            region,
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
