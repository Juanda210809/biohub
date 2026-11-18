"""Caso de uso de HU-08: reclasificar un hallazgo como otra especie.

Reglas:
- Se registra quién autoriza el cambio (sale del token, no del cuerpo) y por qué.
- Sin justificación no se guarda nada.
- La clasificación anterior nunca se borra: cada cambio es una versión nueva del historial.
- Del análisis externo solo se guarda el resultado (la especie), el autor y la justificación.

No sabe nada de HTTP ni de SQL: recibe el repositorio por el constructor.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

LONGITUD_MAXIMA_JUSTIFICACION = 2000


class HallazgoNoExiste(Exception):
    """No hay un hallazgo con ese id."""


class EspecieNoExiste(Exception):
    """La especie nueva no está en el catálogo."""


class MismaEspecie(Exception):
    """El hallazgo ya está clasificado como esa especie: no hay nada que reclasificar."""


class JustificacionInvalida(Exception):
    """La justificación está vacía o es demasiado larga."""


@dataclass(frozen=True)
class Especie:
    id: UUID
    nombre_cientifico: str


@dataclass(frozen=True)
class HallazgoActual:
    """Lo que Gobernanza necesita saber del hallazgo antes de reclasificarlo."""

    id: UUID
    especie_id: UUID
    especie_nombre: str
    version_actual: int


@dataclass(frozen=True)
class Reclasificacion:
    """El resultado: la versión nueva que quedó en el historial."""

    hallazgo_id: UUID
    version: int
    especie_anterior: str
    especie_nueva: str
    autor_id: UUID
    justificacion: str
    vigente_desde: datetime


class RepositorioReclasificacion(Protocol):
    """Lo que el caso de uso necesita de la base (lo implementa RepositorioGobernanza)."""

    def obtener_hallazgo(self, hallazgo_id: UUID) -> HallazgoActual | None: ...

    def obtener_especie(self, especie_id: UUID) -> Especie | None: ...

    def reclasificar(
        self, hallazgo: HallazgoActual, especie: Especie, justificacion: str, autor_id: UUID
    ) -> Reclasificacion: ...

    def descartar(self) -> None:
        """Deshace lo pendiente y libera el bloqueo del hallazgo."""


def limpiar_justificacion(justificacion: str | None) -> str:
    texto = (justificacion or "").strip()
    if not texto:
        raise JustificacionInvalida("La justificación es obligatoria")
    if len(texto) > LONGITUD_MAXIMA_JUSTIFICACION:
        raise JustificacionInvalida(
            f"La justificación no puede pasar de {LONGITUD_MAXIMA_JUSTIFICACION} caracteres"
        )
    return texto


class ServicioReclasificacion:
    def __init__(self, repositorio: RepositorioReclasificacion) -> None:
        self._repositorio = repositorio

    def reclasificar(
        self, hallazgo_id: UUID, especie_id: UUID, justificacion: str, autor_id: UUID
    ) -> Reclasificacion:
        texto = limpiar_justificacion(justificacion)
        hallazgo = self._repositorio.obtener_hallazgo(hallazgo_id)  # queda bloqueado hasta el final
        try:
            if hallazgo is None:
                raise HallazgoNoExiste
            if hallazgo.especie_id == especie_id:
                raise MismaEspecie
            especie = self._repositorio.obtener_especie(especie_id)
            if especie is None:
                raise EspecieNoExiste
        except Exception:
            self._repositorio.descartar()  # si se rechaza, el hallazgo se libera de inmediato
            raise
        return self._repositorio.reclasificar(hallazgo, especie, texto, autor_id)
