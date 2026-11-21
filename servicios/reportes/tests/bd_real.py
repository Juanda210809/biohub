"""PostgreSQL real para las pruebas de integración de Reportes (HU-15).

Usa el mismo script de db/reportes (sin la suscripción: en la prueba no hay base operacional de
donde copiar) y la migración real de Reportes, con el usuario real svc_reportes. Los hallazgos de
prueba se insertan como administrador en campo.hallazgo_publico, como si hubieran llegado por
replicación.

Cómo corren:
- En el CI levantan un contenedor postgres:16 con Docker (igual que las de Kong y Gobernanza).
- En tu PC, si tienes Docker prendido: `python -m pytest` desde servicios/reportes.
- Con un PostgreSQL ya corriendo: define BIOHUB_PG_ADMIN_URL (usuario administrador).
Sin Docker ni BIOHUB_PG_ADMIN_URL se saltan en tu PC, pero en el CI fallan: nunca se saltan allá.
"""
import os
import re
import shutil
import socket
import subprocess
import time
from pathlib import Path

import psycopg
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import close_all_sessions

RAIZ = Path(__file__).resolve().parents[3]
SERVICIO = RAIZ / "servicios" / "reportes"
SCRIPT_BD = RAIZ / "db" / "reportes" / "01-copia-y-suscripcion.sh"
IMAGEN = os.environ.get("BIOHUB_PG_TEST_IMAGE_REPORTES", "postgres:16")
CLAVES = {"POSTGRES_DB": "biohub_reportes_prueba", "REPORTES_DB_PASSWORD": "reportes"}


def _puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _esperar(url: str, segundos: int = 90) -> None:
    limite = time.time() + segundos
    while True:
        try:
            with psycopg.connect(url, connect_timeout=2):
                return
        except psycopg.OperationalError:
            if time.time() > limite:
                raise
            time.sleep(1)


def _sql_del_script() -> str:
    """El primer bloque SQL de db/reportes (tablas, rol y esquema), con las variables reemplazadas."""
    contenido = SCRIPT_BD.read_text(encoding="utf-8")
    sql = contenido.split("<<-EOSQL", 1)[1].split("EOSQL", 1)[0]
    return re.sub(r"\$\{(\w+)\}", lambda m: CLAVES[m.group(1)], sql)


@pytest.fixture(scope="session")
def servidor():
    """Un PostgreSQL limpio: (host, puerto, url de administrador)."""
    admin = os.environ.get("BIOHUB_PG_ADMIN_URL")
    if admin:
        info = psycopg.conninfo.conninfo_to_dict(admin)
        yield info.get("host", "localhost"), int(info.get("port", 5432)), admin
        return
    puerto = _puerto_libre()
    nombre = f"biohub-pg-reportes-prueba-{os.getpid()}"
    arranque = None
    if shutil.which("docker") is not None:
        arranque = subprocess.run(
            ["docker", "run", "-d", "--rm", "--name", nombre, "-e", "POSTGRES_PASSWORD=postgres",
             "-p", f"127.0.0.1:{puerto}:5432", IMAGEN],
            capture_output=True,
            text=True,
        )
    if arranque is None or arranque.returncode != 0:
        motivo = "no hay Docker" if arranque is None else arranque.stderr.strip()[:300]
        if os.environ.get("CI"):
            pytest.fail(f"Las pruebas de integración son obligatorias en el CI ({motivo})")
        pytest.skip(f"Se saltan en local: {motivo}. Prende Docker o define BIOHUB_PG_ADMIN_URL")
    try:
        url = f"postgresql://postgres:postgres@127.0.0.1:{puerto}/postgres"
        _esperar(url)
        yield "127.0.0.1", puerto, url
    finally:
        subprocess.run(["docker", "rm", "-f", nombre], capture_output=True)


@pytest.fixture(scope="session")
def bd(servidor):
    """(admin, reportes): motores sobre una base con el script de db/reportes y la migración aplicados."""
    host, puerto, admin = servidor
    nombre_bd = CLAVES["POSTGRES_DB"]
    with psycopg.connect(admin, autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {nombre_bd}")
        c.execute("DROP ROLE IF EXISTS svc_reportes")
        c.execute(f"CREATE DATABASE {nombre_bd}")
    url_bd = psycopg.conninfo.make_conninfo(admin, dbname=nombre_bd)
    with psycopg.connect(url_bd, autocommit=True) as c:
        c.execute(_sql_del_script())

    clave = CLAVES["REPORTES_DB_PASSWORD"]
    url_reportes = f"postgresql+psycopg://svc_reportes:{clave}@{host}:{puerto}/{nombre_bd}"
    subprocess.run(
        ["python", "-m", "alembic", "upgrade", "head"],
        cwd=SERVICIO,
        env=dict(os.environ, ESQUEMA="reportes", DATABASE_URL=url_reportes),
        check=True,
        capture_output=True,
    )
    info = psycopg.conninfo.conninfo_to_dict(admin)
    usuario, clave_admin = info.get("user", "postgres"), info.get("password", "")
    admin_motor = create_engine(f"postgresql+psycopg://{usuario}:{clave_admin}@{host}:{puerto}/{nombre_bd}")
    reportes = create_engine(url_reportes)
    yield admin_motor, reportes
    close_all_sessions()
    admin_motor.dispose()
    reportes.dispose()
    with psycopg.connect(admin, autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {nombre_bd} WITH (FORCE)")
        c.execute("DROP ROLE IF EXISTS svc_reportes")
