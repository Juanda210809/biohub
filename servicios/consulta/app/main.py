"""Servicio Consulta Pública de BioHub.

Dueño: Luna
Historias: HU-05 Consultar ficha pública · HU-06 Ver región o departamento · HU-13 API externa · HU-20 Caché

Documentación automática de las rutas: http://localhost:8000/api/v1/consulta/docs
"""
from fastapi import FastAPI

from app.api import ejemplo, externa
from app.cache import estado_cache
from app.config import ROOT_PATH, SERVICIO
from app.db import estado_bd, filas_publicas

app = FastAPI(title="BioHub · Consulta Pública", root_path=ROOT_PATH)
app.include_router(ejemplo.router)
app.include_router(externa.router)


@app.get("/salud", tags=["salud"])
def salud():
    """Indica si el servicio está vivo y si llega a su base de datos."""
    return {
        "servicio": SERVICIO,
        "estado": "ok",
        "bd": estado_bd(),
        "cache": estado_cache(),
        "filas_hallazgo_publico": filas_publicas(),
    }
