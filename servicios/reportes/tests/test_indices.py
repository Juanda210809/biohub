from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from app.dominio.indices import (
    Conteo,
    Periodo,
    PeriodoInvalido,
    ServicioIndices,
    calcular,
    nivel_de,
)
from tests.conftest import AHORA


@pytest.mark.parametrize("texto", ["2026-13", "2026-1", "26-10", "octubre", "2026/10", ""])
def test_periodo_invalido(texto):
    with pytest.raises(PeriodoInvalido):
        Periodo.desde_texto(texto)


def test_periodo_cruza_el_cambio_de_anio():
    enero = Periodo.desde_texto("2027-01")

    assert enero.desplazar(-3).texto == "2026-10"
    assert Periodo.desde_texto("2026-12").fin == date(2027, 1, 1)


def test_el_mes_anterior_se_cuenta_en_hora_de_colombia():
    # 1 de diciembre 03:00 UTC = 30 de noviembre 10 p. m. en Colombia: el mes anterior es octubre.
    assert Periodo.anterior_a(datetime(2026, 12, 1, 3, 0, tzinfo=UTC)).texto == "2026-10"
    assert Periodo.anterior_a(datetime(2026, 12, 1, 6, 0, tzinfo=UTC)).texto == "2026-11"


def test_indice_es_el_mes_sobre_el_promedio_de_los_tres_anteriores():
    mes = [Conteo("Bosque húmedo", 12, 5)]
    previos = [Conteo("Bosque húmedo", 24)]  # promedio 8 al mes

    [indice] = calcular(mes, previos)

    assert indice.promedio_previo == Decimal("8.00")
    assert indice.indice == Decimal("1.50")
    assert indice.nivel == "ALTA"
    assert indice.especies_distintas == 5


def test_sin_historia_el_indice_queda_vacio():
    [indice] = calcular([Conteo("Páramo", 4, 2)], [])

    assert indice.indice is None
    assert indice.nivel == "SIN_HISTORIA"


def test_un_ecosistema_sin_hallazgos_este_mes_aparece_con_indice_cero():
    [indice] = calcular([], [Conteo("Manglar", 6)])

    assert (indice.hallazgos, indice.indice, indice.nivel) == (0, Decimal("0.00"), "BAJA")


def test_orden_del_mas_alto_al_mas_bajo_y_los_vacios_al_final():
    mes = [Conteo("A", 3, 1), Conteo("B", 9, 1), Conteo("C", 1, 1)]
    previos = [Conteo("A", 9), Conteo("B", 9)]

    assert [i.ecosistema for i in calcular(mes, previos)] == ["B", "A", "C"]


@pytest.mark.parametrize(
    ("indice", "nivel"),
    [(None, "SIN_HISTORIA"), (Decimal("0.74"), "BAJA"), (Decimal("0.75"), "NORMAL"),
     (Decimal("1.25"), "NORMAL"), (Decimal("1.26"), "ALTA")],
)
def test_niveles(indice, nivel):
    assert nivel_de(indice) == nivel


def test_generar_cuenta_el_mes_y_los_tres_anteriores(repositorio):
    ServicioIndices(repositorio).generar(Periodo.desde_texto("2026-10"), "MANUAL", None, AHORA)

    assert repositorio.llamadas_contar == [
        (date(2026, 10, 1), date(2026, 11, 1)),
        (date(2026, 7, 1), date(2026, 10, 1)),
    ]


def test_no_genera_un_mes_que_no_ha_empezado(repositorio):
    with pytest.raises(PeriodoInvalido):
        ServicioIndices(repositorio).generar(Periodo.desde_texto("2026-12"), "MANUAL", None, AHORA)
    assert repositorio.guardados == {}


def test_el_mes_en_curso_si_se_puede_generar(repositorio):
    reporte = ServicioIndices(repositorio).generar(Periodo.desde_texto("2026-11"), "MANUAL", None, AHORA)

    assert reporte.periodo.texto == "2026-11"


def test_automatico_genera_el_mes_anterior_solo_una_vez(repositorio):
    servicio = ServicioIndices(repositorio)

    primero = servicio.generar_mes_anterior_si_falta(AHORA)
    segundo = servicio.generar_mes_anterior_si_falta(AHORA)

    assert primero.periodo.texto == "2026-10"
    assert primero.origen == "AUTOMATICO"
    assert segundo is None
