"""Servicio Gobernanza Científica de BioHub.

Dueño: Guarnizo
Historias: HU-08 Reclasificar hallazgo · HU-12 Reconstrucción histórica por fecha

Documentación automática de las rutas: http://localhost:8000/api/v1/gobernanza/docs
"""
from fastapi import FastAPI

from app.api import ejemplo
from app.config import ROOT_PATH, SERVICIO
from app.db import estado_bd

app = FastAPI(title="BioHub · Gobernanza Científica", root_path=ROOT_PATH)
app.include_router(ejemplo.router)


@app.get("/salud", tags=["salud"])
def salud():
    """Indica si el servicio está vivo y si llega a su base de datos."""
    return {
        "servicio": SERVICIO,
        "estado": "ok",
        "bd": estado_bd(),
    }
