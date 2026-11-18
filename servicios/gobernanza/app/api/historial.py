"""Ruta de HU-12: cómo estaba un hallazgo en una fecha y qué cambió hasta hoy."""
from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencias import (
    Autorizador,
    Credenciales,
    exigir_permiso,
    obtener_autorizador,
    obtener_repositorio,
)
from app.api.errores import ErrorApi
from app.api.esquemas import ReconstruccionSalida
from app.dominio.historial import HallazgoSinHistorial, ServicioHistorial, SinVersionEnFecha
from app.repositorio.hallazgos import RepositorioGobernanza

ACCION_PDP = "ver_historial"

router = APIRouter(tags=["historial"])


def obtener_servicio_historial(
    repositorio: Annotated[RepositorioGobernanza, Depends(obtener_repositorio)],
) -> ServicioHistorial:
    return ServicioHistorial(repositorio)


@router.get("/hallazgos/{hallazgo_id}/historial", response_model=ReconstruccionSalida)
def reconstruir_hallazgo(
    hallazgo_id: UUID,
    fecha: Annotated[date, Query(description="Día a reconstruir (AAAA-MM-DD, hora de Colombia)")],
    servicio: Annotated[ServicioHistorial, Depends(obtener_servicio_historial)],
    autorizador: Annotated[Autorizador, Depends(obtener_autorizador)],
    credenciales: Credenciales,
) -> ReconstruccionSalida:
    """La versión vigente en esa fecha (con autor y justificación) comparada con la actual.

    Requiere el rol AUDITOR (lo decide el PDP).
    """
    exigir_permiso(
        autorizador, credenciales, ACCION_PDP, str(hallazgo_id),
        "No tiene permiso para consultar el historial",
    )
    try:
        return ReconstruccionSalida.desde(servicio.reconstruir(hallazgo_id, fecha))
    except HallazgoSinHistorial:
        raise ErrorApi(404, "hallazgo_no_existe", "El hallazgo no existe") from None
    except SinVersionEnFecha as error:
        raise ErrorApi(
            404,
            "sin_version_en_fecha",
            "El hallazgo aún no se había registrado en esa fecha",
            [{"campo": "fecha", "mensaje": f"Primera versión: {error.primera_version.isoformat()}"}],
        ) from None
