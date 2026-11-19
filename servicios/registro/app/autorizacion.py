"""Cliente del PDP (interfaz IAutorizacion del servicio Identidad).

REGLA DEL EQUIPO (RNF-05): ningún servicio decide permisos por su cuenta.
Antes de cada operación sensible se le pregunta al PDP:

    from app.autorizacion import autorizar
    decision = autorizar(token, "registrar_hallazgo")
    if not decision.permitido:
        raise HTTPException(status_code=403, detail="Sin permiso")

Si el PDP no responde, responde algo inválido o permite sin decir quién es el usuario,
se NIEGA (falla segura).
"""
from dataclasses import dataclass
from uuid import UUID

import httpx

from app.config import IDENTIDAD_URL

MOTIVO_PDP_NO_DISPONIBLE = "PDP no disponible o respuesta inválida: se niega"


@dataclass(frozen=True)
class DecisionPDP:
    """La respuesta del PDP. Solo permitido decide; rol y nivel_ubicacion son informativos."""

    permitido: bool
    motivo: str = ""
    usuario_id: UUID | None = None
    rol: str | None = None
    nivel_ubicacion: str = "REGION"


def autorizar(token: str, accion: str, recurso: str | None = None) -> DecisionPDP:
    try:
        respuesta = httpx.post(
            f"{IDENTIDAD_URL}/interno/autorizar",
            json={"token": token, "accion": accion, "recurso": recurso},
            timeout=2.0,
        )
        if respuesta.status_code != 200:
            return DecisionPDP(False, f"{MOTIVO_PDP_NO_DISPONIBLE} (HTTP {respuesta.status_code})")
        datos = respuesta.json()
        if datos.get("decision") != "PERMITIR":
            return DecisionPDP(False, datos.get("motivo") or "Denegado por el PDP")
        return DecisionPDP(
            permitido=True,
            motivo=datos.get("motivo", ""),
            usuario_id=UUID(datos["usuarioId"]),
            rol=datos.get("rol"),
            nivel_ubicacion=datos.get("nivelUbicacion", "REGION"),
        )
    except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError) as error:
        return DecisionPDP(False, f"{MOTIVO_PDP_NO_DISPONIBLE} ({type(error).__name__})")
