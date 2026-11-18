from app.dominio.fichas import validar_definiciones
from app.dominio.validadores import DefinicionAtributo, TipoAtributo

VIGENTE = [
    DefinicionAtributo(
        "temperaturaAgua",
        TipoAtributo.NUMERO,
        obligatorio=True,
        reglas={"minimo": 0, "maximo": 40, "unidad": "°C"},
        publicable=True,
        etiqueta="Temperatura del agua (°C)",
    ),
    DefinicionAtributo(
        "habitat",
        TipoAtributo.SELECCION,
        reglas={"opciones": ["quebrada", "charca"]},
        etiqueta="Hábitat",
    ),
]


def _atributo(clave="salinidad", tipo=TipoAtributo.NUMERO, reglas=None, etiqueta="Salinidad"):
    return DefinicionAtributo(clave, tipo, reglas=reglas or {}, etiqueta=etiqueta)


def _campos(errores):
    return [error["campo"] for error in errores]


def test_la_ficha_vigente_se_puede_volver_a_publicar():
    assert validar_definiciones(VIGENTE, VIGENTE) == []


def test_agregar_un_atributo_nuevo_es_valido():
    nuevas = [*VIGENTE, _atributo(reglas={"minimo": 0, "maximo": 45})]
    assert validar_definiciones(nuevas, VIGENTE) == []


def test_quitar_un_atributo_es_valido():
    assert validar_definiciones(VIGENTE[:1], VIGENTE) == []


def test_modificar_las_reglas_de_un_atributo_es_valido():
    modificado = DefinicionAtributo(
        "temperaturaAgua", TipoAtributo.NUMERO, reglas={"minimo": -5, "maximo": 45}, etiqueta="Temp."
    )
    assert validar_definiciones([modificado, VIGENTE[1]], VIGENTE) == []


def test_una_ficha_sin_atributos_se_rechaza():
    errores = validar_definiciones([], VIGENTE)
    assert _campos(errores) == ["atributos"]


def test_clave_con_formato_invalido():
    for clave in ("Temperatura", "con espacio", "1numero", "con-guion", ""):
        errores = validar_definiciones([_atributo(clave=clave)], [])
        assert _campos(errores) == ["atributos[0].clave"], clave


def test_clave_repetida():
    errores = validar_definiciones([_atributo(), _atributo()], [])
    assert _campos(errores) == ["atributos[1].clave"]
    assert "repetida" in errores[0]["mensaje"]


def test_etiqueta_vacia_o_demasiado_larga():
    assert _campos(validar_definiciones([_atributo(etiqueta="   ")], [])) == ["atributos[0].etiqueta"]
    assert _campos(validar_definiciones([_atributo(etiqueta="x" * 101)], [])) == [
        "atributos[0].etiqueta"
    ]


def test_no_se_puede_cambiar_el_tipo_de_una_clave_existente():
    cambiado = DefinicionAtributo(
        "temperaturaAgua", TipoAtributo.TEXTO, reglas={}, etiqueta="Temperatura del agua"
    )
    errores = validar_definiciones([cambiado], VIGENTE)
    assert _campos(errores) == ["atributos[0].tipo"]
    assert "NUMERO" in errores[0]["mensaje"]


def test_el_mismo_tipo_con_otra_clave_si_se_permite():
    nueva = DefinicionAtributo(
        "temperaturaAguaTexto", TipoAtributo.TEXTO, reglas={}, etiqueta="Temperatura (texto)"
    )
    assert validar_definiciones([nueva], VIGENTE) == []


def test_regla_desconocida_para_el_tipo():
    errores = validar_definiciones([_atributo(reglas={"maxim": 10})], [])
    assert _campos(errores) == ["atributos[0].reglas"]
    assert "maxim" in errores[0]["mensaje"]


def test_regla_de_otro_tipo():
    errores = validar_definiciones([_atributo(reglas={"opciones": ["a"]})], [])
    assert _campos(errores) == ["atributos[0].reglas"]


# --- Reglas por tipo ----------------------------------------------------------------------------
def _mensajes(tipo, reglas):
    errores = validar_definiciones([_atributo(tipo=tipo, reglas=reglas)], [])
    return [error["mensaje"] for error in errores]


def test_numero_minimo_mayor_que_maximo():
    assert _mensajes(TipoAtributo.NUMERO, {"minimo": 10, "maximo": 5}) == [
        "minimo no puede ser mayor que maximo"
    ]


def test_numero_con_reglas_que_no_son_numeros():
    assert len(_mensajes(TipoAtributo.NUMERO, {"minimo": "0", "maximo": True})) == 2


def test_numero_sin_reglas_es_valido():
    assert _mensajes(TipoAtributo.NUMERO, {}) == []


def test_texto_con_longitud_maxima_invalida():
    for valor in (0, -3, "10", 2.5, True):
        assert len(_mensajes(TipoAtributo.TEXTO, {"longitudMaxima": valor})) == 1, valor


def test_texto_con_patron_invalido():
    assert _mensajes(TipoAtributo.TEXTO, {"patron": "[abc"}) == [
        "patron no es una expresión regular válida"
    ]


def test_texto_con_reglas_validas():
    assert _mensajes(TipoAtributo.TEXTO, {"longitudMaxima": 500, "patron": "[A-Z]+"}) == []


def test_fecha_con_formato_invalido():
    assert len(_mensajes(TipoAtributo.FECHA, {"fechaMinima": "01/02/2026"})) == 1


def test_fecha_minima_posterior_a_la_maxima():
    reglas = {"fechaMinima": "2026-12-01", "fechaMaxima": "2026-01-01"}
    assert _mensajes(TipoAtributo.FECHA, reglas) == ["fechaMinima no puede ser posterior a fechaMaxima"]


def test_fecha_con_reglas_validas():
    assert _mensajes(TipoAtributo.FECHA, {"fechaMinima": "2020-01-01", "fechaMaxima": "2030-12-31"}) == []


def test_seleccion_sin_opciones():
    assert len(_mensajes(TipoAtributo.SELECCION, {})) == 1
    assert len(_mensajes(TipoAtributo.SELECCION, {"opciones": []})) == 1


def test_seleccion_con_opciones_vacias_o_repetidas():
    assert _mensajes(TipoAtributo.SELECCION, {"opciones": ["a", " "]}) == [
        "cada opción debe ser un texto no vacío"
    ]
    assert _mensajes(TipoAtributo.SELECCION, {"opciones": ["a", "a"]}) == [
        "las opciones no pueden repetirse"
    ]


def test_seleccion_con_opciones_validas():
    assert _mensajes(TipoAtributo.SELECCION, {"opciones": ["a", "b"]}) == []
