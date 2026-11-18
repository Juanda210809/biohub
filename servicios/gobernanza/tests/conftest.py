"""Falsos y fixtures compartidos: las pruebas de Gobernanza no usan base de datos ni el PDP real."""
from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.api.reclasificaciones import obtener_autorizador, obtener_repositorio
from app.autorizacion import DecisionPDP
from app.dominio.reclasificacion import Especie, HallazgoActual, Reclasificacion
from app.main import app

HALLAZGO_ID = UUID("80b22314-d956-4eb1-a17a-0f3bd23f23f2")
ESPECIE_ACTUAL_ID = UUID("20000000-0000-0000-0000-000000000002")
ESPECIE_NUEVA_ID = UUID("20000000-0000-0000-0000-000000000003")
CIENTIFICO_ID = UUID("00000000-0000-0000-0000-0000000000ab")
INSTANTE = datetime(2026, 11, 18, 15, 0, tzinfo=UTC)


class RepositorioFalso:
    """Reemplaza a RepositorioGobernanza: guarda en memoria lo que recibe."""

    def __init__(self) -> None:
        self.hallazgo = HallazgoActual(HALLAZGO_ID, ESPECIE_ACTUAL_ID, "Setophaga cerulea", 1)
        self.especies = {ESPECIE_NUEVA_ID: Especie(ESPECIE_NUEVA_ID, "Thraupis episcopus")}
        self.guardado = None
        self.descartado = False

    def obtener_hallazgo(self, hallazgo_id):
        return self.hallazgo if self.hallazgo and self.hallazgo.id == hallazgo_id else None

    def obtener_especie(self, especie_id):
        return self.especies.get(especie_id)

    def descartar(self):
        self.descartado = True

    def reclasificar(self, hallazgo, especie, justificacion, autor_id):
        self.guardado = (hallazgo, especie, justificacion, autor_id)
        return Reclasificacion(
            hallazgo_id=hallazgo.id,
            version=hallazgo.version_actual + 1,
            especie_anterior=hallazgo.especie_nombre,
            especie_nueva=especie.nombre_cientifico,
            autor_id=autor_id,
            justificacion=justificacion,
            vigente_desde=INSTANTE,
        )


class AutorizadorFalso:
    """Reemplaza al PDP: responde lo que le digas y recuerda con qué le preguntaron."""

    def __init__(self) -> None:
        self.permitir = True
        self.usuario_id = CIENTIFICO_ID
        self.llamadas = []

    def __call__(self, token, accion, recurso):
        self.llamadas.append((token, accion, recurso))
        if not self.permitir:
            return DecisionPDP(False, "Denegado por el falso")
        return DecisionPDP(True, "Permitido por el falso", self.usuario_id, "CIENTIFICO_AUTORIZADO")


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
    return {"especieId": str(ESPECIE_NUEVA_ID), "justificacion": "Análisis genético del laboratorio"}
