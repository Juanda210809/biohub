"""Formas de las peticiones y respuestas de la API de Identidad (JSON en camelCase)."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.dominio.politicas import Decision
from app.dominio.usuarios import Usuario


class EsquemaBase(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


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
