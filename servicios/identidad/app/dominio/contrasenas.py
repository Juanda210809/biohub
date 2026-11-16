"""Contraseñas con bcrypt: solo se guarda el hash."""
from functools import cache

import bcrypt

RONDAS = 12


def hashear(contrasena: str, rondas: int = RONDAS) -> str:
    return bcrypt.hashpw(contrasena.encode(), bcrypt.gensalt(rondas)).decode()


def verificar(contrasena: str, hash_guardado: str) -> bool:
    try:
        return bcrypt.checkpw(contrasena.encode(), hash_guardado.encode())
    except ValueError:
        return False


@cache
def hash_de_relleno() -> str:
    """Se compara contra él cuando el correo no existe, para tardar lo mismo que un intento real."""
    return hashear("contrasena-de-relleno-que-nadie-usa")
