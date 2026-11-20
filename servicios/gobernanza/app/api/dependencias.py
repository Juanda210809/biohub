"""Piezas que comparten las rutas de Gobernanza: token, PDP y repositorio.

Las pruebas reemplazan obtener_autorizador y obtener_repositorio para no depender
del PDP real ni de la base de datos.
"""
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.api.errores import ErrorApi
from app.autorizacion import DecisionPDP, autorizar
from app.db import obtener_sesion
from app.repositorio.hallazgos import RepositorioGobernanza

Autorizador = Callable[[str, str, str | None], DecisionPDP]

# auto_error=False: el 401 lo damos nosotros, con el formato de errores del equipo.
esquema_bearer = HTTPBearer(auto_error=False)
Credenciales = Annotated[HTTPAuthorizationCredentials | None, Depends(esquema_bearer)]


def obtener_repositorio(sesion: Annotated[Session, Depends(obtener_sesion)]) -> RepositorioGobernanza:
    return RepositorioGobernanza(sesion)


def obtener_autorizador() -> Autorizador:
    return autorizar


def extraer_token(credenciales: HTTPAuthorizationCredentials | None) -> str:
    if credenciales is not None and credenciales.credentials.strip():
        return credenciales.credentials.strip()
    raise ErrorApi(401, "no_autenticado", "Falta el encabezado Authorization: Bearer <token>")


def exigir_permiso(autorizador: Autorizador, credenciales, accion: str, recurso: str, mensaje: str):
    """Pregunta al PDP. 401 sin token, 403 si niega. Devuelve la decisión (trae el usuario)."""
    decision = autorizador(extraer_token(credenciales), accion, recurso)
    if not decision.permitido:
        raise ErrorApi(403, "sin_permiso", mensaje)
    return decision
