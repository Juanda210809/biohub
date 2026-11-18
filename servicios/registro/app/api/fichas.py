"""Ruta de HU-04: definir y modificar los atributos de la ficha de un tipo de especie.

El GET de la ficha vigente sigue en hallazgos.py (HU-03). Aquí solo está el PUT, que publica
una revisión nueva de la ficha sin tocar código ni detener el sistema (RNF-01).
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.errores import ErrorApi
from app.api.esquemas import FichaEntrada, FichaSalida, ficha_a_salida
from app.api.hallazgos import Autorizador, Credenciales, extraer_token, obtener_autorizador
from app.db import obtener_sesion
from app.dominio.servicio_fichas import (
    DefinicionInvalida,
    FichaNoExiste,
    RevisionDesactualizada,
    ServicioFichas,
)
from app.dominio.validadores import DefinicionAtributo
from app.repositorio.fichas import RepositorioFichas

ACCION_PDP = "definir_ficha"

router = APIRouter(tags=["fichas"])


def obtener_repositorio_fichas(
    sesion: Annotated[Session, Depends(obtener_sesion)],
) -> RepositorioFichas:
    return RepositorioFichas(sesion)


def obtener_servicio_fichas(
    repositorio: Annotated[RepositorioFichas, Depends(obtener_repositorio_fichas)],
) -> ServicioFichas:
    return ServicioFichas(repositorio)


@router.put("/tipos-especie/{tipo_especie_id}/ficha", response_model=FichaSalida)
def definir_ficha(
    tipo_especie_id: UUID,
    entrada: FichaEntrada,
    servicio: Annotated[ServicioFichas, Depends(obtener_servicio_fichas)],
    autorizador: Annotated[Autorizador, Depends(obtener_autorizador)],
    credenciales: Credenciales,
) -> FichaSalida:
    """Publica una revisión nueva con la lista completa de atributos que quedará vigente.

    Para agregar o modificar un atributo se envía la lista con el cambio; para quitarlo, se omite.
    Requiere el rol CIENTIFICO_AUTORIZADO (lo decide el PDP). Los hallazgos ya registrados no
    cambian. Si la ficha cambió mientras se editaba (revisionBase), responde 409.
    """
    token = extraer_token(credenciales)
    decision = autorizador(token, ACCION_PDP, None)
    if not decision.permitido:
        raise ErrorApi(403, "sin_permiso", "No tiene permiso para definir fichas")

    nuevas = [
        DefinicionAtributo(
            clave=atributo.clave,
            tipo=atributo.tipo,
            obligatorio=atributo.obligatorio,
            reglas=atributo.reglas,
            publicable=atributo.publicable,
            etiqueta=atributo.etiqueta,
        )
        for atributo in entrada.atributos
    ]
    try:
        ficha = servicio.publicar(tipo_especie_id, entrada.revision_base, nuevas, decision.usuario_id)
    except FichaNoExiste:
        raise ErrorApi(
            404, "ficha_no_existe", "El tipo de especie no existe o no tiene una ficha publicada"
        ) from None
    except RevisionDesactualizada as error:
        raise ErrorApi(
            409,
            "conflicto_de_revision",
            "La ficha cambió mientras la editaba; cárguela de nuevo y repita el cambio",
            [{"campo": "revisionBase", "mensaje": f"la revisión vigente es la {error.revision_actual}"}],
        ) from None
    except DefinicionInvalida as error:
        raise ErrorApi(
            422, "definicion_invalida", "Los atributos de la ficha no son válidos", error.errores
        ) from None
    return ficha_a_salida(ficha)
