from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_database_ports_are_local_only():
    services = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))["services"]
    for name, port in (("bd-operacional", 5442), ("bd-consulta", 5443), ("bd-reportes", 5444)):
        assert services[name]["ports"] == [f"127.0.0.1:{port}:5432"]


def test_services_and_cache_have_no_host_ports():
    services = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))["services"]
    for name in ("registro", "gobernanza", "identidad", "consulta", "reportes", "redis"):
        assert not services[name].get("ports")
        assert services[name].get("network_mode") != "host"
    assert services["kong"]["environment"]["KONG_ADMIN_LISTEN"] == "127.0.0.1:8001"
