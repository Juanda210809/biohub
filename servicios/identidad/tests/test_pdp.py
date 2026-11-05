from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)


def test_pdp_niega_por_defecto():
    respuesta = cliente.post("/interno/autorizar", json={"accion": "ver_ubicacion"})
    assert respuesta.json()["decision"] == "DENEGAR"
