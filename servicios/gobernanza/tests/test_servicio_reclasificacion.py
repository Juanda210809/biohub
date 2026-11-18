import pytest

from app.dominio.reclasificacion import (
    JustificacionInvalida,
    MismaEspecie,
    ServicioReclasificacion,
    limpiar_justificacion,
)
from tests.conftest import CIENTIFICO_ID, ESPECIE_NUEVA_ID, HALLAZGO_ID


def test_justificacion_vacia_no_llega_al_repositorio(repositorio):
    servicio = ServicioReclasificacion(repositorio)

    with pytest.raises(JustificacionInvalida):
        servicio.reclasificar(HALLAZGO_ID, ESPECIE_NUEVA_ID, "  ", CIENTIFICO_ID)
    assert repositorio.guardado is None


def test_justificacion_demasiado_larga():
    with pytest.raises(JustificacionInvalida):
        limpiar_justificacion("x" * 2001)


def test_reclasificar_pasa_al_repositorio_la_especie_y_el_autor(repositorio):
    resultado = ServicioReclasificacion(repositorio).reclasificar(
        HALLAZGO_ID, ESPECIE_NUEVA_ID, "Nueva evidencia", CIENTIFICO_ID
    )

    hallazgo, especie, justificacion, autor = repositorio.guardado
    assert especie.id == ESPECIE_NUEVA_ID
    assert justificacion == "Nueva evidencia"
    assert autor == CIENTIFICO_ID
    assert resultado.version == hallazgo.version_actual + 1


def test_si_se_rechaza_libera_el_hallazgo(repositorio):
    especie_actual = repositorio.hallazgo.especie_id

    with pytest.raises(MismaEspecie):
        ServicioReclasificacion(repositorio).reclasificar(
            HALLAZGO_ID, especie_actual, "Nueva evidencia", CIENTIFICO_ID
        )
    assert repositorio.descartado
