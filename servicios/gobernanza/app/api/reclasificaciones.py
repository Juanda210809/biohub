"""Ruta de HU-08: reclasificar un hallazgo como otra especie."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencias import (
    Autorizador,
    Credenciales,
    exigir_permiso,
    obtener_autorizador,
    obtener_repositorio,
)
from app.api.errores import ErrorApi
from app.api.esquemas import ReclasificacionEntrada, ReclasificacionSalida
from app.dominio.reclasificacion import (
    EspecieNoExiste,
    HallazgoNoExiste,
    MismaEspecie,
    ServicioReclasificacion,
)
from app.repositorio.hallazgos import RepositorioGobernanza

ACCION_PDP = "reclasificar"

router = APIRouter(tags=["reclasificación"])


def obtener_servicio(
    repositorio: Annotated[RepositorioGobernanza, Depends(obtener_repositorio)],
) -> ServicioReclasificacion:
    return ServicioReclasificacion(repositorio)


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
    decision = exigir_permiso(
        autorizador, credenciales, ACCION_PDP, str(hallazgo_id),
        "No tiene permiso para reclasificar hallazgos",
    )
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
