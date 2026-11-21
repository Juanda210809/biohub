"""Rutas de HU-15: generar y consultar los índices de presión de un mes."""
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencias import (
    Autorizador,
    Credenciales,
    exigir_permiso,
    obtener_autorizador,
    obtener_repositorio,
)
from app.api.errores import ErrorApi
from app.api.esquemas import ReporteSalida
from app.dominio.indices import IndicesNoGenerados, Periodo, PeriodoInvalido, ServicioIndices
from app.repositorio.indices import RepositorioIndicesSql

router = APIRouter(prefix="/indices", tags=["índices de presión"])


def obtener_servicio(
    repositorio: Annotated[RepositorioIndicesSql, Depends(obtener_repositorio)],
) -> ServicioIndices:
    return ServicioIndices(repositorio)


def obtener_reloj():
    """Las pruebas lo reemplazan para fijar "ahora"."""
    return lambda: datetime.now(UTC)


def _periodo(texto: str) -> Periodo:
    try:
        return Periodo.desde_texto(texto)
    except PeriodoInvalido as error:
        raise ErrorApi(
            422, "periodo_invalido", "El mes no es válido", [{"campo": "periodo", "mensaje": str(error)}]
        ) from None


@router.post("/{periodo}", response_model=ReporteSalida, status_code=status.HTTP_201_CREATED)
def generar_indices(
    periodo: str,
    servicio: Annotated[ServicioIndices, Depends(obtener_servicio)],
    autorizador: Annotated[Autorizador, Depends(obtener_autorizador)],
    reloj: Annotated[object, Depends(obtener_reloj)],
    credenciales: Credenciales,
) -> ReporteSalida:
    """Genera (o recalcula) los índices de un mes AAAA-MM. Requiere ALTO_RANGO (lo decide el PDP).

    El cálculo corre sobre la copia de BD Reportes: no frena el registro de hallazgos (RNF-04).
    """
    decision = exigir_permiso(
        autorizador, credenciales, "generar_reporte", periodo, "No tiene permiso para generar reportes"
    )
    try:
        reporte = servicio.generar(_periodo(periodo), "MANUAL", decision.usuario_id, reloj())
    except PeriodoInvalido as error:
        raise ErrorApi(
            422, "periodo_invalido", "El mes no es válido", [{"campo": "periodo", "mensaje": str(error)}]
        ) from None
    return ReporteSalida.desde(reporte)


@router.get("/{periodo}", response_model=ReporteSalida)
def consultar_indices(
    periodo: str,
    servicio: Annotated[ServicioIndices, Depends(obtener_servicio)],
    autorizador: Annotated[Autorizador, Depends(obtener_autorizador)],
    credenciales: Credenciales,
) -> ReporteSalida:
    """Los índices de un mes AAAA-MM, del más alto al más bajo. Requiere ALTO_RANGO."""
    exigir_permiso(autorizador, credenciales, "ver_reportes", periodo, "No tiene permiso para ver reportes")
    try:
        return ReporteSalida.desde(servicio.consultar(_periodo(periodo)))
    except IndicesNoGenerados:
        raise ErrorApi(404, "indices_no_generados", f"Aún no hay índices de {periodo}") from None
