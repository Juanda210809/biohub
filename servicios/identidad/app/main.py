"""Servicio Identidad y Autorización de BioHub.

Dueño: Matheus
Historias: HU-01 Iniciar sesión · HU-02 Asignar rol · HU-18 Gestionar cuentas internas

Documentación automática de las rutas: http://localhost:8000/api/v1/identidad/docs
"""
from fastapi import FastAPI

from app.api import pdp, sesiones
from app.api.errores import registrar_manejadores
from app.config import ROOT_PATH, SERVICIO
from app.db import estado_bd

app = FastAPI(title="BioHub · Identidad y Autorización", root_path=ROOT_PATH)
registrar_manejadores(app)
app.include_router(sesiones.router)
app.include_router(pdp.router)


@app.get("/salud", tags=["salud"])
def salud():
    """Indica si el servicio está vivo y si llega a su base de datos."""
    return {
        "servicio": SERVICIO,
        "estado": "ok",
        "bd": estado_bd(),
    }
