"""Acceso de Registro a la base para el catálogo del formulario (HU-03): solo lectura.

La sesión llega desde afuera (no se crea aquí), así las pruebas pueden darle una falsa.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.dominio.catalogo import EspecieCatalogo, ExpedicionCatalogo

SQL_ESPECIES = text(
    """
    SELECT e.id, e.nombre_cientifico, e.nombre_comun, e.tipo_especie_id, t.nombre AS tipo_especie
    FROM campo.especie e
    JOIN campo.tipo_especie t ON t.id = e.tipo_especie_id
    ORDER BY e.nombre_cientifico
    """
)

# Primero las expediciones más recientes: son las que se usan al registrar.
SQL_EXPEDICIONES = text(
    """
    SELECT id, nombre, fecha_inicio, fecha_fin
    FROM campo.expedicion
    ORDER BY fecha_inicio DESC, nombre
    """
)


class RepositorioCatalogo:
    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def listar_especies(self) -> list[EspecieCatalogo]:
        filas = self._sesion.execute(SQL_ESPECIES).all()
        return [
            EspecieCatalogo(f.id, f.nombre_cientifico, f.nombre_comun, f.tipo_especie_id, f.tipo_especie)
            for f in filas
        ]

    def listar_expediciones(self) -> list[ExpedicionCatalogo]:
        filas = self._sesion.execute(SQL_EXPEDICIONES).all()
        return [ExpedicionCatalogo(f.id, f.nombre, f.fecha_inicio, f.fecha_fin) for f in filas]
