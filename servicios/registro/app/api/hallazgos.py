"""Rutas de HU-03: consultar la ficha de un tipo de especie y registrar un hallazgo."""
from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.api.errores import ErrorApi
from app.api.esquemas import AtributoFicha, FichaSalida, HallazgoCreado, HallazgoEntrada
from app.autorizacion import autorizar
from app.config import INVESTIGADOR_PRUEBA_ID
from app.db import obtener_sesion
from app.dominio.hallazgos import NuevoHallazgo
from app.dominio.servicio_hallazgos import (
    EspecieNoExiste,
    ExpedicionNoExiste,
    FichaInvalida,
    ServicioHallazgos,
)
from app.repositorio.hallazgos import RepositorioHallazgos

ACCION_PDP = "registrar_hallazgo"

Autorizador = Callable[[str, str, str | None], bool]

router = APIRouter(tags=["hallazgos"])
   # auto_error=False: el 401 lo damos nosotros, con el formato de errores del equipo.
esquema_bearer = HTTPBearer(auto_error=False)
Credenciales = Annotated[HTTPAuthorizationCredentials | None, Depends(esquema_bearer)]


def obtener_repositorio(sesion: Annotated[Session, Depends(obtener_sesion)]) -> RepositorioHallazgos:
    return RepositorioHallazgos(sesion)


def obtener_servicio(
    repositorio: Annotated[RepositorioHallazgos, Depends(obtener_repositorio)],
) -> ServicioHallazgos:
    return ServicioHallazgos(repositorio)


def obtener_autorizador() -> Autorizador:
    """Las pruebas lo reemplazan para no depender del PDP."""
    return autorizar


def extraer_token(credenciales: HTTPAuthorizationCredentials | None) -> str:
       if credenciales is not None and credenciales.credentials.strip():
           return credenciales.credentials.strip()
       raise ErrorApi(401, "no_autenticado", "Falta el encabezado Authorization: Bearer <token>")


@router.get("/tipos-especie/{tipo_especie_id}/ficha", response_model=FichaSalida)
def obtener_ficha(
    tipo_especie_id: UUID,
    repositorio: Annotated[RepositorioHallazgos, Depends(obtener_repositorio)],
) -> FichaSalida:
    """Atributos de la ficha vigente de un tipo de especie (para armar el formulario)."""
    ficha = repositorio.obtener_ficha_vigente(tipo_especie_id)
    if ficha is None:
        raise ErrorApi(
            404, "ficha_no_existe", "El tipo de especie no existe o no tiene una ficha publicada"
        )
    return FichaSalida(
        tipo_especie_id=ficha.tipo_especie_id,
        nombre=ficha.nombre,
        revision=ficha.revision,
        atributos=[
            AtributoFicha(
                clave=a.clave,
                etiqueta=a.etiqueta,
                tipo=a.tipo.value,
                obligatorio=a.obligatorio,
                reglas=a.reglas,
            )
            for a in ficha.atributos
        ],
    )


@router.post("/hallazgos", response_model=HallazgoCreado, status_code=status.HTTP_201_CREATED)
def registrar_hallazgo(
    entrada: HallazgoEntrada,
    servicio: Annotated[ServicioHallazgos, Depends(obtener_servicio)],
    autorizador: Annotated[Autorizador, Depends(obtener_autorizador)],
    credenciales: Credenciales,
) -> HallazgoCreado:
    """Registra un hallazgo con su versión inicial. Requiere el rol INVESTIGADOR (lo decide el PDP)."""
    token = extraer_token(credenciales)
    if not autorizador(token, ACCION_PDP, None):
        raise ErrorApi(403, "sin_permiso", "No tiene permiso para registrar hallazgos")

    datos = NuevoHallazgo(
        especie_id=entrada.especie_id,
        expedicion_id=entrada.expedicion_id,
        investigador_id=UUID(INVESTIGADOR_PRUEBA_ID),  # TODO (HU-01): tomarlo del token
        fecha_hallazgo=entrada.fecha_hallazgo,
        latitud=entrada.latitud,
        longitud=entrada.longitud,
        precision_m=entrada.precision_m,
        region=entrada.region,
        departamento=entrada.departamento,
        ecosistema=entrada.ecosistema,
        atributos=entrada.atributos,
    )
    try:
        hallazgo_id = servicio.registrar(datos)
    except EspecieNoExiste:
        raise ErrorApi(404, "especie_no_existe", "La especie indicada no existe") from None
    except ExpedicionNoExiste:
        raise ErrorApi(404, "expedicion_no_existe", "La expedición indicada no existe") from None
    except FichaInvalida as error:
        raise ErrorApi(
            422, "ficha_invalida", "Los atributos no cumplen la ficha de la especie", error.errores
        ) from None
    return HallazgoCreado(hallazgo_id=hallazgo_id, version=1)
