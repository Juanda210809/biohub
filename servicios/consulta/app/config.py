"""Configuración del servicio: todo viene de variables de entorno (docker-compose.yml y .env)."""
import os

SERVICIO = os.getenv("SERVICIO", "consulta")
ROOT_PATH = os.getenv("ROOT_PATH", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")
IDENTIDAD_URL = os.getenv("IDENTIDAD_URL", "http://identidad:8000")
REDIS_URL = os.getenv("REDIS_URL", "")
