"""Caso de uso: publicar una revisión nueva de la ficha de un tipo de especie (HU-04).

No sabe nada de HTTP ni de SQL: recibe el repositorio por el constructor, igual que
ServicioHallazgos.
"""
from typing import Protocol
from uuid import UUID

from app.dominio.fichas import validar_definiciones
from app.dominio.hallazgos import FichaVigente
from app.dominio.validadores import DefinicionAtributo


class FichaNoExiste(Exception):
    """El tipo de especie no existe o no tiene una ficha publicada."""


class RevisionDesactualizada(Exception):
    """Otra persona publicó una revisión nueva mientras se editaba. Lleva la revisión vigente."""

    def __init__(self, revision_actual: int) -> None:
        super().__init__("La ficha cambió mientras se editaba")
        self.revision_actual = revision_actual


class DefinicionInvalida(Exception):
    """Los atributos de la ficha no son válidos. Lleva la lista de errores por campo."""

    def __init__(self, errores: list[dict[str, str]]) -> None:
        super().__init__("Los atributos de la ficha no son válidos")
        self.errores = errores


class RepositorioDeFichas(Protocol):
    """Lo que el servicio necesita de la base de datos (lo implementa RepositorioFichas)."""

    def obtener_ficha_para_publicar(self, tipo_especie_id: UUID) -> FichaVigente | None:
        """Bloquea el tipo de especie y devuelve su ficha vigente (None si no existe).

        El bloqueo dura hasta publicar_revision o cancelar.
        """

    def publicar_revision(
        self, ficha: FichaVigente, nuevas: list[DefinicionAtributo], autor_id: UUID
    ) -> FichaVigente:
        """Reemplaza la vigente por la nueva en una transacción y devuelve la ficha nueva."""

    def cancelar(self) -> None:
        """Deshace la transacción y libera el bloqueo."""


class ServicioFichas:
    def __init__(self, repositorio: RepositorioDeFichas) -> None:
        self._repositorio = repositorio

    def publicar(
        self,
        tipo_especie_id: UUID,
        revision_base: int,
        nuevas: list[DefinicionAtributo],
        autor_id: UUID,
    ) -> FichaVigente:
        ficha = self._repositorio.obtener_ficha_para_publicar(tipo_especie_id)
        try:
            if ficha is None:
                raise FichaNoExiste
            # Primero el conflicto: si la ficha cambió, lo que editó la persona ya no aplica.
            if ficha.revision != revision_base:
                raise RevisionDesactualizada(ficha.revision)
            errores = validar_definiciones(nuevas, ficha.atributos)
            if errores:
                raise DefinicionInvalida(errores)
            return self._repositorio.publicar_revision(ficha, nuevas, autor_id)
        except Exception:
            self._repositorio.cancelar()
            raise
