"""Formas de las peticiones y respuestas de la API de Gobernanza (JSON en camelCase)."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

from app.dominio.reclasificacion import (
    LONGITUD_MAXIMA_JUSTIFICACION,
    JustificacionInvalida,
    Reclasificacion,
    limpiar_justificacion,
)


class EsquemaBase(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ReclasificacionEntrada(EsquemaBase):
    especie_id: UUID
    justificacion: str = Field(max_length=LONGITUD_MAXIMA_JUSTIFICACION + 200)

    @field_validator("justificacion")
    @classmethod
    def exigir_justificacion(cls, valor: str) -> str:
        try:
            return limpiar_justificacion(valor)
        except JustificacionInvalida as error:
            raise ValueError(str(error)) from None


class ReclasificacionSalida(EsquemaBase):
    hallazgo_id: UUID
    version: int
    especie_anterior: str
    especie_nueva: str
    autor_id: UUID
    justificacion: str
    vigente_desde: datetime

    @classmethod
    def desde(cls, r: Reclasificacion) -> "ReclasificacionSalida":
        return cls(
            hallazgo_id=r.hallazgo_id,
            version=r.version,
            especie_anterior=r.especie_anterior,
            especie_nueva=r.especie_nueva,
            autor_id=r.autor_id,
            justificacion=r.justificacion,
            vigente_desde=r.vigente_desde,
        )
