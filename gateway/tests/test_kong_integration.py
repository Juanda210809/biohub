import http.server
import json
import os
import shutil
import socket
import subprocess
import threading
import time
from email.utils import parsedate_to_datetime
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
KONG_CONFIG = REPO_ROOT / "gateway" / "kong.yml"
KONG_IMAGE = os.environ.get("BIOHUB_KONG_TEST_IMAGE", "kong:3.6")
API_KEY = "clave-demo-universidad"


class EchoHandler(http.server.BaseHTTPRequestHandler):
    requests = 0

    def do_GET(self):
        type(self).requests += 1
        body = json.dumps({"path": self.path}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


def free_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


@pytest.fixture
def kong_gateway(tmp_path_factory):
    if shutil.which("docker") is None:
        pytest.fail("Docker is required: integration tests must not be skipped")

    name = f"biohub-kong-test-{os.getpid()}"
    upstream_port = free_port()
    proxy_port = free_port()
    EchoHandler.requests = 0
    server = http.server.ThreadingHTTPServer(("0.0.0.0", upstream_port), EchoHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    config = yaml.safe_load(KONG_CONFIG.read_text(encoding="utf-8-sig"))
    external = next(item for item in config["services"] if item["name"] == "consulta-externa")
    external["url"] = f"http://host.docker.internal:{upstream_port}/externa"
    public = next(item for item in config["services"] if item["name"] == "consulta")
    public["url"] = f"http://host.docker.internal:{upstream_port}"
    config["consumers"].append(
        {"username": "universidad-demo-2", "keyauth_credentials": [{"key": "clave-demo-universidad-2"}]}
    )
    config_path = tmp_path_factory.mktemp("kong") / "kong.yml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    command = [
        "docker",
        "run",
        "--detach",
        "--rm",
        "--name",
        name,
        "--add-host=host.docker.internal:host-gateway",
        "--publish",
        f"127.0.0.1:{proxy_port}:8000",
        "--env",
        "KONG_DATABASE=off",
        "--env",
        "KONG_DECLARATIVE_CONFIG=/kong/kong.yml",
        "--env",
        "KONG_PROXY_LISTEN=0.0.0.0:8000",
        "--volume",
        f"{config_path}:/kong/kong.yml:ro",
        KONG_IMAGE,
    ]
    container_id = None
    try:
        started = subprocess.run(
            command, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        container_id = started.stdout.strip()
        import httpx

        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            try:
                response = httpx.get(f"http://127.0.0.1:{proxy_port}/", timeout=1)
            except httpx.HTTPError:
                time.sleep(1)
                continue
            if response.status_code in {404, 401, 200}:
                break
            time.sleep(1)
        else:
            logs = subprocess.run(
                ["docker", "logs", container_id],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            pytest.fail(f"Kong did not become ready.\n{logs.stdout}\n{logs.stderr}")

        yield f"http://127.0.0.1:{proxy_port}"
    finally:
        if container_id:
            subprocess.run(["docker", "stop", container_id], capture_output=True, check=False)
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_external_route_authenticates_and_forwards_to_consulta(kong_gateway):
    import httpx

    url = f"{kong_gateway}/externa/v1/hallazgos"
    with httpx.Client(timeout=5) as client:
        assert client.get(url).status_code == 401
        assert client.get(url, headers={"apikey": "clave-invalida"}).status_code == 401
        response = client.get(url, headers={"apikey": API_KEY})
        internal = client.get(f"{kong_gateway}/api/v1/identidad/interno/politicas")

    assert response.status_code == 200
    assert response.json() == {"path": "/externa/hallazgos"}
    assert response.headers["x-ratelimit-limit-minute"] == "60"
    assert response.headers["x-ratelimit-remaining-minute"] == "59"
    assert internal.status_code == 403


def test_external_rate_limit_rejects_request_61_before_upstream(kong_gateway):
    import httpx

    url = f"{kong_gateway}/externa/v1/hallazgos"
    with httpx.Client(timeout=5) as client:
        # Start well inside the server's minute window, not at its boundary.
        server_time = parsedate_to_datetime(client.get(f"{kong_gateway}/").headers["date"])
        if server_time.second > 30:
            time.sleep(61 - server_time.second)
        responses = [client.get(url, headers={"apikey": API_KEY}) for _ in range(60)]
        other_consumer = client.get(url, headers={"apikey": "clave-demo-universidad-2"})
        over_limit = client.get(url, headers={"apikey": API_KEY})

    assert all(response.status_code == 200 for response in responses)
    assert other_consumer.status_code == 200
    assert over_limit.status_code == 429
    assert EchoHandler.requests == 61


def test_public_route_cannot_bypass_external_controls(kong_gateway):
    import httpx

    with httpx.Client(timeout=5) as client:
        for path in (
            "/api/v1/consulta/externa/hallazgos",
            "/api/v1/consulta/externa",
            "/api/v1/consulta/externa/",
            "/api/v1/consulta/%65xterna/hallazgos",
        ):
            response = client.get(f"{kong_gateway}{path}")
            assert response.status_code == 403, (path, response.status_code)
        assert EchoHandler.requests == 0
        public = client.get(f"{kong_gateway}/api/v1/consulta/salud")
        assert public.status_code == 200
        assert public.json() == {"path": "/salud"}
