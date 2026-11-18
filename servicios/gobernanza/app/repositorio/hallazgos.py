"""Acceso de Gobernanza a la base: leer un hallazgo y guardar su reclasificación (HU-08).

Permisos de svc_gobernanza (los dan los dueños de cada tabla en sus migraciones):
- gobernanza.hallazgo_version: es suya; puede agregar y leer, nunca cambiar ni borrar.
- campo.hallazgo: leer, y cambiar SOLO especie_id y version_actual.
- campo.especie: leer (para saber el nombre de la especie nueva).
- campo.hallazgo_publico: leer, y cambiar SOLO especie, version, atributos_publicos y actualizado_en.
- campo.auditoria: solo agregar.

La sesión llega desde afuera (no se crea aquí), así las pruebas pueden darle una falsa.
"""
from uuid import UUID, uuid4

from sqlalchemy import bindparam, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from app.dominio.reclasificacion import Especie, HallazgoActual, Reclasificacion

ACCION_RECLASIFICAR = "reclasificar"

# FOR UPDATE bloquea el hallazgo hasta el commit: si dos científicos reclasifican a la vez,
# el segundo espera y calcula su número de versión con lo que dejó el primero.
SQL_HALLAZGO = text(
    """
    SELECT h.id, h.especie_id, h.version_actual, e.nombre_cientifico
    FROM campo.hallazgo h
    JOIN campo.especie e ON e.id = h.especie_id
    WHERE h.id = :id
    FOR UPDATE OF h
    """
)

SQL_ESPECIE = text("SELECT id, nombre_cientifico FROM campo.especie WHERE id = :id")

# La versión nueva conserva los atributos de la última: reclasificar cambia la especie, no lo medido.
SQL_ULTIMA_VERSION = text(
    """
    SELECT numero, atributos
    FROM gobernanza.hallazgo_version
    WHERE hallazgo_id = :hallazgo_id
    ORDER BY numero DESC
    LIMIT 1
    """
)

SQL_NUEVA_VERSION = text(
    """
    INSERT INTO gobernanza.hallazgo_version
        (id, hallazgo_id, numero, especie, atributos, autor_id, justificacion)
    VALUES
        (:id, :hallazgo_id, :numero, :especie, :atributos, :autor_id, :justificacion)
    RETURNING vigente_desde
    """
).bindparams(bindparam("atributos", type_=JSONB))

SQL_ACTUALIZAR_HALLAZGO = text(
    "UPDATE campo.hallazgo SET especie_id = :especie_id, version_actual = :numero WHERE id = :id"
)

SQL_ACTUALIZAR_PUBLICO = text(
    """
    UPDATE campo.hallazgo_publico
    SET especie = :especie, version = :numero, actualizado_en = now()
    WHERE hallazgo_id = :hallazgo_id
    """
)

SQL_AUDITORIA = text(
    """
    INSERT INTO campo.auditoria (id, actor_id, accion, recurso_id)
    VALUES (:id, :actor_id, :accion, :recurso_id)
    """
)


class RepositorioGobernanza:
    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def obtener_hallazgo(self, hallazgo_id: UUID) -> HallazgoActual | None:
        fila = self._sesion.execute(SQL_HALLAZGO, {"id": hallazgo_id}).first()
        if fila is None:
            return None
        return HallazgoActual(fila.id, fila.especie_id, fila.nombre_cientifico, fila.version_actual)

    def obtener_especie(self, especie_id: UUID) -> Especie | None:
        fila = self._sesion.execute(SQL_ESPECIE, {"id": especie_id}).first()
        return Especie(fila.id, fila.nombre_cientifico) if fila else None

    def descartar(self) -> None:
        self._sesion.rollback()

    def reclasificar(
        self, hallazgo: HallazgoActual, especie: Especie, justificacion: str, autor_id: UUID
    ) -> Reclasificacion:
        """Guarda la reclasificación en UNA transacción: o queda todo o no queda nada."""
        try:
            ultima = self._sesion.execute(SQL_ULTIMA_VERSION, {"hallazgo_id": hallazgo.id}).first()
            numero = max(hallazgo.version_actual, ultima.numero if ultima else 0) + 1
            atributos = ultima.atributos if ultima else {}

            vigente_desde = self._sesion.execute(
                SQL_NUEVA_VERSION,
                {
                    "id": uuid4(),
                    "hallazgo_id": hallazgo.id,
                    "numero": numero,
                    "especie": especie.nombre_cientifico,
                    "atributos": atributos,
                    "autor_id": autor_id,
                    "justificacion": justificacion,
                },
            ).scalar_one()
            self._sesion.execute(
                SQL_ACTUALIZAR_HALLAZGO,
                {"especie_id": especie.id, "numero": numero, "id": hallazgo.id},
            )
            self._sesion.execute(
                SQL_ACTUALIZAR_PUBLICO,
                {"especie": especie.nombre_cientifico, "numero": numero, "hallazgo_id": hallazgo.id},
            )
            self._sesion.execute(
                SQL_AUDITORIA,
                {
                    "id": uuid4(),
                    "actor_id": autor_id,
                    "accion": ACCION_RECLASIFICAR,
                    "recurso_id": hallazgo.id,
                },
            )
            self._sesion.commit()
        except Exception:
            self._sesion.rollback()
            raise
        return Reclasificacion(
            hallazgo_id=hallazgo.id,
            version=numero,
            especie_anterior=hallazgo.especie_nombre,
            especie_nueva=especie.nombre_cientifico,
            autor_id=autor_id,
            justificacion=justificacion,
            vigente_desde=vigente_desde,
        )

