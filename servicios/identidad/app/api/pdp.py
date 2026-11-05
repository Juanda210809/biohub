"""PDP: Punto de Decisión de Políticas (interfaz IAutorizacion).

Es el ÚNICO lugar del sistema donde se decide quién puede hacer qué (RNF-05).
Los demás servicios lo llaman con POST /interno/autorizar.
Kong bloquea esta ruta desde afuera: solo se usa dentro de la red de Docker.

Por ahora NIEGA TODO (falla segura). Matheus implementa las reglas reales:
validar el JWT, que el usuario esté activo y su rol (HU-01, HU-02).
"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/interno", tags=["interno (PDP)"])


class SolicitudAutorizacion(BaseModel):
    token: str | None = None
    accion: str
    recurso: str | None = None


@router.post("/autorizar")
def autorizar(solicitud: SolicitudAutorizacion):
    # TODO (Matheus): decidir según el rol del usuario del token.
    return {"decision": "DENEGAR", "motivo": "PDP sin reglas todavía"}
