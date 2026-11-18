"""Acceso de Gobernanza a la base: reclasificación (HU-08) y reconstrucción histórica (HU-12).

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

from app.dominio.historial import Version
from app.dominio.reclasificacion import Especie, HallazgoActual, Reclasificacion

ACCION_RECLASIFICAR = "reclasificar"

# FOR UPDATE bloquea el hallazgo hasta el commit: si dos científicos reclasifican a la vez,
# el segundo espera y calcula su número de versión con lo que dejó el primero.
# Va SIN join a propósito: con un join, el que espera revisa la fila nueva (con la especie ya
# cambiada) contra la especie vieja, no coincide y el hallazgo "desaparece" (HallazgoNoExiste).
SQL_HALLAZGO = text(
    "SELECT id, especie_id, version_actual FROM campo.hallazgo WHERE id = :id FOR UPDATE"
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

COLUMNAS_VERSION = "numero, especie, atributos, autor_id, justificacion, vigente_desde"

# Usan el índice hallazgo_version_por_fecha (hallazgo_id, vigente_desde): responden en milisegundos.
SQL_VIGENTE_EN = text(
    f"""
    SELECT {COLUMNAS_VERSION} FROM gobernanza.hallazgo_version
    WHERE hallazgo_id = :hallazgo_id AND vigente_desde < :instante
    ORDER BY vigente_desde DESC, numero DESC
    LIMIT 1
    """
)

SQL_EXTREMO = (
    "SELECT {columnas} FROM gobernanza.hallazgo_version "
    "WHERE hallazgo_id = :hallazgo_id ORDER BY numero {orden} LIMIT 1"
)
SQL_ACTUAL = text(SQL_EXTREMO.format(columnas=COLUMNAS_VERSION, orden="DESC"))
SQL_PRIMERA = text(SQL_EXTREMO.format(columnas=COLUMNAS_VERSION, orden="ASC"))

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
        especie = self.obtener_especie(fila.especie_id)  # ya con el bloqueo: lee la especie vigente
        return HallazgoActual(fila.id, fila.especie_id, especie.nombre_cientifico, fila.version_actual)

    def obtener_especie(self, especie_id: UUID) -> Especie | None:
        fila = self._sesion.execute(SQL_ESPECIE, {"id": especie_id}).first()
        return Especie(fila.id, fila.nombre_cientifico) if fila else None

    def version_vigente_en(self, hallazgo_id: UUID, instante) -> Version | None:
        return _a_version(
            self._sesion.execute(SQL_VIGENTE_EN, {"hallazgo_id": hallazgo_id, "instante": instante}).first()
        )

    def version_actual(self, hallazgo_id: UUID) -> Version | None:
        return _a_version(self._sesion.execute(SQL_ACTUAL, {"hallazgo_id": hallazgo_id}).first())

    def primera_version(self, hallazgo_id: UUID) -> Version | None:
        return _a_version(self._sesion.execute(SQL_PRIMERA, {"hallazgo_id": hallazgo_id}).first())

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


def _a_version(fila) -> Version | None:
    if fila is None:
        return None
    return Version(
        fila.numero, fila.especie, fila.atributos or {}, fila.autor_id, fila.justificacion, fila.vigente_desde
    )
