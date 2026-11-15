
"""Endpoints para consultar fichas públicas."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.dominio.servicio_fichas import consultar_ficha_publica

router = APIRouter(prefix="/hallazgos", tags=["fichas públicas"])


@router.get("/{hallazgo_id}")
def consultar_ficha(
    hallazgo_id: UUID,
    sesion: Annotated[Session, Depends(obtener_sesion)]
):
    """Consulta la ficha pública de un hallazgo."""

    ficha = consultar_ficha_publica(sesion, hallazgo_id)

    if ficha is None:
        raise HTTPException(
            status_code=404,
            detail="No se encontró el hallazgo solicitado."
        )

    return ficha
