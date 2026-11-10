"""Datos y reglas del negocio de un hallazgo (sin HTTP ni base de datos)."""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.dominio.validadores import DefinicionAtributo


@dataclass(frozen=True)
class Especie:
    id: UUID
    tipo_especie_id: UUID
    nombre_cientifico: str


@dataclass(frozen=True)
class NuevoHallazgo:
    """Lo que hace falta para registrar un hallazgo (HU-03)."""

    especie_id: UUID
    expedicion_id: UUID
    investigador_id: UUID
    fecha_hallazgo: date
    latitud: Decimal
    longitud: Decimal
    precision_m: Decimal | None = None
    region: str | None = None
    departamento: str | None = None
    ecosistema: str | None = None
    atributos: dict[str, Any] = field(default_factory=dict)


def atributos_publicos(
    definiciones: list[DefinicionAtributo], atributos: dict[str, Any]
) -> dict[str, Any]:
    """Deja solo los atributos marcados como publicables: es lo que va a hallazgo_publico."""
    return {
        d.clave: atributos[d.clave] for d in definiciones if d.publicable and d.clave in atributos
    }
