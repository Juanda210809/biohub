"""Catálogo para los desplegables del formulario de HU-03: especies y expediciones."""
from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass(frozen=True)
class EspecieCatalogo:
    id: UUID
    nombre_cientifico: str
    nombre_comun: str | None
    tipo_especie_id: UUID
    tipo_especie: str


@dataclass(frozen=True)
class ExpedicionCatalogo:
    id: UUID
    nombre: str
    fecha_inicio: date
    fecha_fin: date | None
