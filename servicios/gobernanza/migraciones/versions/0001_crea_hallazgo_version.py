"""Crea gobernanza.hallazgo_version: el historial de versiones de cada hallazgo.

- Registro (svc_registro) solo puede AGREGAR la versión 1 cuando se crea un hallazgo (HU-03).
- Gobernanza agrega las versiones 2, 3... al reclasificar (HU-08).
- Nadie actualiza ni borra filas, ni siquiera Gobernanza: el historial nunca se pierde (HU-08, HU-12).
- Sin llave foránea hacia campo.hallazgo: las migraciones de Registro y Gobernanza
  arrancan al mismo tiempo y no se garantiza cuál termina primero.

Revision ID: 0001
Revises:
Create Date: 2026-11-08
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
        CREATE TABLE gobernanza.hallazgo_version (
            id             UUID PRIMARY KEY,
            hallazgo_id    UUID NOT NULL,
            numero         INTEGER NOT NULL CHECK (numero >= 1),
            especie        TEXT NOT NULL,
            atributos      JSONB NOT NULL DEFAULT '{}'::jsonb,
            autor_id       UUID NOT NULL,
            justificacion  TEXT NOT NULL CHECK (length(trim(justificacion)) > 0),
            vigente_desde  TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT hallazgo_version_unica UNIQUE (hallazgo_id, numero)
        )
        """
    )
    # Para HU-12: buscar rápido la versión vigente de un hallazgo en una fecha.
    op.execute(
        "CREATE INDEX hallazgo_version_por_fecha "
        "ON gobernanza.hallazgo_version (hallazgo_id, vigente_desde)"
    )

    # El historial es de solo inserción, también para el dueño (svc_gobernanza).
    op.execute("REVOKE UPDATE, DELETE, TRUNCATE ON gobernanza.hallazgo_version FROM svc_gobernanza")

    # Registro puede entrar al esquema y AGREGAR la versión 1. No puede leer, cambiar ni borrar.
    op.execute("GRANT USAGE ON SCHEMA gobernanza TO svc_registro")
    op.execute(
        "GRANT INSERT (id, hallazgo_id, numero, especie, atributos, autor_id, justificacion) "
        "ON gobernanza.hallazgo_version TO svc_registro"
    )
    # Solo la versión 1 puede venir de Registro; las demás son de Gobernanza.
    op.execute(
        """
        CREATE FUNCTION gobernanza.solo_version_inicial() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            IF current_user = 'svc_registro' AND NEW.numero <> 1 THEN
                RAISE EXCEPTION 'Registro solo puede crear la versión 1 de un hallazgo';
            END IF;
            RETURN NEW;
        END;
        $$
        """
    )
    op.execute(
        "CREATE TRIGGER hallazgo_version_inicial BEFORE INSERT ON gobernanza.hallazgo_version "
        "FOR EACH ROW EXECUTE FUNCTION gobernanza.solo_version_inicial()"
    )


def downgrade() -> None:
    op.execute("DROP TABLE gobernanza.hallazgo_version")
    op.execute("DROP FUNCTION gobernanza.solo_version_inicial()")
    op.execute("REVOKE USAGE ON SCHEMA gobernanza FROM svc_registro")
