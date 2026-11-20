"""Consulta de la ficha pública con el patrón Decorator (Entrega 2, sección 6.2 · HU-05, HU-20).

- IConsulta: lo único que necesita la ruta, obtener_ficha(id).
- ConsultaBD: el componente concreto; lee hallazgo_publico de la BD Consulta.
- ConsultaCacheada: el decorador; envuelve otra IConsulta y le pone la caché Redis delante (300 s).

Como solo maneja la ficha pública (sin coordenadas), la caché nunca guarda datos sensibles (RNF-05).
"""
import json
from typing import Any, Protocol
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.cache import guardar_cache, obtener_cache
from app.repositorio.fichas import obtener_ficha_publica

Ficha = dict[str, Any]


class IConsulta(Protocol):
    def obtener_ficha(self, hallazgo_id: UUID) -> Ficha | None:
        """La ficha pública del hallazgo, o None si no existe."""


class ConsultaBD:
    """Componente concreto: lee la ficha pública de la BD Consulta."""

    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def obtener_ficha(self, hallazgo_id: UUID) -> Ficha | None:
        ficha = obtener_ficha_publica(self._sesion, hallazgo_id)
        if ficha is None:
            return None
        # Fechas y UUID como texto: la respuesta es igual venga de la base o de la caché.
        return jsonable_encoder(ficha)


class ConsultaCacheada:
    """Decorador: misma interfaz que IConsulta, con la caché Redis delante (cache-aside)."""

    def __init__(self, interna: IConsulta) -> None:
        self._interna = interna

    def obtener_ficha(self, hallazgo_id: UUID) -> Ficha | None:
        clave = f"ficha_publica:{hallazgo_id}"
        guardada = obtener_cache(clave)
        if guardada is not None:
            try:
                return json.loads(guardada)
            except ValueError:
                pass  # dato dañado en Redis: se ignora y se lee de la fuente
        ficha = self._interna.obtener_ficha(hallazgo_id)
        if ficha is not None:
            guardar_cache(clave, json.dumps(ficha, ensure_ascii=False))
        return ficha


def armar_consulta(sesion: Session) -> IConsulta:
    """Ensambla la cadena: la caché envuelve a la base."""
    return ConsultaCacheada(ConsultaBD(sesion))


def consultar_ficha_publica(sesion: Session, hallazgo_id: UUID) -> Ficha | None:
    """La usa GET /hallazgos/{id}. No sabe si la ficha sale de Redis o de la base."""
    return armar_consulta(sesion).obtener_ficha(hallazgo_id)
