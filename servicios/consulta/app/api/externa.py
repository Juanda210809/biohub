"""API externa para universidades y ONG (HU-13).

Llega por Kong en /externa/v1/... con clave y cuota de 60 por minuto (HU-14).
Kong ya validó la clave y la cuota: aquí solo se responden datos públicos.

Los campos salen de una lista blanca sobre hallazgo_publico, que no tiene
coordenadas: la API externa nunca puede devolver la ubicación exacta (RF-08).
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.autorizacion import autorizar
from app.db import obtener_sesion

router = APIRouter(prefix="/externa", tags=["externa"])

LIMITE_MAXIMO = 100

# Lista blanca: solo estos campos pueden salir hacia un consumidor externo.
CAMPOS_PUBLICOS = (
    "hallazgo_id",
    "especie",
    "region",
    "departamento",
    "ecosistema",
    "fecha_hallazgo",
    "atributos_publicos",
    "version",
    "actualizado_en",
)

CONSULTA_HALLAZGOS = text(
    f"""
    SELECT {", ".join(CAMPOS_PUBLICOS)}
    FROM campo.hallazgo_publico
    ORDER BY actualizado_en DESC, hallazgo_id
    LIMIT :limite OFFSET :desplazamiento
    """
)


def listar_hallazgos_publicos(sesion: Session, limite: int, desplazamiento: int) -> list[dict]:
    filas = sesion.execute(
        CONSULTA_HALLAZGOS, {"limite": limite, "desplazamiento": desplazamiento}
    ).mappings()
    return [{campo: fila[campo] for campo in CAMPOS_PUBLICOS} for fila in filas]


@router.get("/hallazgos")
def listar_hallazgos(
    sesion: Annotated[Session, Depends(obtener_sesion)],
    limite: Annotated[int, Query(ge=1, le=LIMITE_MAXIMO)] = 50,
    desplazamiento: Annotated[int, Query(ge=0)] = 0,
):
    """Listado público del inventario, paginado y sin coordenadas."""
    # Toda solicitud de ubicación pasa por el PDP (RNF-05); el consumidor externo
    # recibe la política pública: solo región o departamento.
    if not autorizar(None, "ver_ficha_publica"):
        raise HTTPException(status_code=403, detail="Sin permiso")

    hallazgos = listar_hallazgos_publicos(sesion, limite, desplazamiento)
    return {
        "hallazgos": hallazgos,
        "limite": limite,
        "desplazamiento": desplazamiento,
        "cantidad": len(hallazgos),
    }
