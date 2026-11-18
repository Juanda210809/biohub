import pytest
from fastapi.testclient import TestClient

from app.api import externa
from app.db import obtener_sesion
from app.main import app

cliente = TestClient(app)


class ResultadoFalso:
    def __init__(self, filas):
        self.filas = filas

    def mappings(self):
        return self.filas


class SesionFalsa:
    def __init__(self):
        self.filas = []
        self.consultas = []

    def execute(self, consulta, parametros):
        self.consultas.append((consulta, parametros))
        return ResultadoFalso(self.filas)


@pytest.fixture
def entorno(monkeypatch):
    sesion = SesionFalsa()
    permisos = {"permitido": True, "llamadas": []}

    def autorizar_falso(*args, **kwargs):
        permisos["llamadas"].append((args, kwargs))
        return permisos["permitido"]

    monkeypatch.setattr(externa, "autorizar", autorizar_falso)
    monkeypatch.setitem(app.dependency_overrides, obtener_sesion, lambda: sesion)
    return sesion, permisos


@pytest.fixture
def fila_publica():
    return {
        "hallazgo_id": "hallazgo-1",
        "especie": "Quercus humboldtii",
        "region": "Andina",
        "departamento": "Cundinamarca",
        "ecosistema": "Bosque andino",
        "fecha_hallazgo": "2026-11-01",
        "atributos_publicos": {"nombre_comun": "Roble"},
        "version": 1,
        "actualizado_en": "2026-11-01T12:00:00",
    }


def test_hallazgos_permitidos(entorno, fila_publica):
    sesion, permisos = entorno
    sesion.filas = [fila_publica, {**fila_publica, "hallazgo_id": "hallazgo-2"}]

    respuesta = cliente.get("/externa/hallazgos")

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "hallazgos": sesion.filas,
        "limite": 50,
        "desplazamiento": 0,
        "cantidad": 2,
    }
    assert permisos["llamadas"] == [((None, "ver_ficha_publica"), {})]


def test_hallazgos_denegados_no_consultan_sesion(entorno, monkeypatch):
    sesion, permisos = entorno
    permisos["permitido"] = False

    def consulta_prohibida(*args, **kwargs):
        pytest.fail("No debe consultar hallazgos sin permiso")

    monkeypatch.setattr(externa, "listar_hallazgos_publicos", consulta_prohibida)

    respuesta = cliente.get("/externa/hallazgos")

    assert respuesta.status_code == 403
    assert respuesta.json() == {"detail": "Sin permiso"}
    assert permisos["llamadas"] == [((None, "ver_ficha_publica"), {})]
    assert sesion.consultas == []


def test_hallazgos_solo_incluyen_campos_publicos(entorno, fila_publica):
    sesion, _ = entorno
    extras = {"latitud", "longitud", "ubicacion", "geom", "precision"}
    sesion.filas = [{**fila_publica, **dict.fromkeys(extras, "dato privado")}]

    respuesta = cliente.get("/externa/hallazgos")

    assert respuesta.status_code == 200
    hallazgos = respuesta.json()["hallazgos"]
    assert hallazgos == [fila_publica]
    assert "departamento" in externa.CAMPOS_PUBLICOS
    for hallazgo in hallazgos:
        assert set(hallazgo) == set(externa.CAMPOS_PUBLICOS)
        assert extras.isdisjoint(hallazgo)
        assert hallazgo["departamento"] == "Cundinamarca"


@pytest.mark.parametrize(
    ("parametros", "limite", "desplazamiento"),
    [
        ({}, 50, 0),
        ({"limite": 1, "desplazamiento": 7}, 1, 7),
        ({"limite": 100, "desplazamiento": 0}, 100, 0),
    ],
)
def test_paginacion_llega_a_la_consulta(entorno, parametros, limite, desplazamiento):
    sesion, _ = entorno

    respuesta = cliente.get("/externa/hallazgos", params=parametros)

    assert respuesta.status_code == 200
    assert respuesta.json()["limite"] == limite
    assert respuesta.json()["desplazamiento"] == desplazamiento
    assert len(sesion.consultas) == 1
    consulta, valores = sesion.consultas[0]
    assert consulta is externa.CONSULTA_HALLAZGOS
    assert valores == {"limite": limite, "desplazamiento": desplazamiento}
    sql = " ".join(str(consulta).split())
    assert f"SELECT {', '.join(externa.CAMPOS_PUBLICOS)} FROM campo.hallazgo_publico" in sql
    assert "LIMIT :limite OFFSET :desplazamiento" in sql


@pytest.mark.parametrize("parametros", [{"limite": 0}, {"limite": 101}, {"desplazamiento": -1}])
def test_paginacion_invalida_no_llama_pdp_ni_consulta(entorno, parametros):
    sesion, permisos = entorno

    respuesta = cliente.get("/externa/hallazgos", params=parametros)

    assert respuesta.status_code == 422
    assert permisos["llamadas"] == []
    assert sesion.consultas == []


def test_hallazgos_vacios(entorno):
    sesion, _ = entorno

    respuesta = cliente.get("/externa/hallazgos")

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "hallazgos": [],
        "limite": 50,
        "desplazamiento": 0,
        "cantidad": 0,
    }
    assert len(sesion.consultas) == 1
