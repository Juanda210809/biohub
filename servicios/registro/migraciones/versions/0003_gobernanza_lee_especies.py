"""Gobernanza puede leer el catálogo de especies (HU-08).

- Al reclasificar, Gobernanza necesita el nombre científico de la especie nueva para
  guardarlo en el historial (gobernanza.hallazgo_version) y en campo.hallazgo_publico.
- Solo lectura: Gobernanza no puede crear, cambiar ni borrar especies.
- No se edita la 0001 porque ya está en main.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-18
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("GRANT SELECT ON campo.especie TO svc_gobernanza")


def downgrade() -> None:
    op.execute("REVOKE SELECT ON campo.especie FROM svc_gobernanza")
