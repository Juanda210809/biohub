"""Falsos y fixtures compartidos: las pruebas unitarias de Reportes no usan base ni PDP real."""
import os

os.environ.setdefault("REPORTES_AUTOMATICO", "0")  # sin hilo automático durante las pruebas

from datetime import UTC, datetime  # noqa: E402
from uuid import UUID  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.api.dependencias import obtener_autorizador, obtener_repositorio  # noqa: E402
from app.api.indices import obtener_reloj  # noqa: E402
from app.autorizacion import DecisionPDP  # noqa: E402
from app.dominio.indices import Conteo, ReporteMensual  # noqa: E402
from app.main import app  # noqa: E402
from tests.bd_real import bd, servidor  # noqa: E402, F401  (fixtures de las pruebas de integración)

ALTO_RANGO_ID = UUID("00000000-0000-0000-0000-0000000000ac")
# "Ahora" fijo para las pruebas: 20 de noviembre de 2026 a mediodía en Colombia.
AHORA = datetime(2026, 11, 20, 17, 0, tzinfo=UTC)


class RepositorioFalso:
    """Reemplaza a RepositorioIndicesSql: cuenta desde una lista en memoria y guarda lo que recibe."""

    def __init__(self) -> None:
        # (fecha, ecosistema, especie)
        self.hallazgos = []
        self.guardados = {}
        self.llamadas_contar = []

    def contar(self, desde, hasta):
        self.llamadas_contar.append((desde, hasta))
        por_eco = {}
        for fecha, ecosistema, especie in self.hallazgos:
            if desde <= fecha < hasta:
                por_eco.setdefault(ecosistema, []).append(especie)
        return [Conteo(e, len(ss), len(set(ss))) for e, ss in por_eco.items()]

    def guardar(self, periodo, indices, origen, solicitado_por):
        reporte = ReporteMensual(periodo, origen, solicitado_por, AHORA, indices)
        self.guardados[periodo.inicio] = reporte
        return reporte

    def obtener(self, periodo):
        return self.guardados.get(periodo.inicio)


class AutorizadorFalso:
    def __init__(self) -> None:
        self.permitir = True
        self.llamadas = []

    def __call__(self, token, accion, recurso):
        self.llamadas.append((token, accion, recurso))
        if not self.permitir:
            return DecisionPDP(False, "Denegado por el falso")
        return DecisionPDP(True, "Permitido por el falso", ALTO_RANGO_ID, "ALTO_RANGO")


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
    app.dependency_overrides[obtener_reloj] = lambda: (lambda: AHORA)
    yield TestClient(app)
    app.dependency_overrides.clear()
