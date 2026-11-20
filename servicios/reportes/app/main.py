"""Servicio Reportes y Analítica de BioHub.

Dueño: Guarnizo
Historias: HU-15 Generar índices de presión mensuales

Documentación automática de las rutas: http://localhost:8000/api/v1/reportes/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.orm import sessionmaker

from app.api import indices
from app.api.errores import registrar_manejadores
from app.config import DATABASE_URL, REPORTES_AUTOMATICO, REPORTES_INTERVALO_S, ROOT_PATH, SERVICIO
from app.db import estado_bd, motor
from app.dominio.indices import ServicioIndices
from app.programador import ProgramadorMensual
from app.repositorio.indices import RepositorioIndicesSql


def generar_si_falta(ahora):
    """Una vuelta del programador: una sesión nueva cada vez, cerrada al terminar."""
    sesion = sessionmaker(bind=motor())()
    try:
        return ServicioIndices(RepositorioIndicesSql(sesion)).generar_mes_anterior_si_falta(ahora)
    finally:
        sesion.close()


@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    programador = None
    if REPORTES_AUTOMATICO and DATABASE_URL:
        programador = ProgramadorMensual(generar_si_falta, REPORTES_INTERVALO_S)
        programador.iniciar()
    yield
    if programador is not None:
        programador.detener()


app = FastAPI(title="BioHub · Reportes y Analítica", root_path=ROOT_PATH, lifespan=ciclo_de_vida)
registrar_manejadores(app)
app.include_router(indices.router)


@app.get("/salud", tags=["salud"])
def salud():
    """Indica si el servicio está vivo y si llega a su base de datos."""
    return {
        "servicio": SERVICIO,
        "estado": "ok",
        "bd": estado_bd(),
    }
