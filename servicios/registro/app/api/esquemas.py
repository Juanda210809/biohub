"""Formas de las peticiones y respuestas de la API de Registro (JSON en camelCase)."""
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from app.dominio.hallazgos import FichaVigente
from app.dominio.validadores import TipoAtributo


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
    publicable: bool
    reglas: dict[str, Any]


class FichaSalida(EsquemaBase):
    tipo_especie_id: UUID
    nombre: str
    revision: int
    atributos: list[AtributoFicha]

class UbicacionSalida(EsquemaBase):
    hallazgo_id: UUID
    nivel_ubicacion: str
    region: str | None = None
    departamento: str | None = None
    latitud: Decimal | None = None
    longitud: Decimal | None = None
    precision_m: Decimal | None = None


def ficha_a_salida(ficha: FichaVigente) -> FichaSalida:
    """Convierte la ficha del dominio en la respuesta de la API (la usan el GET y el PUT)."""
    return FichaSalida(
        tipo_especie_id=ficha.tipo_especie_id,
        nombre=ficha.nombre,
        revision=ficha.revision,
        atributos=[
            AtributoFicha(
                clave=a.clave,
                etiqueta=a.etiqueta,
                tipo=a.tipo.value,
                obligatorio=a.obligatorio,
                publicable=a.publicable,
                reglas=a.reglas,
            )
            for a in ficha.atributos
        ],
    )


class AtributoEntrada(EsquemaBase):
    clave: str
    etiqueta: str
    tipo: TipoAtributo
    obligatorio: bool = False
    publicable: bool = False
    reglas: dict[str, Any] = Field(default_factory=dict)


class FichaEntrada(EsquemaBase):
    """La ficha completa que quedará vigente, y la revisión que vio quien la edita."""

    revision_base: int = Field(ge=1)
    atributos: list[AtributoEntrada]