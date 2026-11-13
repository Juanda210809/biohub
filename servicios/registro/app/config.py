"""Configuración del servicio: todo viene de variables de entorno (docker-compose.yml y .env)."""
import os

SERVICIO = os.getenv("SERVICIO", "registro")
ROOT_PATH = os.getenv("ROOT_PATH", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")
IDENTIDAD_URL = os.getenv("IDENTIDAD_URL", "http://identidad:8000")
# TODO (HU-01, Matheus): reemplazar por el id del investigador que venga en el token.
INVESTIGADOR_PRUEBA_ID = os.getenv("INVESTIGADOR_PRUEBA_ID", "00000000-0000-0000-0000-0000000000aa")
