"""Servicio Registro y Gestión de Campo de BioHub.

Dueño: Peña
Historias: HU-03 Registrar hallazgo · HU-04 Definir atributos de la ficha ·
HU-21 Registro disponible durante picos de consulta

Documentación automática de las rutas: http://localhost:8000/api/v1/registro/docs
"""
from fastapi import FastAPI

from app.api import hallazgos
from app.api.errores import registrar_manejadores
from app.config import ROOT_PATH, SERVICIO
from app.db import estado_bd

app = FastAPI(title="BioHub · Registro y Gestión de Campo", root_path=ROOT_PATH)
registrar_manejadores(app)
app.include_router(hallazgos.router)


@app.get("/salud", tags=["salud"])
def salud():
    """Indica si el servicio está vivo y si llega a su base de datos."""
    return {
        "servicio": SERVICIO,
        "estado": "ok",
        "bd": estado_bd(),
    }
