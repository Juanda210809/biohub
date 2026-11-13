import json
import shutil
import subprocess
import time
import uuid
from pathlib import Path

import httpx
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
DATABASES = ("bd-operacional", "bd-consulta", "bd-reportes")


@pytest.fixture(scope="module")
def stack(tmp_path_factory):
    if not shutil.which("docker"):
        pytest.fail("Docker is required for infrastructure integration tests")
    project = "biohub-test-" + uuid.uuid4().hex[:10]
    config = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    for service in config["services"].values():
        if "env_file" in service:
            service["env_file"] = str(ROOT / ".env.example")
        # Preserve database binding IPs, use ephemeral ports to avoid collisions.
        service["ports"] = [
            {
                "target": int(port.split(":")[-1]),
                "published": "0",
                "host_ip": port.split(":")[0] if port.count(":") == 2 else "127.0.0.1",
            }
            for port in service.get("ports", [])
        ]
    path = tmp_path_factory.mktemp("stack") / "compose.yml"
    path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    command = [
        "docker",
        "compose",
        "--project-directory",
        str(ROOT),
        "--env-file",
        str(ROOT / ".env.example"),
        "-p",
        project,
        "-f",
        str(path),
    ]

    def run(*args, check=True):
        result = subprocess.run(
            command + list(args),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=900,
        )
        if check and result.returncode:
            pytest.fail(result.stdout + result.stderr)
        return result

    try:
        run("up", "--build", "-d", "--wait", "--wait-timeout", "180")
        yield run
    finally:
        # Only the uniquely named test project's containers and volumes are removed.
        run("down", "--volumes", "--remove-orphans", check=False)


def sql(stack, database, statement, role=None, check=True):
    user = role or "$POSTGRES_USER"
    return stack(
        "exec",
        "-T",
        database,
        "sh",
        "-c",
        f'psql -v ON_ERROR_STOP=1 -v VERBOSITY=verbose -U "{user}" -d "$POSTGRES_DB" -Atc "$1"',
        "sh",
        statement,
        check=check,
    )


def test_runtime_ports_and_database_connections(stack):
    for database in DATABASES:
        container = stack("ps", "-q", database).stdout.strip()
        info = json.loads(
            subprocess.check_output(["docker", "inspect", container], text=True, encoding="utf-8")
        )[0]
        bindings = info["NetworkSettings"]["Ports"]["5432/tcp"]
        assert bindings and all(binding["HostIp"] == "127.0.0.1" for binding in bindings)
        assert sql(stack, database, "SELECT 1").stdout.strip() == "1"


def test_replication_and_readonly_consulta(stack):
    identifier = str(uuid.uuid4())
    sql(
        stack,
        "bd-operacional",
        "INSERT INTO campo.hallazgo_publico (hallazgo_id, especie) "
        f"VALUES ('{identifier}', 'Prueba aislada')",
    )
    for database in ("bd-consulta", "bd-reportes"):
        for _ in range(30):
            count = sql(
                stack,
                database,
                f"SELECT count(*) FROM campo.hallazgo_publico WHERE hallazgo_id='{identifier}'",
            )
            if count.stdout.strip() == "1":
                break
            time.sleep(1)
        else:
            pytest.fail(f"Replication did not reach {database}")
    assert (
        sql(
            stack, "bd-consulta", "SELECT count(*) FROM campo.hallazgo_publico", role="svc_consulta"
        ).returncode
        == 0
    )
    denied = sql(stack, "bd-consulta", "DELETE FROM campo.hallazgo_publico", role="svc_consulta", check=False)
    assert denied.returncode != 0
    assert (
        sql(
            stack,
            "bd-consulta",
            f"SELECT count(*) FROM campo.hallazgo_publico WHERE hallazgo_id='{identifier}'",
        ).stdout.strip()
        == "1"
    )


