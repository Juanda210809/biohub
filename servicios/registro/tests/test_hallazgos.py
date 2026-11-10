from app.dominio.hallazgos import atributos_publicos
from app.dominio.validadores import DefinicionAtributo, TipoAtributo

FICHA = [
    DefinicionAtributo("temperaturaAgua", TipoAtributo.NUMERO, publicable=True),
    DefinicionAtributo("habitat", TipoAtributo.SELECCION, publicable=True),
    DefinicionAtributo("observaciones", TipoAtributo.TEXTO, publicable=False),
]


def test_solo_deja_los_atributos_publicables():
    atributos = {"temperaturaAgua": 18.5, "habitat": "rio", "observaciones": "cerca de la vereda"}
    assert atributos_publicos(FICHA, atributos) == {"temperaturaAgua": 18.5, "habitat": "rio"}


def test_ignora_los_publicables_que_no_vinieron():
    assert atributos_publicos(FICHA, {"temperaturaAgua": 18.5}) == {"temperaturaAgua": 18.5}


def test_sin_atributos_devuelve_vacio():
    assert atributos_publicos(FICHA, {}) == {}
