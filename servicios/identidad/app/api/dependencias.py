"""Arma los objetos que usan las rutas. Las pruebas reemplazan el repositorio y los tokens."""
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.api.errores import ErrorApi
from app.config import JWT_SECRET, TOKEN_MINUTOS
from app.db import obtener_sesion
from app.dominio.autenticacion import ServicioAutenticacion
from app.dominio.politicas import ServicioAutorizacion
from app.dominio.tokens import ServicioTokens
from app.repositorio.usuarios import RepositorioUsuarios

# auto_error=False: el 401 lo damos nosotros, con el formato de errores del equipo.
esquema_bearer = HTTPBearer(auto_error=False)
Credenciales = Annotated[HTTPAuthorizationCredentials | None, Depends(esquema_bearer)]


def obtener_repositorio(sesion: Annotated[Session, Depends(obtener_sesion)]) -> RepositorioUsuarios:
    return RepositorioUsuarios(sesion)


def obtener_tokens() -> ServicioTokens:
    return ServicioTokens(JWT_SECRET, TOKEN_MINUTOS)


def obtener_autenticacion(
    repositorio: Annotated[RepositorioUsuarios, Depends(obtener_repositorio)],
    tokens: Annotated[ServicioTokens, Depends(obtener_tokens)],
) -> ServicioAutenticacion:
    return ServicioAutenticacion(repositorio, tokens)


def obtener_autorizacion(
    autenticacion: Annotated[ServicioAutenticacion, Depends(obtener_autenticacion)],
) -> ServicioAutorizacion:
    return ServicioAutorizacion(autenticacion)


def extraer_token(credenciales: HTTPAuthorizationCredentials | None) -> str:
    if credenciales is not None and credenciales.credentials.strip():
        return credenciales.credentials.strip()
    raise ErrorApi(401, "no_autenticado", "Falta el encabezado Authorization: Bearer <token>")
