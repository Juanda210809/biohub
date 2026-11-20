
from unittest.mock import Mock
from uuid import UUID

import pytest

from app.repositorio.hallazgos import (
    ACCION_CONSULTAR_UBICACION,
    RepositorioHallazgos,
    SQL_AUDITORIA,
    SQL_UBICACION_EXACTA,
    SQL_UBICACION_GENERAL,
)

HALLAZGO_ID = UUID("80b22314-d956-4eb1-a17a-0f3bd23f23f2")
ACTOR_ID = UUID("00000000-0000-0000-0000-0000000000aa")


@pytest.fixture
def sesion():
    return Mock()


@pytest.fixture
def repositorio(sesion):
    return RepositorioHallazgos(sesion)


def fila_ubicacion(exacta=False):
    datos = {
        "region": "Pacifico",
        "departamento": "Cauca",
    }

    if exacta:
        datos.update({
            "latitud": 2.512345,
            "longitud": -77.123456,
            "precision_m": 5,
        })

    return Mock(**datos)


def test_consulta_regional_registra_auditoria_sin_coordenadas(
    repositorio, sesion
):
    sesion.execute.return_value.first.return_value = fila_ubicacion()

    resultado = repositorio.obtener_ubicacion(
        HALLAZGO_ID, ACTOR_ID, incluir_exacta=False
    )

    assert resultado["nivel_ubicacion"] == "REGION"
    assert resultado["region"] == "Pacifico"
    assert resultado["departamento"] == "Cauca"
    assert "latitud" not in resultado
    assert "longitud" not in resultado
    assert "precision_m" not in resultado

    assert sesion.execute.call_args_list[0].args[0] == SQL_UBICACION_GENERAL
    assert sesion.execute.call_args_list[1].args[0] == SQL_AUDITORIA
    assert sesion.execute.call_args_list[1].args[1]["actor_id"] == ACTOR_ID
    assert sesion.execute.call_args_list[1].args[1]["accion"] == ACCION_CONSULTAR_UBICACION
    assert sesion.execute.call_args_list[1].args[1]["recurso_id"] == HALLAZGO_ID
    sesion.commit.assert_called_once()


def test_consulta_exacta_registra_auditoria_y_devuelve_coordenadas(
    repositorio, sesion
):
    sesion.execute.return_value.first.return_value = fila_ubicacion(exacta=True)

    resultado = repositorio.obtener_ubicacion(
        HALLAZGO_ID, ACTOR_ID, incluir_exacta=True
    )

    assert resultado["nivel_ubicacion"] == "EXACTA"
    assert resultado["latitud"] == 2.512345
    assert resultado["longitud"] == -77.123456
    assert resultado["precision_m"] == 5

    assert sesion.execute.call_args_list[0].args[0] == SQL_UBICACION_EXACTA
    assert sesion.execute.call_args_list[1].args[0] == SQL_AUDITORIA
    sesion.commit.assert_called_once()


def test_hallazgo_inexistente_no_registra_auditoria(
    repositorio, sesion
):
    sesion.execute.return_value.first.return_value = None

    resultado = repositorio.obtener_ubicacion(
        HALLAZGO_ID, ACTOR_ID, incluir_exacta=False
    )

    assert resultado is None
    assert sesion.execute.call_count == 1
    sesion.execute.assert_called_once_with(
        SQL_UBICACION_GENERAL,
        {"hallazgo_id": HALLAZGO_ID},
    )
    sesion.commit.assert_not_called()


def test_error_en_consulta_hace_rollback(repositorio, sesion):
    sesion.execute.side_effect = RuntimeError("Error de base de datos")

    with pytest.raises(RuntimeError, match="Error de base de datos"):
        repositorio.obtener_ubicacion(
            HALLAZGO_ID, ACTOR_ID, incluir_exacta=False
        )

    sesion.rollback.assert_called_once()
    sesion.commit.assert_not_called()


def test_error_al_auditar_hace_rollback(repositorio, sesion):
    sesion.execute.side_effect = [
        Mock(first=Mock(return_value=fila_ubicacion())),
        RuntimeError("Error de auditoria"),
    ]

    with pytest.raises(RuntimeError, match="Error de auditoria"):
        repositorio.obtener_ubicacion(
            HALLAZGO_ID, ACTOR_ID, incluir_exacta=False
        )

    sesion.rollback.assert_called_once()
    sesion.commit.assert_not_called()
