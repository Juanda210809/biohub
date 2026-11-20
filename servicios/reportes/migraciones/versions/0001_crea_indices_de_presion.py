"""Crea las tablas de HU-15 en el esquema reportes (base BD Reportes).

- reportes.ejecucion_indices: cada vez que se generan los índices de un mes (quién y cuándo).
- reportes.indice_presion: el índice de cada ecosistema en cada mes. Recalcular un mes reemplaza
  sus filas: son datos derivados de campo.hallazgo_publico y se pueden volver a calcular.
- Se calcula sobre la COPIA de hallazgo_publico que llega por replicación: nunca toca la base
  operacional, así generar el reporte no frena el registro de hallazgos (RNF-04).

Revision ID: 0001
Revises:
Create Date: 2026-11-20
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE reportes.ejecucion_indices (
            id              UUID PRIMARY KEY,
            periodo         DATE NOT NULL CHECK (extract(day FROM periodo) = 1),
            origen          TEXT NOT NULL CHECK (origen IN ('AUTOMATICO', 'MANUAL')),
            solicitado_por  UUID,
            generado_en     TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
            CONSTRAINT ejecucion_manual_con_autor CHECK (origen = 'AUTOMATICO' OR solicitado_por IS NOT NULL)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE reportes.indice_presion (
            periodo             DATE NOT NULL,
            ecosistema          TEXT NOT NULL,
            hallazgos           INTEGER NOT NULL CHECK (hallazgos >= 0),
            especies_distintas  INTEGER NOT NULL CHECK (especies_distintas >= 0),
            promedio_previo     NUMERIC(10, 2) NOT NULL,
            indice              NUMERIC(10, 2),
            nivel               TEXT NOT NULL CHECK (nivel IN ('SIN_HISTORIA', 'BAJA', 'NORMAL', 'ALTA')),
            ejecucion_id        UUID NOT NULL REFERENCES reportes.ejecucion_indices (id),
            PRIMARY KEY (periodo, ecosistema)
        )
        """
    )
    op.execute("CREATE INDEX ejecucion_por_periodo ON reportes.ejecucion_indices (periodo, generado_en DESC)")


def downgrade() -> None:
    op.execute("DROP TABLE reportes.indice_presion")
    op.execute("DROP TABLE reportes.ejecucion_indices")
