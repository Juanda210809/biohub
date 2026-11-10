"""Caso de uso: registrar un hallazgo (HU-03).

No sabe nada de HTTP ni de SQL: recibe el repositorio por el constructor (DIP, Sesión 18).
"""
from typing import Protocol
from uuid import UUID

from app.dominio.hallazgos import Especie, NuevoHallazgo, atributos_publicos
from app.dominio.validadores import DefinicionAtributo, validar_atributos


class EspecieNoExiste(Exception):
    """La especie indicada no está en el catálogo."""


class ExpedicionNoExiste(Exception):
    """La expedición indicada no existe."""


class FichaInvalida(Exception):
    """Los atributos no cumplen la ficha de la especie. Lleva la lista de errores por campo."""

    def __init__(self, errores: list[dict[str, str]]) -> None:
        super().__init__("Los atributos no cumplen la ficha")
        self.errores = errores


class RepositorioDeHallazgos(Protocol):
    """Lo que el servicio necesita de la base de datos (lo implementa RepositorioHallazgos)."""

    def obtener_especie(self, especie_id: UUID) -> Especie | None:
        """Busca una especie por su id."""

    def existe_expedicion(self, expedicion_id: UUID) -> bool:
        """Indica si la expedición existe."""

    def definiciones_vigentes(self, tipo_especie_id: UUID) -> list[DefinicionAtributo]:
        """Atributos de la ficha vigente de un tipo de especie."""

    def registrar(self, datos: NuevoHallazgo, nombre_especie: str, publicos: dict) -> UUID:
        """Guarda el hallazgo completo en una transacción y devuelve su id."""


class ServicioHallazgos:
    def __init__(self, repositorio: RepositorioDeHallazgos) -> None:
        self._repositorio = repositorio

    def registrar(self, datos: NuevoHallazgo) -> UUID:
        especie = self._repositorio.obtener_especie(datos.especie_id)
        if especie is None:
            raise EspecieNoExiste
        if not self._repositorio.existe_expedicion(datos.expedicion_id):
            raise ExpedicionNoExiste

        definiciones = self._repositorio.definiciones_vigentes(especie.tipo_especie_id)
        errores = validar_atributos(definiciones, datos.atributos)
        if errores:
            raise FichaInvalida(errores)

        publicos = atributos_publicos(definiciones, datos.atributos)
        return self._repositorio.registrar(datos, especie.nombre_cientifico, publicos)
