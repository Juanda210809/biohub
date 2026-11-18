from uuid import uuid4

from tests.conftest import CIENTIFICO_ID, HALLAZGO_ID, INVESTIGADOR_ID

CABECERA = {"Authorization": "Bearer token-de-prueba"}
RUTA = f"/hallazgos/{HALLAZGO_ID}/historial"


def test_sin_token_responde_401(cliente):
    respuesta = cliente.get(RUTA, params={"fecha": "2026-03-01"})

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "no_autenticado"


def test_sin_permiso_responde_403(cliente, autorizador):
    autorizador.permitir = False

    respuesta = cliente.get(RUTA, params={"fecha": "2026-03-01"}, headers=CABECERA)

    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "sin_permiso"


def test_pregunta_al_pdp_por_ver_historial_de_ese_hallazgo(cliente, autorizador):
    cliente.get(RUTA, params={"fecha": "2026-03-01"}, headers=CABECERA)

    assert autorizador.llamadas == [("token-de-prueba", "ver_historial", str(HALLAZGO_ID))]


def test_reconstruye_la_version_de_esa_fecha_y_la_compara_con_hoy(cliente):
    respuesta = cliente.get(RUTA, params={"fecha": "2026-03-01"}, headers=CABECERA)

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["fecha"] == "2026-03-01"
    assert datos["enFecha"]["numero"] == 1
    assert datos["enFecha"]["especie"] == "Setophaga cerulea"
    assert datos["enFecha"]["autorId"] == str(INVESTIGADOR_ID)
    assert datos["enFecha"]["justificacion"] == "Registro inicial"
    assert datos["actual"]["numero"] == 2
    assert datos["actual"]["autorId"] == str(CIENTIFICO_ID)
    assert datos["versionesPosteriores"] == 1
    assert datos["cambios"] == [
        {"campo": "especie", "antes": "Setophaga cerulea", "ahora": "Thraupis episcopus"},
        {"campo": "atributos.altitudMsnm", "antes": 1200, "ahora": 1250},
    ]


def test_una_fecha_posterior_al_ultimo_cambio_coincide_con_hoy(cliente):
    respuesta = cliente.get(RUTA, params={"fecha": "2026-12-01"}, headers=CABECERA)

    assert respuesta.status_code == 200
    assert respuesta.json()["enFecha"]["numero"] == 2
    assert respuesta.json()["cambios"] == []
    assert respuesta.json()["versionesPosteriores"] == 0


def test_antes_del_registro_responde_404_con_la_primera_fecha(cliente):
    respuesta = cliente.get(RUTA, params={"fecha": "2025-12-31"}, headers=CABECERA)

    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "sin_version_en_fecha"
    assert "2026-01-10" in respuesta.json()["detalles"][0]["mensaje"]


def test_hallazgo_inexistente_responde_404(cliente):
    ruta = f"/hallazgos/{uuid4()}/historial"

    respuesta = cliente.get(ruta, params={"fecha": "2026-03-01"}, headers=CABECERA)

    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "hallazgo_no_existe"


def test_sin_fecha_o_fecha_invalida_responde_422(cliente):
    sin_fecha = cliente.get(RUTA, headers=CABECERA)
    invalida = cliente.get(RUTA, params={"fecha": "15/01/2026"}, headers=CABECERA)

    assert sin_fecha.status_code == 422
    assert invalida.status_code == 422
    assert invalida.json()["codigo"] == "peticion_invalida"
