"""Cliente del PDP (interfaz IAutorizacion del servicio Identidad).

REGLA DEL EQUIPO (RNF-05): ningún servicio decide permisos por su cuenta.
Antes de cada operación sensible se le pregunta al PDP:

    from app.autorizacion import autorizar
    if not autorizar(token, "reclasificar", hallazgo_id):
        raise HTTPException(status_code=403, detail="Sin permiso")

Si el PDP no responde, se NIEGA (falla segura).
"""
import httpx

from app.config import IDENTIDAD_URL


def autorizar(token: str, accion: str, recurso: str | None = None) -> bool:
    try:
        respuesta = httpx.post(
            f"{IDENTIDAD_URL}/interno/autorizar",
            json={"token": token, "accion": accion, "recurso": recurso},
            timeout=2.0,
        )
        return respuesta.status_code == 200 and respuesta.json().get("decision") == "PERMITIR"
    except httpx.HTTPError:
        return False
