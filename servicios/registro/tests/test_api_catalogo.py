from datetime import date
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.api.catalogo import obtener_repositorio_catalogo
from app.api.hallazgos import obtener_autorizador
from app.dominio.catalogo import EspecieCatalogo, ExpedicionCatalogo
from app.main import app
from app.repositorio.catalogo import SQL_ESPECIES, SQL_EXPEDICIONES, RepositorioCatalogo

CABECERA = {"Authorization": "Bearer token-de-prueba"}
CONSULTA_PDP = ("token-de-prueba", "consultar_catalogo", None)
TIPO_ID = UUID("10000000-0000-0000-0000-000000000001")
ESPECIE_ID = UUID("20000000-0000-0000-0000-000000000001")
EXPEDICION_ID = UUID("30000000-0000-0000-0000-000000000001")


class RepositorioCatalogoFalso:
    def __init__(self, autorizador):
        self.autorizador = autorizador
        self.especies = []
        self.expediciones = []
        self.llamadas = []
        self.consultas_pdp_al_leer = []

    def listar_especies(self):
        self.llamadas.append("especies")
        self.consultas_pdp_al_leer.append(list(self.autorizador.llamadas))
        return self.especies

    def listar_expediciones(self):
        self.llamadas.append("expediciones")
        self.consultas_pdp_al_leer.append(list(self.autorizador.llamadas))
        return self.expediciones


@pytest.fixture
def repositorio_catalogo(autorizador):
    return RepositorioCatalogoFalso(autorizador)


@pytest.fixture
def cliente_catalogo(repositorio_catalogo, autorizador):
    app.dependency_overrides[obtener_repositorio_catalogo] = lambda: repositorio_catalogo
    app.dependency_overrides[obtener_autorizador] = lambda: autorizador
    try:
        with TestClient(app) as cliente:
            yield cliente
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize("ruta", ["/especies", "/expediciones"])
def test_sin_token_responde_401(cliente_catalogo, repositorio_catalogo, autorizador, ruta):
    respuesta = cliente_catalogo.get(ruta)

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "no_autenticado"
    assert autorizador.llamadas == []
    assert repositorio_catalogo.llamadas == []


@pytest.mark.parametrize("ruta", ["/especies", "/expediciones"])
def test_sin_permiso_responde_403_sin_leer(
    cliente_catalogo, repositorio_catalogo, autorizador, ruta,
):
    autorizador.permitir = False

    respuesta = cliente_catalogo.get(ruta, headers=CABECERA)

    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "sin_permiso"
    assert autorizador.llamadas == [CONSULTA_PDP]
    assert repositorio_catalogo.llamadas == []


@pytest.mark.parametrize("nombre_comun", ["Rana dorada", None])
def test_especies_responde_200_en_camel_case(
    cliente_catalogo, repositorio_catalogo, autorizador, nombre_comun,
):
    repositorio_catalogo.especies = [
        EspecieCatalogo(ESPECIE_ID, "Phyllobates terribilis", nombre_comun, TIPO_ID, "Anfibio"),
    ]

    respuesta = cliente_catalogo.get("/especies", headers=CABECERA)

    assert respuesta.status_code == 200
    assert respuesta.json() == [{
        "id": str(ESPECIE_ID),
        "nombreCientifico": "Phyllobates terribilis",
        "nombreComun": nombre_comun,
        "tipoEspecieId": str(TIPO_ID),
        "tipoEspecie": "Anfibio",
    }]
    assert autorizador.llamadas == [CONSULTA_PDP]
    assert repositorio_catalogo.llamadas == ["especies"]
    assert repositorio_catalogo.consultas_pdp_al_leer == [[CONSULTA_PDP]]


@pytest.mark.parametrize("fecha_fin", [date(2026, 10, 25), None])
def test_expediciones_responde_200_en_camel_case(
    cliente_catalogo, repositorio_catalogo, autorizador, fecha_fin,
):
    repositorio_catalogo.expediciones = [
        ExpedicionCatalogo(EXPEDICION_ID, "Pacifico", date(2026, 10, 20), fecha_fin),
    ]

    respuesta = cliente_catalogo.get("/expediciones", headers=CABECERA)

    assert respuesta.status_code == 200
    assert respuesta.json() == [{
        "id": str(EXPEDICION_ID),
        "nombre": "Pacifico",
        "fechaInicio": "2026-10-20",
        "fechaFin": fecha_fin.isoformat() if fecha_fin else None,
    }]
    assert autorizador.llamadas == [CONSULTA_PDP]
    assert repositorio_catalogo.llamadas == ["expediciones"]
    assert repositorio_catalogo.consultas_pdp_al_leer == [[CONSULTA_PDP]]


