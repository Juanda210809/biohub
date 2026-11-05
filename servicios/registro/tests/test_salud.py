from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)


def test_salud_responde():
    respuesta = cliente.get("/salud")
    assert respuesta.status_code == 200
    assert respuesta.json()["servicio"] == "registro"
