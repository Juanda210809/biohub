"""Crea las tablas de Identidad (HU-01) y los usuarios de demostración.

Revision ID: 0001
Revises:
Create Date: 2026-11-11
"""
from typing import Sequence, Union

import bcrypt
import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CONTRASENA_DEMO = "BioHub2026!"

USUARIOS_DEMO = [
    ("00000000-0000-0000-0000-0000000000aa", "Investigador Demo", "investigador@biohub.local", "INVESTIGADOR"),
    ("00000000-0000-0000-0000-0000000000ab", "Cientifico Demo", "cientifico@biohub.local", "CIENTIFICO_AUTORIZADO"),
    ("00000000-0000-0000-0000-0000000000ac", "Alto Rango Demo", "altorango@biohub.local", "ALTO_RANGO"),
    ("00000000-0000-0000-0000-0000000000ad", "Auditor Demo", "auditor@biohub.local", "AUDITOR"),
    ("00000000-0000-0000-0000-0000000000ae", "Administrador Demo", "admin@biohub.local", "ADMINISTRADOR"),
    ("00000000-0000-0000-0000-0000000000af", "Sin Rol Demo", "sinrol@biohub.local", None),
]


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE identidad.usuario (
            id               UUID PRIMARY KEY,
            nombre           TEXT NOT NULL CHECK (length(trim(nombre)) > 0),
            correo           TEXT NOT NULL,
            hash_contrasena  TEXT NOT NULL,
            rol              TEXT CHECK (rol IN ('INVESTIGADOR', 'CIENTIFICO_AUTORIZADO',
                                                 'ALTO_RANGO', 'AUDITOR', 'ADMINISTRADOR')),
            activo           BOOLEAN NOT NULL DEFAULT true,
            creado_en        TIMESTAMPTZ NOT NULL DEFAULT now(),
            actualizado_en   TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    # El correo es único sin importar mayúsculas: Ana@x.co y ana@x.co son la misma cuenta.
    op.execute("CREATE UNIQUE INDEX usuario_correo_unico ON identidad.usuario (lower(correo))")
    # Los usuarios no se borran, solo se desactivan (también para el dueño, svc_identidad).
    op.execute("REVOKE DELETE, TRUNCATE ON identidad.usuario FROM svc_identidad")

    op.execute(
        """
        CREATE TABLE identidad.sesion_revocada (
            jti          UUID PRIMARY KEY,
            usuario_id   UUID NOT NULL REFERENCES identidad.usuario (id),
            expira_en    TIMESTAMPTZ NOT NULL,
            revocada_en  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    insertar = sa.text(
        "INSERT INTO identidad.usuario (id, nombre, correo, hash_contrasena, rol) "
        "VALUES (CAST(:id AS uuid), :nombre, :correo, :hash, :rol)"
    )
    conexion = op.get_bind()
    for usuario_id, nombre, correo, rol in USUARIOS_DEMO:
        hash_contrasena = bcrypt.hashpw(CONTRASENA_DEMO.encode(), bcrypt.gensalt()).decode()
        conexion.execute(
            insertar,
            {"id": usuario_id, "nombre": nombre, "correo": correo, "hash": hash_contrasena, "rol": rol},
        )


def downgrade() -> None:
    op.execute("DROP TABLE identidad.sesion_revocada")
    op.execute("DROP TABLE identidad.usuario")

