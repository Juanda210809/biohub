"""Usuario interno y sus roles (sin HTTP ni base de datos)."""
from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID


class Rol(StrEnum):
    INVESTIGADOR = "INVESTIGADOR"
    CIENTIFICO_AUTORIZADO = "CIENTIFICO_AUTORIZADO"
    ALTO_RANGO = "ALTO_RANGO"
    AUDITOR = "AUDITOR"
    ADMINISTRADOR = "ADMINISTRADOR"


@dataclass(frozen=True)
class Usuario:
    """Cuenta interna. Sin rol (None) no puede usar funciones internas (HU-02)."""

    id: UUID
    nombre: str
    correo: str
    rol: Rol | None
    activo: bool
    hash_contrasena: str = field(default="", repr=False)  # repr=False: nunca sale en un log