def test_real_services_via_kong(stack):
    address = stack("port", "kong", "8000").stdout.strip()
    with httpx.Client(base_url=f"http://{address}", timeout=10) as client:
        for service in ("registro", "gobernanza", "identidad", "consulta", "reportes"):
            for _ in range(30):
                response = client.get(f"/api/v1/{service}/salud")
                if response.status_code == 200 and response.json().get("bd") == "ok":
                    break
                time.sleep(1)
            assert response.status_code == 200
            assert response.json()["bd"] == "ok", response.text
            if service == "consulta":
                assert response.json()["cache"] == "ok"
        assert client.get("/externa/v1/hallazgos").status_code == 401
        external = client.get("/externa/v1/hallazgos", headers={"apikey": "clave-demo-universidad"})
        assert external.status_code == 200
        assert client.get("/api/v1/consulta/externa/hallazgos").status_code == 403
    portal = stack("port", "portal", "5173").stdout.strip()
    assert httpx.get(f"http://{portal}", timeout=10).status_code == 200


REGISTRO_SCRIPT = """
import json
from datetime import date
from decimal import Decimal
from uuid import UUID
from app.db import obtener_sesion
from app.dominio.hallazgos import NuevoHallazgo
from app.dominio.servicio_hallazgos import ServicioHallazgos
from app.repositorio.hallazgos import RepositorioHallazgos
session_generator = obtener_sesion()
session = next(session_generator)
try:
    identifier = ServicioHallazgos(RepositorioHallazgos(session)).registrar(NuevoHallazgo(
        especie_id=UUID("20000000-0000-0000-0000-000000000001"),
        expedicion_id=UUID("30000000-0000-0000-0000-000000000001"),
        investigador_id=UUID("00000000-0000-0000-0000-0000000000aa"),
        fecha_hallazgo=date(2026, 11, 1), latitud=Decimal("2.512345"),
        longitud=Decimal("-77.123456"), region="Pacifico", departamento="Cauca",
        atributos={"temperaturaAgua": 18.5, "observaciones": "PRIVATE_TEST_LOCATION"},
    ))
    print(json.dumps({"id": str(identifier)}))
finally:
    session_generator.close()
"""


def test_registro_persists_and_replicates_only_public_data(stack):
    result = stack("exec", "-T", "registro", "python", "-c", REGISTRO_SCRIPT)
    identifier = str(uuid.UUID(json.loads(result.stdout.strip())["id"]))
    for table, column in (
        ("campo.hallazgo", "id"),
        ("campo.ubicacion", "hallazgo_id"),
        ("gobernanza.hallazgo_version", "hallazgo_id"),
        ("campo.auditoria", "recurso_id"),
    ):
        assert (
            sql(
                stack, "bd-operacional", f"SELECT count(*) FROM {table} WHERE {column}='{identifier}'"
            ).stdout.strip()
            == "1"
        )
    for database in DATABASES:
        statement = f"SELECT row_to_json(p) FROM campo.hallazgo_publico p WHERE hallazgo_id='{identifier}'"
        for _ in range(30):
            raw = sql(stack, database, statement).stdout.strip()
            if raw:
                break
            time.sleep(1)
        assert raw, f"Missing public row in {database}"
        row = json.loads(raw)
        assert row["atributos_publicos"] == {"temperaturaAgua": 18.5}
        assert row["region"] == "Pacifico" and row["departamento"] == "Cauca"
        assert row["version"] == 1
        assert not {"latitud", "longitud", "precision_m"} & row.keys()
        assert "PRIVATE_TEST_LOCATION" not in raw
        assert "2.512345" not in raw and "-77.123456" not in raw


def test_registro_http_denial_does_not_create_rows(stack):
    before = sql(stack, "bd-operacional", "SELECT count(*) FROM campo.hallazgo").stdout.strip()
    payload = {
        "especieId": "20000000-0000-0000-0000-000000000001",
        "expedicionId": "30000000-0000-0000-0000-000000000001",
        "fechaHallazgo": "2026-11-01",
        "latitud": 2.512345,
        "longitud": -77.123456,
        "region": "Pacifico",
        "atributos": {"temperaturaAgua": 18.5},
    }
    address = stack("port", "kong", "8000").stdout.strip()
    with httpx.Client(base_url=f"http://{address}", timeout=10) as client:
        assert client.post("/api/v1/registro/hallazgos", json=payload).status_code == 401
        response = client.post(
            "/api/v1/registro/hallazgos", json=payload, headers={"Authorization": "Bearer invalid-test-token"}
        )
        assert response.status_code == 403
    assert sql(stack, "bd-operacional", "SELECT count(*) FROM campo.hallazgo").stdout.strip() == before


