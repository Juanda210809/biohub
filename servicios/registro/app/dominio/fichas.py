"""Validación de la definición de una ficha antes de publicar una revisión nueva (HU-04).

Aquí se revisa que los atributos que define el personal científico sean coherentes: clave
válida y única, etiqueta, reglas que corresponden al tipo y que no se cambie el tipo de un
atributo que ya existe. Los validadores de VALORES (patrón Strategy) siguen en validadores.py.

Este módulo no sabe nada de HTTP ni de la base de datos.
"""
import re
from collections.abc import Callable
from datetime import date
from typing import Any

from app.dominio.validadores import DefinicionAtributo, TipoAtributo

CLAVE_VALIDA = re.compile(r"[a-z][a-zA-Z0-9]{0,59}")
ETIQUETA_MAXIMA = 100

# Reglas que acepta cada tipo (las mismas que leen los validadores de validadores.py).
REGLAS_PERMITIDAS: dict[TipoAtributo, frozenset[str]] = {
    TipoAtributo.NUMERO: frozenset({"minimo", "maximo", "unidad"}),
    TipoAtributo.TEXTO: frozenset({"longitudMaxima", "patron"}),
    TipoAtributo.FECHA: frozenset({"fechaMinima", "fechaMaxima"}),
    TipoAtributo.SELECCION: frozenset({"opciones"}),
}


def _es_numero(valor: Any) -> bool:
    # bool es subclase de int en Python, por eso se rechaza aparte
    return isinstance(valor, int | float) and not isinstance(valor, bool)


def _reglas_numero(reglas: dict[str, Any]) -> list[str]:
    errores = []
    for nombre in ("minimo", "maximo"):
        if nombre in reglas and not _es_numero(reglas[nombre]):
            errores.append(f"{nombre} debe ser un número")
    if "unidad" in reglas and not isinstance(reglas["unidad"], str):
        errores.append("unidad debe ser un texto")
    minimo, maximo = reglas.get("minimo"), reglas.get("maximo")
    if _es_numero(minimo) and _es_numero(maximo) and minimo > maximo:
        errores.append("minimo no puede ser mayor que maximo")
    return errores


def _reglas_texto(reglas: dict[str, Any]) -> list[str]:
    errores = []
    if "longitudMaxima" in reglas:
        maxima = reglas["longitudMaxima"]
        if isinstance(maxima, bool) or not isinstance(maxima, int) or maxima < 1:
            errores.append("longitudMaxima debe ser un entero mayor o igual a 1")
    if "patron" in reglas:
        patron = reglas["patron"]
        if not isinstance(patron, str):
            errores.append("patron debe ser un texto")
        else:
            try:
                re.compile(patron)
            except re.error:
                errores.append("patron no es una expresión regular válida")
    return errores


def _fecha(valor: Any) -> date | None:
    """Convierte 'AAAA-MM-DD' en fecha; devuelve None si no tiene ese formato."""
    if not isinstance(valor, str) or len(valor) != 10:
        return None
    try:
        return date.fromisoformat(valor)
    except ValueError:
        return None


def _reglas_fecha(reglas: dict[str, Any]) -> list[str]:
    errores = []
    fechas: dict[str, date] = {}
    for nombre in ("fechaMinima", "fechaMaxima"):
        if nombre in reglas:
            fecha = _fecha(reglas[nombre])
            if fecha is None:
                errores.append(f"{nombre} debe tener formato AAAA-MM-DD")
            else:
                fechas[nombre] = fecha
    if len(fechas) == 2 and fechas["fechaMinima"] > fechas["fechaMaxima"]:
        errores.append("fechaMinima no puede ser posterior a fechaMaxima")
    return errores


def _reglas_seleccion(reglas: dict[str, Any]) -> list[str]:
    opciones = reglas.get("opciones")
    if not isinstance(opciones, list) or not opciones:
        return ["opciones debe ser una lista con al menos una opción"]
    if not all(isinstance(opcion, str) and opcion.strip() for opcion in opciones):
        return ["cada opción debe ser un texto no vacío"]
    if len(set(opciones)) != len(opciones):
        return ["las opciones no pueden repetirse"]
    return []


# Un verificador de reglas por tipo, igual que los validadores de valores: sin if/else por tipo.
VERIFICADORES_DE_REGLAS: dict[TipoAtributo, Callable[[dict[str, Any]], list[str]]] = {
    TipoAtributo.NUMERO: _reglas_numero,
    TipoAtributo.TEXTO: _reglas_texto,
    TipoAtributo.FECHA: _reglas_fecha,
    TipoAtributo.SELECCION: _reglas_seleccion,
}


def validar_definiciones(
    nuevas: list[DefinicionAtributo], vigentes: list[DefinicionAtributo]
) -> list[dict[str, str]]:
    """Valida la ficha que se quiere publicar contra la que está vigente.

    Devuelve una lista de errores {"campo", "mensaje"}; vacía si todo es válido.
    """
    if not nuevas:
        return [{"campo": "atributos", "mensaje": "debe incluir al menos un atributo"}]

    tipo_vigente = {definicion.clave: definicion.tipo for definicion in vigentes}
    errores: list[dict[str, str]] = []
    claves_vistas: set[str] = set()

    for posicion, definicion in enumerate(nuevas):
        base = f"atributos[{posicion}]"

        if not CLAVE_VALIDA.fullmatch(definicion.clave):
            errores.append(
                {
                    "campo": f"{base}.clave",
                    "mensaje": "debe empezar con minúscula y usar solo letras y números "
                    "(camelCase, máximo 60 caracteres)",
                }
            )
        elif definicion.clave in claves_vistas:
            errores.append({"campo": f"{base}.clave", "mensaje": "está repetida en la ficha"})
        claves_vistas.add(definicion.clave)

        etiqueta = definicion.etiqueta.strip()
        if not etiqueta or len(etiqueta) > ETIQUETA_MAXIMA:
            errores.append(
                {
                    "campo": f"{base}.etiqueta",
                    "mensaje": f"es obligatoria y puede tener hasta {ETIQUETA_MAXIMA} caracteres",
                }
            )

        anterior = tipo_vigente.get(definicion.clave)
        if anterior is not None and anterior != definicion.tipo:
            errores.append(
                {
                    "campo": f"{base}.tipo",
                    "mensaje": f"no se puede cambiar el tipo de un atributo existente (es {anterior.value}); "
                    "use otra clave",
                }
            )

        desconocidas = sorted(set(definicion.reglas) - REGLAS_PERMITIDAS[definicion.tipo])
        for nombre in desconocidas:
            errores.append(
                {
                    "campo": f"{base}.reglas",
                    "mensaje": f"la regla {nombre} no existe para el tipo {definicion.tipo.value}",
                }
            )
        for mensaje in VERIFICADORES_DE_REGLAS[definicion.tipo](definicion.reglas):
            errores.append({"campo": f"{base}.reglas", "mensaje": mensaje})

    return errores
