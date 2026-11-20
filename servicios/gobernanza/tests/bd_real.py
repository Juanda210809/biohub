"""PostgreSQL real para las pruebas de integración (lo comparten HU-08 y HU-12).

Usa los mismos scripts de db/operacional y las mismas migraciones de Registro y Gobernanza del
proyecto, con los usuarios reales (svc_registro, svc_gobernanza).

Cómo corren:
- En el CI levantan un contenedor postgis/postgis:16-3.4 con Docker (igual que las de Kong).
- En tu PC, si tienes Docker prendido: `python -m pytest` desde servicios/gobernanza.
- Con un PostgreSQL ya corriendo: define BIOHUB_PG_ADMIN_URL (usuario administrador), por ejemplo
  postgresql://postgres:postgres@localhost:5432/postgres. Crea una base nueva para la prueba.
Sin Docker ni BIOHUB_PG_ADMIN_URL se saltan en tu PC, pero en el CI fallan: nunca se saltan allá.
"""
import os
import re
import shutil
import socket
import subprocess
import time
import uuid
from pathlib import Path

import psycopg
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import close_all_sessions

RAIZ = Path(__file__).resolve().parents[3]
SERVICIOS = RAIZ / "servicios"
SCRIPTS_BD = RAIZ / "db" / "operacional"
IMAGEN = os.environ.get("BIOHUB_PG_TEST_IMAGE", "postgis/postgis:16-3.4")
CLAVES = {
    "POSTGRES_DB": "biohub_prueba",
    "REGISTRO_DB_PASSWORD": "registro",
    "GOBERNANZA_DB_PASSWORD": "gobernanza",
    "IDENTIDAD_DB_PASSWORD": "identidad",
    "REPLICADOR_PASSWORD": "replicador",
}

EXPEDICION = "30000000-0000-0000-0000-000000000001"
RANA = uuid.UUID("20000000-0000-0000-0000-000000000001")
CERULEA = uuid.UUID("20000000-0000-0000-0000-000000000002")
AZULEJO = uuid.UUID("20000000-0000-0000-0000-000000000003")
INVESTIGADOR = uuid.UUID("00000000-0000-0000-0000-0000000000aa")
CIENTIFICO = uuid.UUID("00000000-0000-0000-0000-0000000000ab")


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


def _sql_de_script(nombre: str) -> str:
    """El SQL de un script de db/operacional, con las variables ${...} ya reemplazadas."""
    contenido = (SCRIPTS_BD / nombre).read_text(encoding="utf-8")
    sql = contenido.split("<<-EOSQL", 1)[1].rsplit("EOSQL", 1)[0]
    return re.sub(r"\$\{(\w+)\}", lambda m: CLAVES[m.group(1)], sql)


def _migrar(servicio: str, usuario: str, clave: str, esquema: str, host: str, puerto: int) -> None:
    entorno = dict(
        os.environ,
        ESQUEMA=esquema,
        DATABASE_URL=f"postgresql+psycopg://{usuario}:{clave}@{host}:{puerto}/{CLAVES['POSTGRES_DB']}",
    )
    subprocess.run(
        ["python", "-m", "alembic", "upgrade", "head"],
        cwd=SERVICIOS / servicio,
        env=entorno,
        check=True,
        capture_output=True,
    )


@pytest.fixture(scope="session")
def servidor():
    """Un PostgreSQL limpio: (host, puerto, url de administrador)."""
    admin = os.environ.get("BIOHUB_PG_ADMIN_URL")
    if admin:
        info = psycopg.conninfo.conninfo_to_dict(admin)
        yield info.get("host", "localhost"), int(info.get("port", 5432)), admin
        return
    puerto = _puerto_libre()
    nombre = f"biohub-pg-prueba-{os.getpid()}"
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
    """Base biohub_prueba con los scripts de db/operacional y las migraciones aplicadas."""
    host, puerto, admin = servidor
    with psycopg.connect(admin, autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {CLAVES['POSTGRES_DB']}")
        c.execute(f"CREATE DATABASE {CLAVES['POSTGRES_DB']}")
    url_bd = psycopg.conninfo.make_conninfo(admin, dbname=CLAVES["POSTGRES_DB"])
    with psycopg.connect(url_bd, autocommit=True) as c:
        for script in ("01-roles-y-esquemas.sh", "02-tabla-publica.sh"):
            c.execute(_sql_de_script(script))
    _migrar("gobernanza", "svc_gobernanza", CLAVES["GOBERNANZA_DB_PASSWORD"], "gobernanza", host, puerto)
    _migrar("registro", "svc_registro", CLAVES["REGISTRO_DB_PASSWORD"], "campo", host, puerto)

    base = f"postgresql+psycopg://{{}}:{{}}@{host}:{puerto}/{CLAVES['POSTGRES_DB']}"
    registro = create_engine(base.format("svc_registro", CLAVES["REGISTRO_DB_PASSWORD"]))
    gobernanza = create_engine(base.format("svc_gobernanza", CLAVES["GOBERNANZA_DB_PASSWORD"]))
    yield registro, gobernanza
    close_all_sessions()  # las sesiones de cada prueba quedan abiertas; se cierran antes de borrar
    registro.dispose()
    gobernanza.dispose()
    with psycopg.connect(admin, autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {CLAVES['POSTGRES_DB']} WITH (FORCE)")
        for rol in ("svc_registro", "svc_gobernanza", "svc_identidad", "replicador"):
            c.execute(f"DROP ROLE IF EXISTS {rol}")


def registrar_hallazgo(registro) -> uuid.UUID:
    """Lo que hace Registro en HU-03: hallazgo, versión 1 y fila pública."""
    hallazgo = uuid.uuid4()
    with registro.begin() as c:
        c.execute(
            text(
                "INSERT INTO campo.hallazgo (id, especie_id, expedicion_id, investigador_id, "
                "fecha_hallazgo, region, departamento) "
                "VALUES (:h, :e, :x, :i, '2026-10-20', 'Pacifico', 'Cauca')"
            ),
            {"h": hallazgo, "e": CERULEA, "x": EXPEDICION, "i": INVESTIGADOR},
        )
        c.execute(
            text(
                "INSERT INTO gobernanza.hallazgo_version "
                "(id, hallazgo_id, numero, especie, atributos, autor_id, justificacion) "
                "VALUES (:id, :h, 1, 'Setophaga cerulea', CAST(:a AS jsonb), :i, 'Registro inicial')"
            ),
            {"id": uuid.uuid4(), "h": hallazgo, "i": INVESTIGADOR, "a": '{"altitudMsnm": 1200}'},
        )
        c.execute(
            text(
                "INSERT INTO campo.hallazgo_publico (hallazgo_id, especie, region, departamento, "
                "atributos_publicos, version) "
                "VALUES (:h, 'Setophaga cerulea', 'Pacifico', 'Cauca', CAST(:a AS jsonb), 1)"
            ),
            {"h": hallazgo, "a": '{"altitudMsnm": 1200}'},
        )
    return hallazgo
