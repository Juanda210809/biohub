from uuid import UUID

import pytest

from app.dominio.hallazgos import FichaVigente
from app.dominio.servicio_fichas import (
    DefinicionInvalida,
    FichaNoExiste,
    RevisionDesactualizada,
    ServicioFichas,
)
from app.dominio.validadores import DefinicionAtributo, TipoAtributo

TIPO_ID = UUID("10000000-0000-0000-0000-000000000001")
AUTOR_ID = UUID("00000000-0000-0000-0000-0000000000bb")

TEMPERATURA = DefinicionAtributo(
    "temperaturaAgua",
    TipoAtributo.NUMERO,
    obligatorio=True,
    reglas={"minimo": 0, "maximo": 40},
    publicable=True,
    etiqueta="Temperatura del agua (°C)",
)
SALINIDAD = DefinicionAtributo(
    "salinidad", TipoAtributo.NUMERO, reglas={"minimo": 0}, etiqueta="Salinidad"
)


class RepositorioFichasFalso:
    """Reemplaza a RepositorioFichas: guarda en memoria lo que recibe."""

    def __init__(self, ficha: FichaVigente | None) -> None:
        self.ficha = ficha
        self.publicado = None
        self.cancelado = False

    def obtener_ficha_para_publicar(self, tipo_especie_id):
        return self.ficha

    def publicar_revision(self, ficha, nuevas, autor_id):
        self.publicado = (ficha, nuevas, autor_id)
        return FichaVigente(ficha.tipo_especie_id, ficha.nombre, ficha.revision + 1, nuevas)

    def cancelar(self):
        self.cancelado = True


def _ficha(revision=1):
    return FichaVigente(TIPO_ID, "Anfibio", revision, [TEMPERATURA])


def test_publica_la_revision_nueva_con_el_autor():
    repositorio = RepositorioFichasFalso(_ficha(revision=1))
    nueva = ServicioFichas(repositorio).publicar(TIPO_ID, 1, [TEMPERATURA, SALINIDAD], AUTOR_ID)
    assert nueva.revision == 2
    assert [a.clave for a in nueva.atributos] == ["temperaturaAgua", "salinidad"]
    ficha, nuevas, autor = repositorio.publicado
    assert ficha.revision == 1
    assert nuevas == [TEMPERATURA, SALINIDAD]
    assert autor == AUTOR_ID
    assert repositorio.cancelado is False


def test_tipo_de_especie_inexistente():
    repositorio = RepositorioFichasFalso(None)
    with pytest.raises(FichaNoExiste):
        ServicioFichas(repositorio).publicar(TIPO_ID, 1, [TEMPERATURA], AUTOR_ID)
    assert repositorio.publicado is None
    assert repositorio.cancelado is True


def test_revision_desactualizada_lleva_la_vigente():
    repositorio = RepositorioFichasFalso(_ficha(revision=3))
    with pytest.raises(RevisionDesactualizada) as error:
        ServicioFichas(repositorio).publicar(TIPO_ID, 2, [TEMPERATURA], AUTOR_ID)
    assert error.value.revision_actual == 3
    assert repositorio.publicado is None
    assert repositorio.cancelado is True


def test_definicion_invalida_no_publica_nada():
    repositorio = RepositorioFichasFalso(_ficha())
    mala = DefinicionAtributo("Mala Clave", TipoAtributo.NUMERO, etiqueta="Mala")
    with pytest.raises(DefinicionInvalida) as error:
        ServicioFichas(repositorio).publicar(TIPO_ID, 1, [mala], AUTOR_ID)
    assert error.value.errores[0]["campo"] == "atributos[0].clave"
    assert repositorio.publicado is None
    assert repositorio.cancelado is True


def test_se_valida_contra_la_ficha_vigente_no_se_puede_cambiar_un_tipo():
    repositorio = RepositorioFichasFalso(_ficha())
    cambiado = DefinicionAtributo("temperaturaAgua", TipoAtributo.TEXTO, etiqueta="Temperatura")
    with pytest.raises(DefinicionInvalida) as error:
        ServicioFichas(repositorio).publicar(TIPO_ID, 1, [cambiado], AUTOR_ID)
    assert error.value.errores[0]["campo"] == "atributos[0].tipo"


def test_el_conflicto_de_revision_se_revisa_antes_que_las_definiciones():
    repositorio = RepositorioFichasFalso(_ficha(revision=2))
    mala = DefinicionAtributo("Mala Clave", TipoAtributo.NUMERO, etiqueta="Mala")
    with pytest.raises(RevisionDesactualizada):
        ServicioFichas(repositorio).publicar(TIPO_ID, 1, [mala], AUTOR_ID)
