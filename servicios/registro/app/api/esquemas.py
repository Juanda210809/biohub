"""Formas de las peticiones y respuestas de la API de Registro (JSON en camelCase)."""
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel


class EsquemaBase(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class HallazgoEntrada(EsquemaBase):
    especie_id: UUID
    expedicion_id: UUID
    fecha_hallazgo: date
    latitud: Decimal = Field(ge=-90, le=90)
    longitud: Decimal = Field(ge=-180, le=180)
    precision_m: Decimal | None = Field(default=None, ge=0)
    region: str | None = None
    departamento: str | None = None
    ecosistema: str | None = None
    atributos: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def exigir_region_o_departamento(self) -> "HallazgoEntrada":
        if not (self.region or self.departamento):
            raise ValueError("Debe indicar al menos la region o el departamento")
        return self


class HallazgoCreado(EsquemaBase):
    hallazgo_id: UUID
    version: int


class AtributoFicha(EsquemaBase):
    clave: str
    etiqueta: str
    tipo: str
    obligatorio: bool
    reglas: dict[str, Any]


class FichaSalida(EsquemaBase):
    tipo_especie_id: UUID
    nombre: str
    revision: int
    atributos: list[AtributoFicha]
