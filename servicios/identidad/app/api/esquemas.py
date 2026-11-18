"""Formas de las peticiones y respuestas de la API de Identidad (JSON en camelCase)."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.alias_generators import to_camel

from app.dominio.politicas import Decision
from app.dominio.usuarios import Rol, Usuario

PATRON_CORREO = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class EsquemaBase(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


def _nombre_sin_espacios(nombre: str | None) -> str | None:
    if nombre is not None and not nombre.strip():
        raise ValueError("El nombre no puede estar vacío")
    return nombre


class CredencialesEntrada(EsquemaBase):
    correo: str = Field(min_length=1, max_length=254)
    contrasena: str = Field(min_length=1, max_length=128)


class UsuarioSalida(EsquemaBase):
    id: UUID
    nombre: str
    correo: str
    rol: str | None
    activo: bool

    @classmethod
    def desde(cls, usuario: Usuario) -> "UsuarioSalida":
        return cls(
            id=usuario.id,
            nombre=usuario.nombre,
            correo=usuario.correo,
            rol=usuario.rol,
            activo=usuario.activo,
        )


class AsignacionRolEntrada(EsquemaBase):
    """null quita el rol: el usuario queda sin acceso a funciones internas."""

    rol: Rol | None


class CuentaNuevaEntrada(EsquemaBase):
    """La cuenta se crea sin rol: el rol se asigna aparte con PUT /usuarios/{id}/rol (HU-02)."""

    nombre: str = Field(min_length=1, max_length=120)
    correo: str = Field(max_length=254, pattern=PATRON_CORREO)
    contrasena: str = Field(min_length=8, max_length=72)

    _validar_nombre = field_validator("nombre")(_nombre_sin_espacios)


class CambiosCuentaEntrada(EsquemaBase):
    """Solo se cambian los datos que lleguen."""

    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    correo: str | None = Field(default=None, max_length=254, pattern=PATRON_CORREO)
    contrasena: str | None = Field(default=None, min_length=8, max_length=72)

    _validar_nombre = field_validator("nombre")(_nombre_sin_espacios)

    @model_validator(mode="after")
    def exigir_algun_cambio(self) -> "CambiosCuentaEntrada":
        if self.nombre is None and self.correo is None and self.contrasena is None:
            raise ValueError("Debe indicar al menos un dato para cambiar")
        return self


class SesionSalida(EsquemaBase):
    token: str
    tipo: str = "Bearer"
    expira_en: datetime
    usuario: UsuarioSalida


class SolicitudAutorizacion(BaseModel):
    token: str | None = None
    accion: str
    recurso: str | None = None


class DecisionSalida(EsquemaBase):
    decision: str
    motivo: str
    usuario_id: UUID | None = None
    rol: str | None = None
    nivel_ubicacion: str

    @classmethod
    def desde(cls, decision: Decision) -> "DecisionSalida":
        return cls(
            decision="PERMITIR" if decision.permitir else "DENEGAR",
            motivo=decision.motivo,
            usuario_id=decision.usuario_id,
            rol=decision.rol,
            nivel_ubicacion=decision.nivel_ubicacion,
        )
