"""API externa para universidades y ONG (HU-13).

Llega por Kong en /externa/v1/... con clave y cuota de 60 por minuto (HU-14).
Kong ya validó la clave y la cuota: aquí solo se responden datos públicos.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/externa", tags=["externa"])


@router.get("/hallazgos")
def listar_hallazgos():
    return {"mensaje": "Ruta externa lista. Aquí va el listado público de hallazgos (HU-13)."}
