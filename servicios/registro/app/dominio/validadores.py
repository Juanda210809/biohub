"""Validación de los atributos de una ficha taxonómica (patrón Strategy · RNF-01).

Cada tipo de atributo tiene su propio validador. Agregar un atributo nuevo de un tipo que ya
existe es solo un dato (una DefinicionAtributo): no cambia este código.

Este módulo no sabe nada de HTTP ni de la base de datos.
"""
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from typing import Any


class TipoAtributo(StrEnum):
    NUMERO = "NUMERO"
    TEXTO = "TEXTO"
    FECHA = "FECHA"
    SELECCION = "SELECCION"


@dataclass(frozen=True)
class DefinicionAtributo:
    """Un atributo de la ficha: su clave, su tipo y sus reglas (por ejemplo minimo y maximo)."""

    clave: str
    tipo: TipoAtributo
    obligatorio: bool = False
    reglas: dict[str, Any] = field(default_factory=dict)
    publicable: bool = False
    etiqueta: str = ""


class ValidadorAtributo(ABC):
    """La estrategia: valida un valor según las reglas y devuelve la lista de errores."""

    @abstractmethod
    def validar(self, valor: Any, reglas: dict[str, Any]) -> list[str]:
        """Lista vacía si el valor es válido; si no, un mensaje por cada problema."""


class ValidadorNumero(ValidadorAtributo):
    """Reglas: minimo y maximo."""

    def validar(self, valor: Any, reglas: dict[str, Any]) -> list[str]:
        # bool es subclase de int en Python, por eso se rechaza aparte
        if isinstance(valor, bool) or not isinstance(valor, int | float):
            return ["debe ser un número"]
        errores = []
        minimo = reglas.get("minimo")
        maximo = reglas.get("maximo")
        if minimo is not None and valor < minimo:
            errores.append(f"debe ser mayor o igual a {minimo}")
        if maximo is not None and valor > maximo:
            errores.append(f"debe ser menor o igual a {maximo}")
        return errores


class ValidadorTexto(ValidadorAtributo):
    """Reglas: longitudMaxima y patron (expresión regular que debe cubrir todo el texto)."""

    def validar(self, valor: Any, reglas: dict[str, Any]) -> list[str]:
        if not isinstance(valor, str):
            return ["debe ser un texto"]
        errores = []
        maxima = reglas.get("longitudMaxima")
        if maxima is not None and len(valor) > maxima:
            errores.append(f"no puede tener más de {maxima} caracteres")
        patron = reglas.get("patron")
        if patron is not None and re.fullmatch(patron, valor) is None:
            errores.append("no cumple el formato esperado")
        return errores


def _a_fecha(valor: Any) -> date | None:
    """Convierte 'AAAA-MM-DD' en fecha; devuelve None si no tiene ese formato."""
    if not isinstance(valor, str) or len(valor) != 10:
        return None
    try:
        return date.fromisoformat(valor)
    except ValueError:
        return None


class ValidadorFecha(ValidadorAtributo):
    """Reglas: fechaMinima y fechaMaxima (formato AAAA-MM-DD)."""

    def validar(self, valor: Any, reglas: dict[str, Any]) -> list[str]:
        fecha = _a_fecha(valor)
        if fecha is None:
            return ["debe ser una fecha con formato AAAA-MM-DD"]
        errores = []
        minima = _a_fecha(reglas.get("fechaMinima"))
        maxima = _a_fecha(reglas.get("fechaMaxima"))
        if minima is not None and fecha < minima:
            errores.append(f"no puede ser anterior a {minima.isoformat()}")
        if maxima is not None and fecha > maxima:
            errores.append(f"no puede ser posterior a {maxima.isoformat()}")
        return errores


class ValidadorSeleccion(ValidadorAtributo):
    """Reglas: opciones (lista de valores permitidos)."""

    def validar(self, valor: Any, reglas: dict[str, Any]) -> list[str]:
        opciones = reglas.get("opciones", [])
        if valor not in opciones:
            return ["debe ser una de: " + ", ".join(str(opcion) for opcion in opciones)]
        return []


class RegistroValidadores:
    """Guarda un validador por TipoAtributo, para no elegirlos nunca con if/else."""

    def __init__(self) -> None:
        self._validadores: dict[TipoAtributo, ValidadorAtributo] = {
            TipoAtributo.NUMERO: ValidadorNumero(),
            TipoAtributo.TEXTO: ValidadorTexto(),
            TipoAtributo.FECHA: ValidadorFecha(),
            TipoAtributo.SELECCION: ValidadorSeleccion(),
        }

    def obtener(self, tipo: TipoAtributo) -> ValidadorAtributo:
        return self._validadores[tipo]

    def registrar(self, tipo: TipoAtributo, validador: ValidadorAtributo) -> None:
        self._validadores[tipo] = validador


def validar_atributos(
    definiciones: list[DefinicionAtributo],
    atributos: dict[str, Any],
    registro: RegistroValidadores | None = None,
) -> list[dict[str, str]]:
    """Valida los atributos de un hallazgo contra la ficha vigente de su especie.

    Devuelve una lista de errores {"campo", "mensaje"}; vacía si todo es válido.
    """
    registro = registro or RegistroValidadores()
    errores: list[dict[str, str]] = []

    for definicion in definiciones:
        valor = atributos.get(definicion.clave)
        if valor is None:
            if definicion.obligatorio:
                errores.append({"campo": definicion.clave, "mensaje": "es obligatorio"})
            continue
        validador = registro.obtener(definicion.tipo)
        for mensaje in validador.validar(valor, definicion.reglas):
            errores.append({"campo": definicion.clave, "mensaje": mensaje})

    claves_conocidas = {definicion.clave for definicion in definiciones}
    for clave in atributos:
        if clave not in claves_conocidas:
            errores.append({"campo": clave, "mensaje": "no existe en la ficha de esta especie"})

    return errores
