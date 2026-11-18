"""Acceso de Registro a la base de datos para publicar una revisión nueva de ficha (HU-04).

La sesión llega desde afuera (no se crea aquí), así las pruebas pueden darle una falsa.
Todo es SQL explícito con text(), igual que en repositorio/hallazgos.py.
"""
import json
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.dominio.hallazgos import FichaVigente
from app.dominio.validadores import DefinicionAtributo
from app.repositorio.hallazgos import SQL_AUDITORIA, RepositorioHallazgos

ACCION_DEFINIR_FICHA = "definir_ficha"

# Bloquea la fila del tipo de especie: dos personas no pueden publicar a la vez sobre el mismo tipo.
SQL_BLOQUEAR_TIPO = text("SELECT id FROM campo.tipo_especie WHERE id = :id FOR UPDATE")

# Primero se reemplaza la vigente y después se inserta la nueva: el índice único parcial
# revision_ficha_vigente solo deja UNA revisión PUBLICADA por tipo de especie.
SQL_REEMPLAZAR = text(
    """
    UPDATE campo.revision_ficha SET estado = 'REEMPLAZADA'
    WHERE tipo_especie_id = :tipo AND estado = 'PUBLICADA'
    """
)

SQL_REVISION = text(
    """
    INSERT INTO campo.revision_ficha (id, tipo_especie_id, numero, estado, publicada_en, publicada_por)
    VALUES (:id, :tipo, :numero, 'PUBLICADA', now(), :publicada_por)
    """
)

SQL_DEFINICION = text(
    """
    INSERT INTO campo.definicion_atributo
        (id, revision_ficha_id, clave, etiqueta, tipo, obligatorio, reglas, publicable)
    VALUES
        (:id, :revision_id, :clave, :etiqueta, :tipo, :obligatorio, CAST(:reglas AS jsonb), :publicable)
    """
)


class RepositorioFichas:
    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def obtener_ficha_para_publicar(self, tipo_especie_id: UUID) -> FichaVigente | None:
        """Bloquea el tipo de especie y devuelve su ficha vigente. Hay que cerrar con
        publicar_revision (que hace commit) o con cancelar."""
        fila = self._sesion.execute(SQL_BLOQUEAR_TIPO, {"id": tipo_especie_id}).first()
        if fila is None:
            return None
        return RepositorioHallazgos(self._sesion).obtener_ficha_vigente(tipo_especie_id)

    def publicar_revision(
        self, ficha: FichaVigente, nuevas: list[DefinicionAtributo], autor_id: UUID
    ) -> FichaVigente:
        """Reemplaza la revisión vigente por la nueva en UNA transacción (commit o rollback).

        Los hallazgos ya registrados no se tocan: sus atributos viven en
        gobernanza.hallazgo_version y no dependen de las definiciones de la ficha.
        """
        revision_id = uuid4()
        numero = ficha.revision + 1
        try:
            self._sesion.execute(SQL_REEMPLAZAR, {"tipo": ficha.tipo_especie_id})
            self._sesion.execute(
                SQL_REVISION,
                {
                    "id": revision_id,
                    "tipo": ficha.tipo_especie_id,
                    "numero": numero,
                    "publicada_por": autor_id,
                },
            )
            for definicion in nuevas:
                self._sesion.execute(
                    SQL_DEFINICION,
                    {
                        "id": uuid4(),
                        "revision_id": revision_id,
                        "clave": definicion.clave,
                        "etiqueta": definicion.etiqueta.strip(),
                        "tipo": definicion.tipo.value,
                        "obligatorio": definicion.obligatorio,
                        "reglas": json.dumps(definicion.reglas, ensure_ascii=False),
                        "publicable": definicion.publicable,
                    },
                )
            self._sesion.execute(
                SQL_AUDITORIA,
                {
                    "id": uuid4(),
                    "actor_id": autor_id,
                    "accion": ACCION_DEFINIR_FICHA,
                    "recurso_id": ficha.tipo_especie_id,
                },
            )
            self._sesion.commit()
        except Exception:
            self._sesion.rollback()
            raise
        atributos = sorted(nuevas, key=lambda definicion: definicion.clave)
        return FichaVigente(ficha.tipo_especie_id, ficha.nombre, numero, atributos)

    def cancelar(self) -> None:
        """Deshace la transacción abierta y libera el bloqueo del tipo de especie."""
        self._sesion.rollback()
