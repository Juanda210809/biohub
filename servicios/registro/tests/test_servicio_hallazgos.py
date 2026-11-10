from dataclasses import replace

import pytest

from app.dominio.servicio_hallazgos import (
    EspecieNoExiste,
    ExpedicionNoExiste,
    FichaInvalida,
    ServicioHallazgos,
)


def test_registra_y_guarda_solo_los_atributos_publicos(repositorio, datos):
    hallazgo_id = ServicioHallazgos(repositorio).registrar(datos)

    guardado, nombre_especie, publicos = repositorio.registrado
    assert hallazgo_id == repositorio.hallazgo_id
    assert guardado is datos
    assert nombre_especie == "Phyllobates terribilis"
    assert publicos == {"temperaturaAgua": 18.5, "habitat": "quebrada"}


def test_especie_que_no_existe(repositorio, datos):
    repositorio.especie = None

    with pytest.raises(EspecieNoExiste):
        ServicioHallazgos(repositorio).registrar(datos)
    assert repositorio.registrado is None


def test_expedicion_que_no_existe(repositorio, datos):
    repositorio.expedicion_existe = False

    with pytest.raises(ExpedicionNoExiste):
        ServicioHallazgos(repositorio).registrar(datos)
    assert repositorio.registrado is None


def test_ficha_invalida_no_guarda_nada(repositorio, datos):
    malos = replace(datos, atributos={"temperaturaAgua": 99})

    with pytest.raises(FichaInvalida) as error:
        ServicioHallazgos(repositorio).registrar(malos)

    assert error.value.errores == [
        {"campo": "temperaturaAgua", "mensaje": "debe ser menor o igual a 40"}
    ]
    assert repositorio.registrado is None


def test_falta_un_atributo_obligatorio(repositorio, datos):
    sin_atributos = replace(datos, atributos={})

    with pytest.raises(FichaInvalida) as error:
        ServicioHallazgos(repositorio).registrar(sin_atributos)

    assert error.value.errores == [{"campo": "temperaturaAgua", "mensaje": "es obligatorio"}]
    assert repositorio.registrado is None
