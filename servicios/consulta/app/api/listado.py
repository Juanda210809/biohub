"""Listado público de hallazgos para el portal: sirve para escoger uno y abrir su ficha.

Usa la misma consulta y la misma lista blanca que la API externa (HU-13): lee hallazgo_publico,
que no tiene coordenadas, así que el listado nunca puede devolver la ubicación exacta (RF-08).
A diferencia de /externa/v1, no pide apikey ni cuota: es la ruta del portal por /api/v1/consulta.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.externa import LIMITE_MAXIMO, listar_hallazgos_publicos
from app.autorizacion import autorizar
from app.db import obtener_sesion

router = APIRouter(prefix="/hallazgos", tags=["fichas públicas"])


def token_de(authorization: str | None) -> str | None:
    """El token de 'Authorization: Bearer <token>', o None si no viene o tiene otro esquema."""
    if not authorization:
        return None
    esquema, separador, credencial = authorization.partition(" ")
    if separador and esquema.lower() == "bearer":
        return credencial.strip() or None
    return None


@router.get("")
def listar_hallazgos(
    sesion: Annotated[Session, Depends(obtener_sesion)],
    limite: Annotated[int, Query(ge=1, le=LIMITE_MAXIMO)] = 50,
    desplazamiento: Annotated[int, Query(ge=0)] = 0,
    authorization: Annotated[str | None, Header()] = None,
):
    """Hallazgos públicos, del más reciente al más antiguo, paginados y sin coordenadas."""
    # Toda consulta pasa por el PDP (RNF-05), también la del visitante sin sesión.
    if not autorizar(token_de(authorization), "ver_ficha_publica"):
        raise HTTPException(status_code=403, detail="Sin permiso")

    hallazgos = listar_hallazgos_publicos(sesion, limite, desplazamiento)
    return {
        "hallazgos": hallazgos,
        "limite": limite,
        "desplazamiento": desplazamiento,
        "cantidad": len(hallazgos),
    }
