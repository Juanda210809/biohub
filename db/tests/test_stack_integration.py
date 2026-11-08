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
        f'psql -v ON_ERROR_STOP=1 -U "{user}" -d "$POSTGRES_DB" -Atc "$1"',
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
