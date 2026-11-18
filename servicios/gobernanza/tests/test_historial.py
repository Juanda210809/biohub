from datetime import UTC, date, datetime

import pytest

from app.dominio.historial import (
    HallazgoSinHistorial,
    ServicioHistorial,
    SinVersionEnFecha,
    Version,
    comparar,
    fin_del_dia,
)
from tests.conftest import CIENTIFICO_ID, HALLAZGO_ID, VERSIONES


def _version(especie="A", atributos=None):
    return Version(1, especie, atributos or {}, CIENTIFICO_ID, "j", datetime(2026, 1, 1, tzinfo=UTC))


def test_el_dia_se_cuenta_en_hora_de_colombia():
    # El 1 de junio termina en Colombia a las 05:00 UTC del 2 de junio.
    assert fin_del_dia(date(2026, 6, 1)) == datetime(2026, 6, 2, 5, 0, tzinfo=UTC)


def test_una_version_de_las_11_pm_en_colombia_cuenta_para_ese_dia(repositorio):
    # 03:30 UTC del 2 de junio = 10:30 p. m. del 1 de junio en Colombia.
    repositorio.versiones[1] = Version(
        2, "Thraupis episcopus", {}, CIENTIFICO_ID, "x", datetime(2026, 6, 2, 3, 30, tzinfo=UTC)
    )

    reconstruccion = ServicioHistorial(repositorio).reconstruir(HALLAZGO_ID, date(2026, 6, 1))

    assert reconstruccion.en_fecha.numero == 2


def test_comparar_detecta_especie_y_atributos_nuevos_cambiados_y_quitados():
    antes = _version("A", {"altura": 1, "color": "rojo", "viejo": True})
    ahora = _version("B", {"altura": 2, "color": "rojo", "nuevo": 5})

    cambios = [(c.campo, c.antes, c.ahora) for c in comparar(antes, ahora)]

    assert cambios == [
        ("especie", "A", "B"),
        ("atributos.altura", 1, 2),
        ("atributos.nuevo", None, 5),
        ("atributos.viejo", True, None),
    ]


def test_sin_cambios_la_lista_queda_vacia():
    assert comparar(VERSIONES[0], VERSIONES[0]) == []


def test_hallazgo_sin_versiones(repositorio):
    repositorio.versiones = []

    with pytest.raises(HallazgoSinHistorial):
        ServicioHistorial(repositorio).reconstruir(HALLAZGO_ID, date(2026, 3, 1))


def test_fecha_anterior_al_registro(repositorio):
    with pytest.raises(SinVersionEnFecha) as error:
        ServicioHistorial(repositorio).reconstruir(HALLAZGO_ID, date(2026, 1, 9))

    assert error.value.primera_version == VERSIONES[0].vigente_desde
