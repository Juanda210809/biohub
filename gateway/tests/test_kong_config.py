from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "gateway" / "kong.yml"


def load_config():
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def test_external_api_is_a_stable_gateway_route():
    config = load_config()
    service = next(item for item in config["services"] if item["name"] == "consulta-externa")
    route = service["routes"][0]

    assert service["url"] == "http://consulta:8000/externa"
    assert route["paths"] == ["/externa/v1"]
    assert route["strip_path"] is True


def test_external_api_requires_consumer_key_and_limits_each_consumer():
    config = load_config()
    service = next(item for item in config["services"] if item["name"] == "consulta-externa")
    plugins = {plugin["name"]: plugin["config"] for plugin in service["plugins"]}

    assert plugins["key-auth"]["key_names"] == ["apikey"]
    assert plugins["rate-limiting"]["minute"] == 60
    assert plugins["rate-limiting"]["policy"] == "local"
    assert config["consumers"]
    assert all(consumer.get("keyauth_credentials") for consumer in config["consumers"])


def test_internal_identity_route_is_blocked_at_gateway():
    config = load_config()
    identity = next(item for item in config["services"] if item["name"] == "identidad")
    blocked = next(route for route in identity["routes"] if route["name"] == "identidad-interno-bloqueado")
    termination = next(plugin for plugin in blocked["plugins"] if plugin["name"] == "request-termination")

    assert blocked["paths"] == ["/api/v1/identidad/interno"]
    assert termination["config"]["status_code"] == 403


def test_public_consulta_route_blocks_external_namespace():
    config = load_config()
    consulta = next(item for item in config["services"] if item["name"] == "consulta")
    blocked = next(route for route in consulta["routes"] if route["name"] == "consulta-externa-bloqueada")
    termination = next(plugin for plugin in blocked["plugins"] if plugin["name"] == "request-termination")

    assert blocked["paths"] == ["/api/v1/consulta/externa"]
    assert termination["config"]["status_code"] == 403
    assert "methods" not in blocked  # El bloqueo aplica a todos los metodos HTTP.
