import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
DEMO = ROOT / "db" / "demo"


def test_demo_sql_matches_generator(tmp_path):
    script = tmp_path / "generar_datos_demo.py"
    shutil.copyfile(DEMO / script.name, script)
    subprocess.run([sys.executable, str(script)], cwd=tmp_path, check=True, timeout=30)
    assert (tmp_path / "datos-demo.sql").read_text(encoding="utf-8") == (
        DEMO / "datos-demo.sql"
    ).read_text(encoding="utf-8")


def test_demo_sql_has_57_distinct_findings():
    content = (DEMO / "datos-demo.sql").read_text(encoding="utf-8")
    identifiers = re.findall(
        r"INSERT\s+INTO\s+campo\.hallazgo\s*\([^)]*\)\s*VALUES\s*\('([^']+)'",
        content,
        re.IGNORECASE,
    )
    assert len(identifiers) == len(set(identifiers)) == 57
    assert all(identifier.startswith("60000000-") for identifier in identifiers)


def test_demo_sql_is_transactional_and_idempotent():
    content = (DEMO / "datos-demo.sql").read_text(encoding="utf-8")
    statements = [
        statement.strip()
        for statement in re.sub(r"(?m)^\s*--[^\n]*", "", content).split(";")
        if statement.strip()
    ]
    assert statements[0] == "BEGIN"
    assert statements[-1] == "COMMIT"
    inserts = [statement for statement in statements if statement.upper().startswith("INSERT")]
    assert inserts
    for statement in inserts:
        assert re.search(r"\bON\s+CONFLICT\b.*\bDO\s+NOTHING\s*$", statement, re.IGNORECASE | re.DOTALL)


def test_demo_public_inserts_never_expose_coordinates():
    content = (DEMO / "datos-demo.sql").read_text(encoding="utf-8")
    inserts = re.findall(
        r"INSERT\s+INTO\s+campo\.hallazgo_publico\b[^;]*;", content, re.IGNORECASE
    )
    assert len(inserts) == 57
    for statement in inserts:
        assert not re.search(r"\b(?:latitud|longitud|precision)(?:\b|_)", statement, re.IGNORECASE)


def test_demo_compose_startup_dependencies_and_no_ports():
    services = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))["services"]
    demo = services["datos-demo"]
    assert demo["restart"] == "no"
    for database in ("bd-operacional", "bd-reportes"):
        assert demo["depends_on"][database]["condition"] == "service_healthy"
    assert services["reportes"]["depends_on"]["datos-demo"]["condition"] == "service_completed_successfully"
    assert not demo.get("ports")
    assert demo.get("network_mode") != "host"