@pytest.mark.parametrize("catalogo", ["especies", "expediciones"])
def test_lista_vacia_responde_200(
    cliente_catalogo, repositorio_catalogo, autorizador, catalogo,
):
    respuesta = cliente_catalogo.get(f"/{catalogo}", headers=CABECERA)

    assert respuesta.status_code == 200
    assert respuesta.json() == []
    assert autorizador.llamadas == [CONSULTA_PDP]
    assert repositorio_catalogo.llamadas == [catalogo]
    assert repositorio_catalogo.consultas_pdp_al_leer == [[CONSULTA_PDP]]


class ResultadoFalso:
    def __init__(self, filas):
        self.filas = filas

    def all(self):
        return self.filas


class SesionFalsa:
    def __init__(self, filas):
        self.filas = filas
        self.consultas = []

    def execute(self, consulta):
        self.consultas.append(consulta)
        return ResultadoFalso(self.filas)


def test_repositorio_especies_usa_sql_y_convierte_filas():
    filas = [
        SimpleNamespace(
            id=ESPECIE_ID,
            nombre_cientifico="Phyllobates terribilis",
            nombre_comun="Rana dorada",
            tipo_especie_id=TIPO_ID,
            tipo_especie="Anfibio",
        ),
        SimpleNamespace(
            id=UUID("20000000-0000-0000-0000-000000000002"),
            nombre_cientifico="Pristimantis bogotensis",
            nombre_comun=None,
            tipo_especie_id=TIPO_ID,
            tipo_especie="Anfibio",
        ),
    ]
    sesion = SesionFalsa(filas)

    resultado = RepositorioCatalogo(sesion).listar_especies()

    assert len(sesion.consultas) == 1
    assert sesion.consultas[0] is SQL_ESPECIES
    assert resultado == [
        EspecieCatalogo(ESPECIE_ID, "Phyllobates terribilis", "Rana dorada", TIPO_ID, "Anfibio"),
        EspecieCatalogo(filas[1].id, "Pristimantis bogotensis", None, TIPO_ID, "Anfibio"),
    ]
    assert all(isinstance(especie, EspecieCatalogo) for especie in resultado)


def test_repositorio_expediciones_usa_sql_y_convierte_filas():
    filas = [
        SimpleNamespace(
            id=EXPEDICION_ID, nombre="Pacifico",
            fecha_inicio=date(2026, 10, 20), fecha_fin=None,
        ),
        SimpleNamespace(
            id=UUID("30000000-0000-0000-0000-000000000002"), nombre="Andes",
            fecha_inicio=date(2026, 9, 10), fecha_fin=date(2026, 9, 15),
        ),
    ]
    sesion = SesionFalsa(filas)

    resultado = RepositorioCatalogo(sesion).listar_expediciones()

    assert len(sesion.consultas) == 1
    assert sesion.consultas[0] is SQL_EXPEDICIONES
    assert resultado == [
        ExpedicionCatalogo(EXPEDICION_ID, "Pacifico", date(2026, 10, 20), None),
        ExpedicionCatalogo(filas[1].id, "Andes", date(2026, 9, 10), date(2026, 9, 15)),
    ]
    assert all(isinstance(expedicion, ExpedicionCatalogo) for expedicion in resultado)


@pytest.mark.parametrize("metodo, sql", [
    ("listar_especies", SQL_ESPECIES),
    ("listar_expediciones", SQL_EXPEDICIONES),
])
def test_repositorio_sin_filas_devuelve_lista_vacia(metodo, sql):
    sesion = SesionFalsa([])

    resultado = getattr(RepositorioCatalogo(sesion), metodo)()

    assert resultado == []
    assert len(sesion.consultas) == 1
    assert sesion.consultas[0] is sql
