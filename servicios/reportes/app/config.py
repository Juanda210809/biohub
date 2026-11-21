"""Configuración del servicio: todo viene de variables de entorno (docker-compose.yml y .env)."""
import os

SERVICIO = os.getenv("SERVICIO", "reportes")
ROOT_PATH = os.getenv("ROOT_PATH", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")
IDENTIDAD_URL = os.getenv("IDENTIDAD_URL", "http://identidad:8000")

# HU-15: generación automática del índice del mes que terminó. "0" la apaga (las pruebas lo hacen).
REPORTES_AUTOMATICO = os.getenv("REPORTES_AUTOMATICO", "1") != "0"
# Cada cuánto revisa si falta el reporte del mes anterior (segundos).
REPORTES_INTERVALO_S = int(os.getenv("REPORTES_INTERVALO_S", "3600"))