def test_late_failure_rolls_back_entire_registro_transaction(stack):
    tables = (
        "campo.hallazgo",
        "campo.ubicacion",
        "gobernanza.hallazgo_version",
        "campo.hallazgo_publico",
        "campo.auditoria",
    )
    before = {
        table: sql(stack, "bd-operacional", f"SELECT count(*) FROM {table}").stdout.strip()
        for table in tables
    }
    # Only the isolated test DB is modified. Fail the final INSERT, after the public row.
    sql(
        stack,
        "bd-operacional",
        """
        CREATE FUNCTION campo.test_fail_audit() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'TEST_FINAL_INSERT_FAILURE' USING ERRCODE = '23514'; END; $$;
        CREATE TRIGGER test_fail_audit BEFORE INSERT ON campo.auditoria
        FOR EACH ROW EXECUTE FUNCTION campo.test_fail_audit();
    """,
    )
    try:
        failed = stack("exec", "-T", "registro", "python", "-c", REGISTRO_SCRIPT, check=False)
        assert failed.returncode != 0
        assert "TEST_FINAL_INSERT_FAILURE" in failed.stderr
        for table in tables:
            assert (
                sql(stack, "bd-operacional", f"SELECT count(*) FROM {table}").stdout.strip() == before[table]
            )
    finally:
        sql(
            stack,
            "bd-operacional",
            "DROP TRIGGER test_fail_audit ON campo.auditoria; DROP FUNCTION campo.test_fail_audit()",
        )
    # A subsequent successful commit acts as a replication barrier, avoiding a sleep-only assertion.
    result = stack("exec", "-T", "registro", "python", "-c", REGISTRO_SCRIPT)
    identifier = str(uuid.UUID(json.loads(result.stdout.strip())["id"]))
    expected = sql(
        stack, "bd-operacional", "SELECT hallazgo_id FROM campo.hallazgo_publico ORDER BY hallazgo_id"
    ).stdout.strip()
    for database in ("bd-consulta", "bd-reportes"):
        for _ in range(30):
            count = sql(
                stack,
                database,
                f"SELECT count(*) FROM campo.hallazgo_publico WHERE hallazgo_id='{identifier}'",
            ).stdout.strip()
            if count == "1":
                break
            time.sleep(1)
        assert count == "1", f"Replication barrier missing in {database}"
        assert (
            sql(
                stack, database, "SELECT hallazgo_id FROM campo.hallazgo_publico ORDER BY hallazgo_id"
            ).stdout.strip()
            == expected
        )


@pytest.mark.parametrize(
    "database,role,statement",
    [
        (database, role, statement)
        for database, role in (("bd-consulta", "svc_consulta"), ("bd-reportes", "svc_reportes"))
        for statement in (
            "INSERT INTO campo.hallazgo_publico (hallazgo_id, especie) VALUES (gen_random_uuid(), 'test')",
            "UPDATE campo.hallazgo_publico SET especie='test'",
            "DELETE FROM campo.hallazgo_publico",
            "TRUNCATE campo.hallazgo_publico",
        )
    ]
    + [
        ("bd-operacional", role, statement)
        for role, statement in (
            ("svc_registro", "SELECT * FROM gobernanza.hallazgo_version"),
            ("svc_registro", "UPDATE campo.auditoria SET accion='test'"),
            ("svc_gobernanza", "SELECT * FROM campo.ubicacion"),
            ("svc_gobernanza", "UPDATE campo.hallazgo_publico SET region='test'"),
            ("svc_gobernanza", "DELETE FROM gobernanza.hallazgo_version"),
            ("svc_gobernanza", "UPDATE gobernanza.hallazgo_version SET especie='test'"),
            ("svc_gobernanza", "TRUNCATE gobernanza.hallazgo_version"),
            ("svc_identidad", "SELECT * FROM campo.hallazgo"),
            ("replicador", "SELECT * FROM campo.ubicacion"),
        )
    ],
)
def test_service_roles_reject_forbidden_sql(stack, database, role, statement):
    # Explicit read-write tests table grants even when the role defaults to read-only.
    # Roll back even if a permission unexpectedly allows the operation.
    result = sql(
        stack,
        database,
        "BEGIN READ WRITE; " + statement + "; ROLLBACK;",
        role=role,
        check=False,
    )
    assert result.returncode != 0
    assert "42501" in result.stderr, result.stderr
