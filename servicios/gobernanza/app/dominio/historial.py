"""Caso de uso de HU-12: reconstruir cómo estaba un hallazgo en una fecha y compararlo con hoy.

- La versión vigente en una fecha es la última que empezó a regir antes de que terminara ese día.
- Los días se cuentan en hora de Colombia (UTC-5, sin horario de verano).
- Muestra autor y justificación de cada versión, y la lista de lo que cambió hasta hoy.

No sabe nada de HTTP ni de SQL: recibe el repositorio por el constructor.
"""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Protocol
from uuid import UUID

HORA_COLOMBIA = timezone(timedelta(hours=-5), "America/Bogota")


class HallazgoSinHistorial(Exception):
    """El hallazgo no existe (no tiene ninguna versión)."""


class SinVersionEnFecha(Exception):
    """En esa fecha el hallazgo todavía no se había registrado."""

    def __init__(self, primera_version: datetime) -> None:
        super().__init__("El hallazgo aún no existía en esa fecha")
        self.primera_version = primera_version


@dataclass(frozen=True)
class Version:
    numero: int
    especie: str
    atributos: dict[str, Any]
    autor_id: UUID
    justificacion: str
    vigente_desde: datetime


@dataclass(frozen=True)
class Cambio:
    campo: str
    antes: Any
    ahora: Any


@dataclass(frozen=True)
class Reconstruccion:
    hallazgo_id: UUID
    fecha: date
    en_fecha: Version
    actual: Version
    cambios: list[Cambio]

    @property
    def versiones_posteriores(self) -> int:
        return self.actual.numero - self.en_fecha.numero


class RepositorioHistorial(Protocol):
    def version_vigente_en(self, hallazgo_id: UUID, instante: datetime) -> Version | None: ...

    def version_actual(self, hallazgo_id: UUID) -> Version | None: ...

    def primera_version(self, hallazgo_id: UUID) -> Version | None: ...


def fin_del_dia(fecha: date) -> datetime:
    """El primer instante del día siguiente, en hora de Colombia."""
    return datetime.combine(fecha + timedelta(days=1), time.min, tzinfo=HORA_COLOMBIA)


def comparar(antes: Version, ahora: Version) -> list[Cambio]:
    """Lo que cambió entre dos versiones: la especie y cada atributo, en orden alfabético."""
    cambios = []
    if antes.especie != ahora.especie:
        cambios.append(Cambio("especie", antes.especie, ahora.especie))
    for clave in sorted(set(antes.atributos) | set(ahora.atributos)):
        valor_antes, valor_ahora = antes.atributos.get(clave), ahora.atributos.get(clave)
        if valor_antes != valor_ahora:
            cambios.append(Cambio(f"atributos.{clave}", valor_antes, valor_ahora))
    return cambios


class ServicioHistorial:
    def __init__(self, repositorio: RepositorioHistorial) -> None:
        self._repositorio = repositorio

    def reconstruir(self, hallazgo_id: UUID, fecha: date) -> Reconstruccion:
        actual = self._repositorio.version_actual(hallazgo_id)
        if actual is None:
            raise HallazgoSinHistorial
        en_fecha = self._repositorio.version_vigente_en(hallazgo_id, fin_del_dia(fecha))
        if en_fecha is None:
            primera = self._repositorio.primera_version(hallazgo_id)
            raise SinVersionEnFecha(primera.vigente_desde if primera else actual.vigente_desde)
        return Reconstruccion(hallazgo_id, fecha, en_fecha, actual, comparar(en_fecha, actual))
