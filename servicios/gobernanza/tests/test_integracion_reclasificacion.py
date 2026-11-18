"""Pruebas de integración de HU-08 contra un PostgreSQL real.

Usan los mismos scripts de db/operacional y las mismas migraciones de Registro y Gobernanza del
proyecto, con los usuarios reales (svc_registro, svc_gobernanza). Así se prueban los permisos de
verdad, la transacción completa y dos reclasificaciones al mismo tiempo.

Cómo corren:
- En el CI levantan un contenedor postgis/postgis:16-3.4 con Docker (igual que las de Kong).
- En tu PC, si tienes Docker: `python -m pytest tests/test_integracion_reclasificacion.py`
  desde servicios/gobernanza.
- Con un PostgreSQL ya corriendo: define BIOHUB_PG_ADMIN_URL (usuario administrador), por ejemplo
  postgresql://postgres:postgres@localhost:5432/postgres. Crea una base nueva para la prueba.
Sin Docker ni BIOHUB_PG_ADMIN_URL se saltan en tu PC, pero en el CI fallan: nunca se saltan allá.
"""
import os
import re
import shutil
import socket
import subprocess
import threading
import time
import uuid
from pathlib import Path

import psycopg
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.dominio.reclasificacion import EspecieNoExiste, MismaEspecie, ServicioReclasificacion
from app.repositorio.hallazgos import RepositorioGobernanza

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


@pytest.fixture(scope="module")
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


@pytest.fixture(scope="module")
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
    registro.dispose()
    gobernanza.dispose()
    with psycopg.connect(admin, autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {CLAVES['POSTGRES_DB']} WITH (FORCE)")
        for rol in ("svc_registro", "svc_gobernanza", "svc_identidad", "replicador"):
            c.execute(f"DROP ROLE IF EXISTS {rol}")


def _registrar_hallazgo(registro) -> uuid.UUID:
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


def _servicio(gobernanza):
    """Un servicio con su propia sesión, como en cada petición HTTP."""
    return ServicioReclasificacion(RepositorioGobernanza(sessionmaker(bind=gobernanza)()))


def test_reclasifica_y_conserva_el_historial(bd):
    registro, gobernanza = bd
    hallazgo = _registrar_hallazgo(registro)

    resultado = _servicio(gobernanza).reclasificar(hallazgo, AZULEJO, "Análisis genético", CIENTIFICO)

    assert (resultado.version, resultado.especie_anterior, resultado.especie_nueva) == (
        2, "Setophaga cerulea", "Thraupis episcopus"
    )
    with gobernanza.connect() as c:
        historial = c.execute(
            text(
                "SELECT numero, especie, justificacion, atributos, autor_id "
                "FROM gobernanza.hallazgo_version WHERE hallazgo_id = :h ORDER BY numero"
            ),
            {"h": hallazgo},
        ).all()
        actual = c.execute(
            text("SELECT especie_id, version_actual FROM campo.hallazgo WHERE id = :h"), {"h": hallazgo}
        ).one()
        publico = c.execute(
            text("SELECT especie, version, atributos_publicos FROM campo.hallazgo_publico "
                 "WHERE hallazgo_id = :h"),
            {"h": hallazgo},
        ).one()
    assert [(v.numero, v.especie) for v in historial] == [(1, "Setophaga cerulea"), (2, "Thraupis episcopus")]
    assert historial[1].atributos == {"altitudMsnm": 1200}  # conserva lo medido en campo
    assert historial[1].autor_id == CIENTIFICO
    assert tuple(actual) == (AZULEJO, 2)
    assert tuple(publico) == ("Thraupis episcopus", 2, {"altitudMsnm": 1200})
    with registro.connect() as c:
        auditoria = c.execute(
            text("SELECT accion, actor_id FROM campo.auditoria WHERE recurso_id = :h"), {"h": hallazgo}
        ).all()
    assert [tuple(a) for a in auditoria] == [("reclasificar", CIENTIFICO)]


def test_un_rechazo_no_deja_el_hallazgo_bloqueado(bd):
    registro, gobernanza = bd
    hallazgo = _registrar_hallazgo(registro)

    with pytest.raises(MismaEspecie):
        _servicio(gobernanza).reclasificar(hallazgo, CERULEA, "Misma", CIENTIFICO)
    with pytest.raises(EspecieNoExiste):
        _servicio(gobernanza).reclasificar(hallazgo, uuid.uuid4(), "No existe", CIENTIFICO)

    # Si el rechazo hubiera dejado el bloqueo, esto se quedaría esperando.
    with gobernanza.connect() as c:
        c.execute(text("SET lock_timeout = '3s'"))
        c.execute(text("SELECT 1 FROM campo.hallazgo WHERE id = :h FOR UPDATE"), {"h": hallazgo})


def test_dos_reclasificaciones_a_la_vez_no_repiten_version(bd):
    registro, gobernanza = bd
    hallazgo = _registrar_hallazgo(registro)
    versiones = []

    def reclasificar(especie):
        resultado = _servicio(gobernanza).reclasificar(hallazgo, especie, "Concurrente", CIENTIFICO)
        versiones.append(resultado.version)

    hilos = [threading.Thread(target=reclasificar, args=(e,)) for e in (AZULEJO, RANA)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join(timeout=30)

    assert sorted(versiones) == [2, 3]
    with gobernanza.connect() as c:
        numeros = c.execute(
            text("SELECT numero FROM gobernanza.hallazgo_version WHERE hallazgo_id = :h ORDER BY numero"),
            {"h": hallazgo},
        ).scalars().all()
    assert numeros == [1, 2, 3]


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE campo.hallazgo SET region = 'Otra' WHERE id = :h",
        "SELECT * FROM campo.ubicacion WHERE hallazgo_id = :h",
        "INSERT INTO campo.especie (id, tipo_especie_id, nombre_cientifico) "
        "VALUES (gen_random_uuid(), '10000000-0000-0000-0000-000000000001', 'Falsa ' || :h)",
        "DELETE FROM gobernanza.hallazgo_version WHERE hallazgo_id = :h",
        "UPDATE gobernanza.hallazgo_version SET especie = 'Otra' WHERE hallazgo_id = :h",
    ],
    ids=["cambiar_region", "ver_coordenadas", "crear_especie", "borrar_historial", "cambiar_historial"],
)
def test_gobernanza_no_puede_lo_que_no_le_toca(bd, sql):
    registro, gobernanza = bd
    hallazgo = _registrar_hallazgo(registro)

    with pytest.raises(Exception, match="permission denied"), gobernanza.begin() as c:
        c.execute(text(sql), {"h": str(hallazgo)})
