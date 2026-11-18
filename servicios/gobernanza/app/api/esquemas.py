"""Formas de las peticiones y respuestas de la API de Gobernanza (JSON en camelCase)."""
from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

from app.dominio.historial import Reconstruccion, Version
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


class VersionSalida(EsquemaBase):
    numero: int
    especie: str
    atributos: dict[str, Any]
    autor_id: UUID
    justificacion: str
    vigente_desde: datetime

    @classmethod
    def desde(cls, v: Version) -> "VersionSalida":
        return cls(
            numero=v.numero,
            especie=v.especie,
            atributos=v.atributos,
            autor_id=v.autor_id,
            justificacion=v.justificacion,
            vigente_desde=v.vigente_desde,
        )


class CambioSalida(EsquemaBase):
    campo: str
    antes: Any
    ahora: Any


class ReconstruccionSalida(EsquemaBase):
    hallazgo_id: UUID
    fecha: date
    en_fecha: VersionSalida
    actual: VersionSalida
    versiones_posteriores: int
    cambios: list[CambioSalida]

    @classmethod
    def desde(cls, r: Reconstruccion) -> "ReconstruccionSalida":
        return cls(
            hallazgo_id=r.hallazgo_id,
            fecha=r.fecha,
            en_fecha=VersionSalida.desde(r.en_fecha),
            actual=VersionSalida.desde(r.actual),
            versiones_posteriores=r.versiones_posteriores,
            cambios=[CambioSalida(campo=c.campo, antes=c.antes, ahora=c.ahora) for c in r.cambios],
        )
