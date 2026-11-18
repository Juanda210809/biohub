"""Crea identidad.cambio_rol: quién le cambió el rol a quién y cuándo (HU-02).

Es de solo inserción: el historial de roles no se modifica ni se borra.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-18
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE identidad.cambio_rol (
            id            UUID PRIMARY KEY,
            usuario_id    UUID NOT NULL REFERENCES identidad.usuario (id),
            rol_anterior  TEXT,
            rol_nuevo     TEXT,
            actor_id      UUID NOT NULL REFERENCES identidad.usuario (id),
            instante      TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("REVOKE UPDATE, DELETE, TRUNCATE ON identidad.cambio_rol FROM svc_identidad")


def downgrade() -> None:
    op.execute("DROP TABLE identidad.cambio_rol")
