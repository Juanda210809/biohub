"""Configuración de Alembic (migraciones) para este servicio.

- La conexión se toma de DATABASE_URL (docker-compose.yml).
- La tabla de control `alembic_version` se guarda en el esquema del servicio (ESQUEMA),
  para que los servicios que comparten la BD Operacional no se pisen entre sí.
"""
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

DATABASE_URL = os.environ["DATABASE_URL"]
ESQUEMA = os.environ["ESQUEMA"]

# Si más adelante usan modelos de SQLAlchemy, pongan aquí su metadata para autogenerar.
target_metadata = None


def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        version_table_schema=ESQUEMA,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    motor = create_engine(DATABASE_URL)
    with motor.connect() as conexion:
        context.configure(
            connection=conexion,
            target_metadata=target_metadata,
            version_table_schema=ESQUEMA,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
