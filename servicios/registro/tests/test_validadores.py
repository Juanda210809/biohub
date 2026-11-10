from app.dominio.validadores import (
    DefinicionAtributo,
    RegistroValidadores,
    TipoAtributo,
    ValidadorAtributo,
    ValidadorFecha,
    ValidadorNumero,
    ValidadorSeleccion,
    ValidadorTexto,
    validar_atributos,
)

FICHA_ANFIBIO = [
    DefinicionAtributo(
        "temperaturaAgua", TipoAtributo.NUMERO, obligatorio=True, reglas={"minimo": 0, "maximo": 40}
    ),
    DefinicionAtributo("habitat", TipoAtributo.SELECCION, reglas={"opciones": ["rio", "lago", "bosque"]}),
]


# --- Número -------------------------------------------------------------------------------------
def test_numero_valido():
    assert ValidadorNumero().validar(18.5, {"minimo": 0, "maximo": 40}) == []


def test_numero_sobre_el_maximo():
    assert ValidadorNumero().validar(50, {"maximo": 40}) == ["debe ser menor o igual a 40"]


def test_numero_bajo_el_minimo():
    assert ValidadorNumero().validar(-1, {"minimo": 0}) == ["debe ser mayor o igual a 0"]


def test_numero_rechaza_texto_y_booleano():
    assert ValidadorNumero().validar("abc", {}) == ["debe ser un número"]
    assert ValidadorNumero().validar(True, {}) == ["debe ser un número"]


# --- Texto --------------------------------------------------------------------------------------
def test_texto_valido():
    assert ValidadorTexto().validar("canto grave", {"longitudMaxima": 20}) == []


def test_texto_muy_largo():
    assert ValidadorTexto().validar("abcdef", {"longitudMaxima": 3}) == ["no puede tener más de 3 caracteres"]


def test_texto_no_cumple_el_patron():
    assert ValidadorTexto().validar("x1", {"patron": "[A-Z]+"}) == ["no cumple el formato esperado"]


def test_texto_rechaza_numero():
    assert ValidadorTexto().validar(5, {}) == ["debe ser un texto"]


# --- Fecha --------------------------------------------------------------------------------------
def test_fecha_valida():
    assert ValidadorFecha().validar("2026-01-10", {}) == []


def test_fecha_con_formato_incorrecto():
    assert ValidadorFecha().validar("10/01/2026", {}) == ["debe ser una fecha con formato AAAA-MM-DD"]


def test_fecha_fuera_de_rango():
    reglas = {"fechaMinima": "2026-01-01", "fechaMaxima": "2026-12-31"}
    assert ValidadorFecha().validar("2025-12-31", reglas) == ["no puede ser anterior a 2026-01-01"]
    assert ValidadorFecha().validar("2027-01-01", reglas) == ["no puede ser posterior a 2026-12-31"]


# --- Selección ----------------------------------------------------------------------------------
def test_seleccion_valida():
    assert ValidadorSeleccion().validar("rio", {"opciones": ["rio", "lago"]}) == []


def test_seleccion_fuera_de_las_opciones():
    errores = ValidadorSeleccion().validar("mar", {"opciones": ["rio", "lago"]})
    assert errores == ["debe ser una de: rio, lago"]


# --- validar_atributos (el contexto) --------------------------------------------------------------
def test_ficha_valida_no_devuelve_errores():
    assert validar_atributos(FICHA_ANFIBIO, {"temperaturaAgua": 18.5, "habitat": "rio"}) == []


def test_falta_un_atributo_obligatorio():
    errores = validar_atributos(FICHA_ANFIBIO, {"habitat": "rio"})
    assert errores == [{"campo": "temperaturaAgua", "mensaje": "es obligatorio"}]


def test_atributo_opcional_ausente_es_valido():
    assert validar_atributos(FICHA_ANFIBIO, {"temperaturaAgua": 18.5}) == []


def test_junta_los_errores_de_varios_atributos():
    errores = validar_atributos(FICHA_ANFIBIO, {"temperaturaAgua": 99, "habitat": "mar"})
    assert [e["campo"] for e in errores] == ["temperaturaAgua", "habitat"]


def test_rechaza_un_atributo_que_no_existe_en_la_ficha():
    errores = validar_atributos(FICHA_ANFIBIO, {"temperaturaAgua": 18.5, "colorPlumaje": "rojo"})
    assert errores == [{"campo": "colorPlumaje", "mensaje": "no existe en la ficha de esta especie"}]


def test_se_puede_cambiar_la_estrategia_sin_tocar_el_contexto():
    class SiempreFalla(ValidadorAtributo):
        def validar(self, valor, reglas):
            return ["falla de prueba"]

    registro = RegistroValidadores()
    registro.registrar(TipoAtributo.NUMERO, SiempreFalla())
    errores = validar_atributos(FICHA_ANFIBIO, {"temperaturaAgua": 18.5}, registro)
    assert errores == [{"campo": "temperaturaAgua", "mensaje": "falla de prueba"}]
