"""Agrega a campo.revision_ficha quién publicó cada revisión (HU-04).

- La arquitectura dice que cada revisión queda asociada al usuario que la publicó.
- La columna admite NULL: las dos revisiones de ejemplo de la 0001 no tienen autor.
- No se edita la 0001 porque ya está en main.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-16
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE campo.revision_ficha ADD COLUMN publicada_por UUID")


def downgrade() -> None:
    op.execute("ALTER TABLE campo.revision_ficha DROP COLUMN publicada_por")
