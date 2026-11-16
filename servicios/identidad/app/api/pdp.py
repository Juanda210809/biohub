"""PDP: Punto de Decisión de Políticas (interfaz IAutorizacion).

Es el ÚNICO lugar del sistema donde se decide quién puede hacer qué (RNF-05).
Los demás servicios lo llaman con POST /interno/autorizar.
Kong bloquea esta ruta desde afuera: solo se usa dentro de la red de Docker.
Las reglas están en app/dominio/politicas.py. Si algo falla, NIEGA (falla segura).
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencias import obtener_autorizacion
from app.api.esquemas import DecisionSalida, SolicitudAutorizacion
from app.dominio.politicas import Decision, ServicioAutorizacion

router = APIRouter(prefix="/interno", tags=["interno (PDP)"])
registro = logging.getLogger(__name__)


@router.post("/autorizar", response_model=DecisionSalida)
def autorizar(
    solicitud: SolicitudAutorizacion,
    autorizacion: Annotated[ServicioAutorizacion, Depends(obtener_autorizacion)],
) -> DecisionSalida:
    try:
        decision = autorizacion.autorizar(solicitud.token, solicitud.accion, solicitud.recurso)
    except Exception:
        registro.exception("Falla del PDP; se niega por seguridad")
        decision = Decision(False, "Error interno del PDP: se niega por seguridad")
    return DecisionSalida.desde(decision)
