"""Pruebas del patrón Decorator de la caché (Entrega 2, sección 6.2 · HU-20)."""
import json
from datetime import datetime
from unittest.mock import Mock
from uuid import UUID

import pytest

from app.dominio import servicio_fichas
from app.dominio.servicio_fichas import ConsultaBD, ConsultaCacheada, armar_consulta

ID = UUID("00000000-0000-0000-0000-000000000001")
CLAVE = f"ficha_publica:{ID}"
FICHA = {"hallazgo_id": str(ID), "especie": "Guacamaya roja", "region": "Amazonía"}


class ConsultaFalsa:
    """Cualquier IConsulta: el decorador no sabe ni le importa cuál envuelve."""

    def __init__(self, ficha):
        self.ficha = ficha
        self.llamadas = 0

    def obtener_ficha(self, hallazgo_id):
        self.llamadas += 1
        return self.ficha


@pytest.fixture
def redis_falso(monkeypatch):
    """Reemplaza Redis por un diccionario."""
    guardado = {}

    def guardar(clave, valor):
        guardado[clave] = valor
        return True

    monkeypatch.setattr(servicio_fichas, "obtener_cache", guardado.get)
    monkeypatch.setattr(servicio_fichas, "guardar_cache", guardar)
    return guardado


def test_si_no_esta_en_cache_le_pregunta_a_la_interna_y_la_guarda(redis_falso):
    interna = ConsultaFalsa(FICHA)

    ficha = ConsultaCacheada(interna).obtener_ficha(ID)

    assert ficha == FICHA
    assert interna.llamadas == 1
    assert json.loads(redis_falso[CLAVE]) == FICHA


def test_si_esta_en_cache_no_molesta_a_la_interna(redis_falso):
    redis_falso[CLAVE] = json.dumps(FICHA)
    interna = ConsultaFalsa({"especie": "otra"})

    ficha = ConsultaCacheada(interna).obtener_ficha(ID)

    assert ficha == FICHA
    assert interna.llamadas == 0


def test_la_segunda_consulta_sale_de_la_cache(redis_falso):
    interna = ConsultaFalsa(FICHA)
    consulta = ConsultaCacheada(interna)

    primera = consulta.obtener_ficha(ID)
    segunda = consulta.obtener_ficha(ID)

    assert primera == segunda
    assert interna.llamadas == 1


def test_una_ficha_que_no_existe_no_se_guarda(redis_falso):
    assert ConsultaCacheada(ConsultaFalsa(None)).obtener_ficha(ID) is None
    assert redis_falso == {}


def test_si_redis_esta_caido_responde_desde_la_interna(monkeypatch):
    monkeypatch.setattr(servicio_fichas, "obtener_cache", Mock(return_value=None))
    monkeypatch.setattr(servicio_fichas, "guardar_cache", Mock(return_value=False))
    interna = ConsultaFalsa(FICHA)
    consulta = ConsultaCacheada(interna)

    assert consulta.obtener_ficha(ID) == FICHA
    assert consulta.obtener_ficha(ID) == FICHA
    assert interna.llamadas == 2


def test_un_dato_danado_en_redis_se_ignora(redis_falso):
    redis_falso[CLAVE] = "esto no es json"
    interna = ConsultaFalsa(FICHA)

    assert ConsultaCacheada(interna).obtener_ficha(ID) == FICHA
    assert interna.llamadas == 1


def test_consulta_bd_lee_del_repositorio_y_deja_las_fechas_como_texto(monkeypatch):
    fila = {"hallazgo_id": ID, "especie": "Colibrí", "fecha_hallazgo": datetime(2026, 1, 10, 8, 0)}
    repositorio = Mock(return_value=fila)
    monkeypatch.setattr(servicio_fichas, "obtener_ficha_publica", repositorio)
    sesion = object()

    ficha = ConsultaBD(sesion).obtener_ficha(ID)

    repositorio.assert_called_once_with(sesion, ID)
    assert ficha == {"hallazgo_id": str(ID), "especie": "Colibrí", "fecha_hallazgo": "2026-01-10T08:00:00"}


def test_la_cache_nunca_guarda_coordenadas(redis_falso):
    """Aunque la base trajera coordenadas por error, el repositorio las filtra antes de la caché (RNF-05)."""
    fila = {
        "hallazgo_id": ID,
        "especie": "Rana dorada",
        "region": "Pacífico",
        "latitud": 2.5,
        "longitud": -77.0,
    }
    sesion = Mock()
    sesion.execute.return_value.mappings.return_value.first.return_value = fila

    armar_consulta(sesion).obtener_ficha(ID)

    guardado = json.loads(redis_falso[CLAVE])
    assert guardado["especie"] == "Rana dorada"
    assert "latitud" not in guardado and "longitud" not in guardado


def test_armar_consulta_pone_la_cache_delante_de_la_base():
    consulta = armar_consulta(sesion=object())

    assert isinstance(consulta, ConsultaCacheada)
    assert isinstance(consulta._interna, ConsultaBD)
