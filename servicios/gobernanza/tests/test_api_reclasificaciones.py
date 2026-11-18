from uuid import UUID, uuid4

from tests.conftest import CIENTIFICO_ID, ESPECIE_ACTUAL_ID, HALLAZGO_ID

CABECERA = {"Authorization": "Bearer token-de-prueba"}
RUTA = f"/hallazgos/{HALLAZGO_ID}/reclasificaciones"


def test_sin_token_responde_401(cliente, repositorio, cuerpo):
    respuesta = cliente.post(RUTA, json=cuerpo)

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "no_autenticado"
    assert repositorio.guardado is None


def test_sin_permiso_responde_403_y_no_guarda(cliente, repositorio, autorizador, cuerpo):
    autorizador.permitir = False

    respuesta = cliente.post(RUTA, json=cuerpo, headers=CABECERA)

    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "sin_permiso"
    assert repositorio.guardado is None


def test_reclasifica_y_responde_la_version_nueva(cliente, repositorio, autorizador, cuerpo):
    respuesta = cliente.post(RUTA, json=cuerpo, headers=CABECERA)

    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["hallazgoId"] == str(HALLAZGO_ID)
    assert datos["version"] == 2
    assert datos["especieAnterior"] == "Setophaga cerulea"
    assert datos["especieNueva"] == "Thraupis episcopus"
    assert datos["justificacion"] == "Análisis genético del laboratorio"
    assert autorizador.llamadas == [("token-de-prueba", "reclasificar", str(HALLAZGO_ID))]


def test_quien_autoriza_sale_del_token(cliente, repositorio, autorizador, cuerpo):
    otro = UUID("00000000-0000-0000-0000-0000000000cc")
    autorizador.usuario_id = otro
    cuerpo["autorId"] = str(CIENTIFICO_ID)  # aunque lo manden en el cuerpo, se ignora

    respuesta = cliente.post(RUTA, json=cuerpo, headers=CABECERA)

    assert respuesta.status_code == 201
    assert respuesta.json()["autorId"] == str(otro)
    assert repositorio.guardado[3] == otro


def test_sin_justificacion_responde_422_y_no_guarda(cliente, repositorio, cuerpo):
    cuerpo["justificacion"] = "   "

    respuesta = cliente.post(RUTA, json=cuerpo, headers=CABECERA)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "peticion_invalida"
    assert respuesta.json()["detalles"][0]["campo"] == "justificacion"
    assert repositorio.guardado is None


def test_justificacion_ausente_responde_422(cliente, repositorio, cuerpo):
    del cuerpo["justificacion"]

    respuesta = cliente.post(RUTA, json=cuerpo, headers=CABECERA)

    assert respuesta.status_code == 422
    assert repositorio.guardado is None


def test_la_justificacion_se_guarda_sin_espacios_sobrantes(cliente, repositorio, cuerpo):
    cuerpo["justificacion"] = "  Nueva evidencia  "

    respuesta = cliente.post(RUTA, json=cuerpo, headers=CABECERA)

    assert respuesta.status_code == 201
    assert repositorio.guardado[2] == "Nueva evidencia"


def test_hallazgo_inexistente_responde_404(cliente, cuerpo):
    respuesta = cliente.post(f"/hallazgos/{uuid4()}/reclasificaciones", json=cuerpo, headers=CABECERA)

    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "hallazgo_no_existe"


def test_especie_inexistente_responde_404(cliente, repositorio, cuerpo):
    cuerpo["especieId"] = str(uuid4())

    respuesta = cliente.post(RUTA, json=cuerpo, headers=CABECERA)

    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "especie_no_existe"
    assert repositorio.guardado is None


def test_misma_especie_responde_409(cliente, repositorio, cuerpo):
    cuerpo["especieId"] = str(ESPECIE_ACTUAL_ID)

    respuesta = cliente.post(RUTA, json=cuerpo, headers=CABECERA)

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "misma_especie"
    assert repositorio.guardado is None
