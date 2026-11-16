from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.api.fichas import obtener_repositorio_fichas
from app.api.hallazgos import obtener_autorizador
from app.dominio.hallazgos import FichaVigente
from app.dominio.validadores import DefinicionAtributo, TipoAtributo
from app.main import app

CABECERA = {"Authorization": "Bearer token-de-prueba"}
TIPO_ID = UUID("10000000-0000-0000-0000-000000000001")
RUTA = f"/tipos-especie/{TIPO_ID}/ficha"

TEMPERATURA = DefinicionAtributo(
    "temperaturaAgua",
    TipoAtributo.NUMERO,
    obligatorio=True,
    reglas={"minimo": 0, "maximo": 40},
    publicable=True,
    etiqueta="Temperatura del agua (°C)",
)


class RepositorioFichasFalso:
    """Reemplaza a RepositorioFichas: guarda en memoria lo que recibe."""

    def __init__(self) -> None:
        self.ficha = FichaVigente(TIPO_ID, "Anfibio", 1, [TEMPERATURA])
        self.publicado = None

    def obtener_ficha_para_publicar(self, tipo_especie_id):
        return self.ficha

    def publicar_revision(self, ficha, nuevas, autor_id):
        self.publicado = (ficha, nuevas, autor_id)
        return FichaVigente(ficha.tipo_especie_id, ficha.nombre, ficha.revision + 1, nuevas)

    def cancelar(self):
        pass


@pytest.fixture
def repositorio_fichas():
    return RepositorioFichasFalso()


@pytest.fixture
def cliente_fichas(repositorio_fichas, autorizador):
    app.dependency_overrides[obtener_repositorio_fichas] = lambda: repositorio_fichas
    app.dependency_overrides[obtener_autorizador] = lambda: autorizador
    yield TestClient(app)
    app.dependency_overrides.clear()


def _cuerpo(revision_base=1):
    return {
        "revisionBase": revision_base,
        "atributos": [
            {
                "clave": "temperaturaAgua",
                "etiqueta": "Temperatura del agua (°C)",
                "tipo": "NUMERO",
                "obligatorio": True,
                "publicable": True,
                "reglas": {"minimo": 0, "maximo": 40, "unidad": "°C"},
            },
            {
                "clave": "salinidad",
                "etiqueta": "Salinidad",
                "tipo": "NUMERO",
                "reglas": {"minimo": 0},
            },
        ],
    }


def test_sin_token_responde_401(cliente_fichas, repositorio_fichas):
    respuesta = cliente_fichas.put(RUTA, json=_cuerpo())

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "no_autenticado"
    assert repositorio_fichas.publicado is None


def test_sin_permiso_responde_403_y_no_publica(cliente_fichas, repositorio_fichas, autorizador):
    autorizador.permitir = False

    respuesta = cliente_fichas.put(RUTA, json=_cuerpo(), headers=CABECERA)

    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "sin_permiso"
    assert repositorio_fichas.publicado is None


def test_publica_la_revision_nueva_y_responde_200(cliente_fichas, repositorio_fichas, autorizador):
    autorizador.usuario_id = UUID("00000000-0000-0000-0000-0000000000cc")

    respuesta = cliente_fichas.put(RUTA, json=_cuerpo(), headers=CABECERA)

    assert respuesta.status_code == 200
    ficha = respuesta.json()
    assert ficha["tipoEspecieId"] == str(TIPO_ID)
    assert ficha["revision"] == 2
    assert {a["clave"] for a in ficha["atributos"]} == {"temperaturaAgua", "salinidad"}
    salinidad = next(a for a in ficha["atributos"] if a["clave"] == "salinidad")
    assert salinidad["obligatorio"] is False
    assert salinidad["publicable"] is False
    assert autorizador.llamadas == [("token-de-prueba", "definir_ficha", None)]
    _, nuevas, autor = repositorio_fichas.publicado
    assert [d.clave for d in nuevas] == ["temperaturaAgua", "salinidad"]
    assert autor == UUID("00000000-0000-0000-0000-0000000000cc")  # el autor sale del token


def test_tipo_de_especie_inexistente_responde_404(cliente_fichas, repositorio_fichas):
    repositorio_fichas.ficha = None

    respuesta = cliente_fichas.put(RUTA, json=_cuerpo(), headers=CABECERA)

    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "ficha_no_existe"


def test_revision_desactualizada_responde_409(cliente_fichas, repositorio_fichas):
    repositorio_fichas.ficha = FichaVigente(TIPO_ID, "Anfibio", 3, [TEMPERATURA])

    respuesta = cliente_fichas.put(RUTA, json=_cuerpo(revision_base=2), headers=CABECERA)

    assert respuesta.status_code == 409
    asunto = respuesta.json()
    assert asunto["codigo"] == "conflicto_de_revision"
    assert asunto["detalles"][0]["campo"] == "revisionBase"
    assert "3" in asunto["detalles"][0]["mensaje"]
    assert repositorio_fichas.publicado is None


def test_definicion_invalida_responde_422_con_los_campos(cliente_fichas, repositorio_fichas):
    cuerpo = _cuerpo()
    cuerpo["atributos"][1]["clave"] = "Mala Clave"
    cuerpo["atributos"][0]["reglas"] = {"minimo": 50, "maximo": 10}

    respuesta = cliente_fichas.put(RUTA, json=cuerpo, headers=CABECERA)

    assert respuesta.status_code == 422
    asunto = respuesta.json()
    assert asunto["codigo"] == "definicion_invalida"
    campos = {d["campo"] for d in asunto["detalles"]}
    assert campos == {"atributos[0].reglas", "atributos[1].clave"}
    assert repositorio_fichas.publicado is None


def test_cuerpo_sin_revision_base_responde_422(cliente_fichas):
    cuerpo = _cuerpo()
    del cuerpo["revisionBase"]

    respuesta = cliente_fichas.put(RUTA, json=cuerpo, headers=CABECERA)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "peticion_invalida"


def test_tipo_de_atributo_desconocido_responde_422(cliente_fichas):
    cuerpo = _cuerpo()
    cuerpo["atributos"][0]["tipo"] = "FOTO"

    respuesta = cliente_fichas.put(RUTA, json=cuerpo, headers=CABECERA)

    assert respuesta.status_code == 422
    assert respuesta.json()["detalles"][0]["campo"] == "atributos.0.tipo"


def test_el_get_de_la_ficha_ahora_incluye_publicable(cliente, repositorio):
    respuesta = cliente.get(f"/tipos-especie/{repositorio.ficha.tipo_especie_id}/ficha")

    atributos = {a["clave"]: a for a in respuesta.json()["atributos"]}
    assert atributos["habitat"]["publicable"] is True
    assert atributos["observaciones"]["publicable"] is False
