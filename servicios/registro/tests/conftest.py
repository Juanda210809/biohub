"""Falsos y fixtures compartidos: las pruebas de Registro no usan base de datos ni el PDP real."""
from datetime import date
from decimal import Decimal
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.api.hallazgos import obtener_autorizador, obtener_repositorio
from app.dominio.hallazgos import Especie, FichaVigente, NuevoHallazgo
from app.dominio.validadores import DefinicionAtributo, TipoAtributo
from app.main import app

TIPO_ID = UUID("10000000-0000-0000-0000-000000000001")
ESPECIE_ID = UUID("20000000-0000-0000-0000-000000000001")
EXPEDICION_ID = UUID("30000000-0000-0000-0000-000000000001")
HALLAZGO_ID = UUID("80b22314-d956-4eb1-a17a-0f3bd23f23f2")
INVESTIGADOR_ID = UUID("00000000-0000-0000-0000-0000000000aa")

# Igual que en la base: ordenadas por clave.
DEFINICIONES = [
    DefinicionAtributo(
        "habitat",
        TipoAtributo.SELECCION,
        reglas={"opciones": ["quebrada", "charca"]},
        publicable=True,
        etiqueta="Hábitat",
    ),
    DefinicionAtributo(
        "observaciones",
        TipoAtributo.TEXTO,
        reglas={"longitudMaxima": 500},
        publicable=False,
        etiqueta="Observaciones",
    ),
    DefinicionAtributo(
        "temperaturaAgua",
        TipoAtributo.NUMERO,
        obligatorio=True,
        reglas={"minimo": 0, "maximo": 40},
        publicable=True,
        etiqueta="Temperatura del agua (°C)",
    ),
]


class RepositorioFalso:
    """Reemplaza a RepositorioHallazgos: guarda en memoria lo que recibe."""

    def __init__(self) -> None:
        self.especie = Especie(ESPECIE_ID, TIPO_ID, "Phyllobates terribilis")
        self.expedicion_existe = True
        self.definiciones = list(DEFINICIONES)
        self.ficha = FichaVigente(TIPO_ID, "Anfibio", 1, list(DEFINICIONES))
        self.hallazgo_id = HALLAZGO_ID
        self.registrado = None

    def obtener_especie(self, especie_id):
        return self.especie

    def existe_expedicion(self, expedicion_id):
        return self.expedicion_existe

    def definiciones_vigentes(self, tipo_especie_id):
        return self.definiciones

    def obtener_ficha_vigente(self, tipo_especie_id):
        return self.ficha

    def registrar(self, datos, nombre_especie, publicos):
        self.registrado = (datos, nombre_especie, publicos)
        return self.hallazgo_id


class AutorizadorFalso:
    """Reemplaza al PDP: responde lo que le digas y recuerda con qué le preguntaron."""

    def __init__(self) -> None:
        self.permitir = True
        self.llamadas = []

    def __call__(self, token, accion, recurso):
        self.llamadas.append((token, accion, recurso))
        return self.permitir


@pytest.fixture
def repositorio():
    return RepositorioFalso()


@pytest.fixture
def autorizador():
    return AutorizadorFalso()


@pytest.fixture
def cliente(repositorio, autorizador):
    app.dependency_overrides[obtener_repositorio] = lambda: repositorio
    app.dependency_overrides[obtener_autorizador] = lambda: autorizador
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def cuerpo():
    """Un cuerpo válido para POST /hallazgos (cada prueba recibe su propia copia)."""
    return {
        "especieId": str(ESPECIE_ID),
        "expedicionId": str(EXPEDICION_ID),
        "fechaHallazgo": "2026-10-20",
        "latitud": 2.512345,
        "longitud": -77.123456,
        "precisionM": 5,
        "region": "Pacifico",
        "departamento": "Cauca",
        "ecosistema": "Bosque humedo",
        "atributos": {"temperaturaAgua": 18.5, "habitat": "quebrada", "observaciones": "cerca"},
    }


@pytest.fixture
def datos():
    """El mismo hallazgo, ya como objeto del dominio."""
    return NuevoHallazgo(
        especie_id=ESPECIE_ID,
        expedicion_id=EXPEDICION_ID,
        investigador_id=INVESTIGADOR_ID,
        fecha_hallazgo=date(2026, 10, 20),
        latitud=Decimal("2.512345"),
        longitud=Decimal("-77.123456"),
        precision_m=Decimal("5"),
        region="Pacifico",
        departamento="Cauca",
        ecosistema="Bosque humedo",
        atributos={"temperaturaAgua": 18.5, "habitat": "quebrada", "observaciones": "cerca"},
    )
