"""Ruta de HU-08: reclasificar un hallazgo como otra especie."""
from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.api.errores import ErrorApi
from app.api.esquemas import ReclasificacionEntrada, ReclasificacionSalida
from app.autorizacion import DecisionPDP, autorizar
from app.db import obtener_sesion
from app.dominio.reclasificacion import (
    EspecieNoExiste,
    HallazgoNoExiste,
    MismaEspecie,
    ServicioReclasificacion,
)
from app.repositorio.hallazgos import RepositorioGobernanza

ACCION_PDP = "reclasificar"

Autorizador = Callable[[str, str, str | None], DecisionPDP]

router = APIRouter(tags=["reclasificación"])
# auto_error=False: el 401 lo damos nosotros, con el formato de errores del equipo.
esquema_bearer = HTTPBearer(auto_error=False)
Credenciales = Annotated[HTTPAuthorizationCredentials | None, Depends(esquema_bearer)]


def obtener_repositorio(sesion: Annotated[Session, Depends(obtener_sesion)]) -> RepositorioGobernanza:
    return RepositorioGobernanza(sesion)


def obtener_servicio(
    repositorio: Annotated[RepositorioGobernanza, Depends(obtener_repositorio)],
) -> ServicioReclasificacion:
    return ServicioReclasificacion(repositorio)


def obtener_autorizador() -> Autorizador:
    """Las pruebas lo reemplazan para no depender del PDP."""
    return autorizar


def extraer_token(credenciales: HTTPAuthorizationCredentials | None) -> str:
    if credenciales is not None and credenciales.credentials.strip():
        return credenciales.credentials.strip()
    raise ErrorApi(401, "no_autenticado", "Falta el encabezado Authorization: Bearer <token>")


@router.post(
    "/hallazgos/{hallazgo_id}/reclasificaciones",
    response_model=ReclasificacionSalida,
    status_code=status.HTTP_201_CREATED,
)
def reclasificar_hallazgo(
    hallazgo_id: UUID,
    entrada: ReclasificacionEntrada,
    servicio: Annotated[ServicioReclasificacion, Depends(obtener_servicio)],
    autorizador: Annotated[Autorizador, Depends(obtener_autorizador)],
    credenciales: Credenciales,
) -> ReclasificacionSalida:
    """Reclasifica un hallazgo y deja una versión nueva en su historial.

    Requiere el rol CIENTIFICO_AUTORIZADO (lo decide el PDP). La versión anterior no se borra.
    """
    token = extraer_token(credenciales)
    decision = autorizador(token, ACCION_PDP, str(hallazgo_id))
    if not decision.permitido:
        raise ErrorApi(403, "sin_permiso", "No tiene permiso para reclasificar hallazgos")

    try:
        resultado = servicio.reclasificar(
            hallazgo_id=hallazgo_id,
            especie_id=entrada.especie_id,
            justificacion=entrada.justificacion,
            autor_id=decision.usuario_id,  # quien autoriza sale del token, no del cuerpo
        )
    except HallazgoNoExiste:
        raise ErrorApi(404, "hallazgo_no_existe", "El hallazgo no existe") from None
    except EspecieNoExiste:
        raise ErrorApi(404, "especie_no_existe", "La especie indicada no existe") from None
    except MismaEspecie:
        raise ErrorApi(
            409, "misma_especie", "El hallazgo ya está clasificado como esa especie"
        ) from None
    return ReclasificacionSalida.desde(resultado)
