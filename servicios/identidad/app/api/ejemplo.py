"""Ruta de ejemplo. Bórrala cuando crees las rutas reales de tus historias."""
from fastapi import APIRouter

router = APIRouter(prefix="/ejemplo", tags=["ejemplo"])


@router.get("")
def ejemplo():
    return {"mensaje": "Hola desde identidad. Reemplaza esta ruta por las de tus historias."}
