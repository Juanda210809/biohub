"""Rutas del catálogo para los desplegables del formulario de HU-03.

Las puede usar cualquier rol interno (acción consultar_catalogo del PDP). El tipoEspecieId de
cada especie sirve para pedir su ficha (GET /tipos-especie/{id}/ficha) y armar los campos.
"""
from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.errores import ErrorApi
from app.api.esquemas import EsquemaBase
from app.api.hallazgos import Autorizador, Credenciales, extraer_token, obtener_autorizador
from app.db import obtener_sesion
from app.repositorio.catalogo import RepositorioCatalogo

ACCION_PDP = "consultar_catalogo"

router = APIRouter(tags=["catálogo"])


class EspecieSalida(EsquemaBase):
    id: UUID
    nombre_cientifico: str
    nombre_comun: str | None
    tipo_especie_id: UUID
    tipo_especie: str


class ExpedicionSalida(EsquemaBase):
    id: UUID
    nombre: str
    fecha_inicio: date
    fecha_fin: date | None


def obtener_repositorio_catalogo(
    sesion: Annotated[Session, Depends(obtener_sesion)],
) -> RepositorioCatalogo:
    return RepositorioCatalogo(sesion)


Catalogo = Annotated[RepositorioCatalogo, Depends(obtener_repositorio_catalogo)]


def exigir_permiso(autorizador: Autorizador, credenciales) -> None:
    """401 sin token; 403 si el PDP niega. Se pregunta antes de tocar la base."""
    decision = autorizador(extraer_token(credenciales), ACCION_PDP, None)
    if not decision.permitido:
        raise ErrorApi(403, "sin_permiso", "No tiene permiso para consultar el catálogo")


@router.get("/especies", response_model=list[EspecieSalida])
def listar_especies(
    catalogo: Catalogo,
    autorizador: Annotated[Autorizador, Depends(obtener_autorizador)],
    credenciales: Credenciales,
) -> list[EspecieSalida]:
    """Especies registrables, ordenadas por nombre científico. Cualquier rol interno."""
    exigir_permiso(autorizador, credenciales)
    return [
        EspecieSalida(
            id=e.id,
            nombre_cientifico=e.nombre_cientifico,
            nombre_comun=e.nombre_comun,
            tipo_especie_id=e.tipo_especie_id,
            tipo_especie=e.tipo_especie,
        )
        for e in catalogo.listar_especies()
    ]


@router.get("/expediciones", response_model=list[ExpedicionSalida])
def listar_expediciones(
    catalogo: Catalogo,
    autorizador: Annotated[Autorizador, Depends(obtener_autorizador)],
    credenciales: Credenciales,
) -> list[ExpedicionSalida]:
    """Expediciones, de la más reciente a la más antigua. Cualquier rol interno."""
    exigir_permiso(autorizador, credenciales)
    return [
        ExpedicionSalida(id=x.id, nombre=x.nombre, fecha_inicio=x.fecha_inicio, fecha_fin=x.fecha_fin)
        for x in catalogo.listar_expediciones()
    ]
