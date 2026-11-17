
from datetime import datetime
from unittest.mock import Mock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.api import fichas as fichas_api
from app.db import obtener_sesion
from app.dominio import servicio_fichas as servicio_fichas_api
from app.main import app
from app.repositorio import fichas as repositorio_fichas

ID_HALLAZGO = "00000000-0000-0000-0000-000000000001"


@pytest.fixture
def cliente():
    def sesion_falsa():
        yield object()

    app.dependency_overrides[obtener_sesion] = sesion_falsa

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_consultar_ficha_publica_permitida(cliente, monkeypatch):
    autorizador = Mock(return_value=True)
    consulta = Mock(return_value={"especie": "Especie de prueba"})

    monkeypatch.setattr(fichas_api, "autorizar", autorizador)
    monkeypatch.setattr(fichas_api, "consultar_ficha_publica", consulta)

    respuesta = cliente.get(f"/hallazgos/{ID_HALLAZGO}")

    assert respuesta.status_code == 200
    assert respuesta.json()["especie"] == "Especie de prueba"
    autorizador.assert_called_once_with(
        None, "ver_ficha_publica", ID_HALLAZGO
    )
    consulta.assert_called_once()


def test_consultar_ficha_publica_denegada(cliente, monkeypatch):
    autorizador = Mock(return_value=False)
    consulta = Mock()

    monkeypatch.setattr(fichas_api, "autorizar", autorizador)
    monkeypatch.setattr(fichas_api, "consultar_ficha_publica", consulta)

    respuesta = cliente.get(f"/hallazgos/{ID_HALLAZGO}")

    assert respuesta.status_code == 403
    consulta.assert_not_called()


def test_consultar_ficha_inexistente(cliente, monkeypatch):
    monkeypatch.setattr(
        fichas_api, "autorizar", Mock(return_value=True)
    )
    monkeypatch.setattr(
        fichas_api, "consultar_ficha_publica", Mock(return_value=None)
    )

    respuesta = cliente.get(f"/hallazgos/{ID_HALLAZGO}")

    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == "No se encontró el hallazgo solicitado."


def test_consultar_ficha_usa_cache(cliente, monkeypatch):
    autorizador = Mock(return_value=True)
    consulta_bd = Mock()

    monkeypatch.setattr(fichas_api, "autorizar", autorizador)
    monkeypatch.setattr(
        servicio_fichas_api,
        "obtener_cache",
        Mock(return_value='{"especie": "Guacamaya roja"}')
    )
    monkeypatch.setattr(
        servicio_fichas_api,
        "obtener_ficha_publica",
        consulta_bd
    )

    respuesta = cliente.get(f"/hallazgos/{ID_HALLAZGO}")

    assert respuesta.status_code == 200
    assert respuesta.json()["especie"] == "Guacamaya roja"
    autorizador.assert_called_once_with(
        None, "ver_ficha_publica", ID_HALLAZGO
    )
    consulta_bd.assert_not_called()


def test_consultar_ficha_si_redis_falla(cliente, monkeypatch):
    autorizador = Mock(return_value=True)
    consulta_bd = Mock(return_value={"especie": "Colibrí"})
    guardar = Mock(return_value=False)

    monkeypatch.setattr(fichas_api, "autorizar", autorizador)
    monkeypatch.setattr(
        servicio_fichas_api,
        "obtener_cache",
        Mock(return_value=None)
    )
    monkeypatch.setattr(
        servicio_fichas_api,
        "obtener_ficha_publica",
        consulta_bd
    )
    monkeypatch.setattr(
        servicio_fichas_api,
        "guardar_cache",
        guardar
    )

    respuesta = cliente.get(f"/hallazgos/{ID_HALLAZGO}")

    assert respuesta.status_code == 200
    assert respuesta.json()["especie"] == "Colibrí"
    consulta_bd.assert_called_once()
    guardar.assert_called_once()


def test_ficha_publica_muestra_departamento(cliente, monkeypatch):
    ficha = {
        "especie": "Guacamaya roja",
        "region": "Amazonía",
        "departamento": "Amazonas",
        "ecosistema": "Bosque húmedo",
    }

    monkeypatch.setattr(
        fichas_api, "autorizar", Mock(return_value=True)
    )
    monkeypatch.setattr(
        fichas_api,
        "consultar_ficha_publica",
        Mock(return_value=ficha)
    )

    respuesta = cliente.get(f"/hallazgos/{ID_HALLAZGO}")

    assert respuesta.status_code == 200
    assert respuesta.json()["region"] == "Amazonía"
    assert respuesta.json()["departamento"] == "Amazonas"


def test_repositorio_no_expone_coordenadas(monkeypatch):
    fila = {
        "hallazgo_id": UUID(ID_HALLAZGO),
        "especie": "Guacamaya roja",
        "region": "Amazonía",
        "departamento": "Amazonas",
        "ecosistema": "Bosque húmedo",
        "latitud": -1.5,
        "longitud": -71.8,
        "fecha_hallazgo": datetime(2026, 11, 15, 10, 30),
        "atributos_publicos": {},
        "version": 1,
        "actualizado_en": datetime(2026, 11, 15, 11, 0),
    }

    sesion = Mock()
    sesion.execute.return_value.mappings.return_value.first.return_value = fila

    resultado = repositorio_fichas.obtener_ficha_publica(
        sesion, UUID(ID_HALLAZGO)
    )

    assert resultado["departamento"] == "Amazonas"
    assert "latitud" not in resultado
    assert "longitud" not in resultado
    assert "coordenadas" not in resultado


def test_primera_consulta_igual_a_respuesta_desde_cache(monkeypatch):
    fecha = datetime(2026, 11, 15, 10, 30)

    ficha_bd = {
        "especie": "Guacamaya roja",
        "region": "Amazonía",
        "departamento": "Amazonas",
        "fecha_hallazgo": fecha,
    }

    cache = {}

    def obtener_cache_falso(clave):
        return cache.get(clave)

    def guardar_cache_falso(clave, valor):
        cache[clave] = valor
        return True

    consulta_bd = Mock(return_value=ficha_bd)

    monkeypatch.setattr(
        servicio_fichas_api, "obtener_cache", obtener_cache_falso
    )
    monkeypatch.setattr(
        servicio_fichas_api, "guardar_cache", guardar_cache_falso
    )
    monkeypatch.setattr(
        servicio_fichas_api, "obtener_ficha_publica", consulta_bd
    )

    id_hallazgo = UUID(ID_HALLAZGO)
    sesion = Mock()

    primera_respuesta = servicio_fichas_api.consultar_ficha_publica(
        sesion, id_hallazgo
    )

    segunda_respuesta = servicio_fichas_api.consultar_ficha_publica(
        sesion, id_hallazgo
    )

    assert primera_respuesta == segunda_respuesta
    assert primera_respuesta["fecha_hallazgo"] == "2026-11-15T10:30:00"
    assert consulta_bd.call_count == 1
