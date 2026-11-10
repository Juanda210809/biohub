"""Acceso de Registro a la base de datos: fichas, especies y la creación de un hallazgo.

La sesión llega desde afuera (no se crea aquí), así las pruebas pueden darle una falsa.
Todo es SQL explícito con text(): el INSERT de la versión 1 no puede usar RETURNING porque
Registro no tiene permiso de SELECT sobre gobernanza.hallazgo_version.
"""
import json
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.dominio.hallazgos import Especie, FichaVigente, NuevoHallazgo
from app.dominio.validadores import DefinicionAtributo, TipoAtributo

ACCION_REGISTRAR = "registrar_hallazgo"
JUSTIFICACION_INICIAL = "Registro inicial"

SQL_HALLAZGO = text(
    """
    INSERT INTO campo.hallazgo
        (id, especie_id, expedicion_id, investigador_id, fecha_hallazgo,
         region, departamento, ecosistema)
    VALUES
        (:id, :especie_id, :expedicion_id, :investigador_id, :fecha_hallazgo,
         :region, :departamento, :ecosistema)
    """
)

SQL_UBICACION = text(
    """
    INSERT INTO campo.ubicacion (hallazgo_id, latitud, longitud, precision_m)
    VALUES (:hallazgo_id, :latitud, :longitud, :precision_m)
    """
)

# Solo INSERT, sin RETURNING, con el nombre completo del esquema. vigente_desde se pone sola.
SQL_VERSION_INICIAL = text(
    """
    INSERT INTO gobernanza.hallazgo_version
        (id, hallazgo_id, numero, especie, atributos, autor_id, justificacion)
    VALUES
        (:id, :hallazgo_id, 1, :especie, CAST(:atributos AS jsonb), :autor_id, :justificacion)
    """
)

SQL_PUBLICO = text(
    """
    INSERT INTO campo.hallazgo_publico
        (hallazgo_id, especie, region, departamento, ecosistema, fecha_hallazgo,
         atributos_publicos, version)
    VALUES
        (:hallazgo_id, :especie, :region, :departamento, :ecosistema, :fecha_hallazgo,
         CAST(:atributos_publicos AS jsonb), 1)
    """
)

SQL_AUDITORIA = text(
    """
    INSERT INTO campo.auditoria (id, actor_id, accion, recurso_id)
    VALUES (:id, :actor_id, :accion, :recurso_id)
    """
)


class RepositorioHallazgos:
    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def obtener_especie(self, especie_id: UUID) -> Especie | None:
        fila = self._sesion.execute(
            text("SELECT id, tipo_especie_id, nombre_cientifico FROM campo.especie WHERE id = :id"),
            {"id": especie_id},
        ).first()
        if fila is None:
            return None
        return Especie(fila.id, fila.tipo_especie_id, fila.nombre_cientifico)

    def existe_expedicion(self, expedicion_id: UUID) -> bool:
        fila = self._sesion.execute(
            text("SELECT 1 FROM campo.expedicion WHERE id = :id"), {"id": expedicion_id}
        ).first()
        return fila is not None

    def definiciones_vigentes(self, tipo_especie_id: UUID) -> list[DefinicionAtributo]:
        """Atributos de la revisión PUBLICADA (la vigente) de la ficha de un tipo de especie."""
        filas = self._sesion.execute(
            text(
                """
                SELECT d.clave, d.etiqueta, d.tipo, d.obligatorio, d.reglas, d.publicable
                FROM campo.definicion_atributo d
                JOIN campo.revision_ficha r ON r.id = d.revision_ficha_id
                WHERE r.tipo_especie_id = :tipo AND r.estado = 'PUBLICADA' AND d.activo
                ORDER BY d.clave
                """
            ),
            {"tipo": tipo_especie_id},
        ).all()
        return [
            DefinicionAtributo(
                f.clave, TipoAtributo(f.tipo), f.obligatorio, f.reglas, f.publicable, f.etiqueta
            )
            for f in filas
        ]

    def obtener_ficha_vigente(self, tipo_especie_id: UUID) -> FichaVigente | None:
        fila = self._sesion.execute(
            text(
                """
                SELECT t.nombre, r.numero
                FROM campo.tipo_especie t
                JOIN campo.revision_ficha r ON r.tipo_especie_id = t.id AND r.estado = 'PUBLICADA'
                WHERE t.id = :id
                """
            ),
            {"id": tipo_especie_id},
        ).first()
        if fila is None:
            return None
        atributos = self.definiciones_vigentes(tipo_especie_id)
        return FichaVigente(tipo_especie_id, fila.nombre, fila.numero, atributos)

    def registrar(
        self, datos: NuevoHallazgo, nombre_especie: str, publicos: dict
    ) -> UUID:
        """Guarda el hallazgo completo en UNA transacción: o queda todo o no queda nada."""
        hallazgo_id = uuid4()
        try:
            self._sesion.execute(
                SQL_HALLAZGO,
                {
                    "id": hallazgo_id,
                    "especie_id": datos.especie_id,
                    "expedicion_id": datos.expedicion_id,
                    "investigador_id": datos.investigador_id,
                    "fecha_hallazgo": datos.fecha_hallazgo,
                    "region": datos.region,
                    "departamento": datos.departamento,
                    "ecosistema": datos.ecosistema,
                },
            )
            self._sesion.execute(
                SQL_UBICACION,
                {
                    "hallazgo_id": hallazgo_id,
                    "latitud": datos.latitud,
                    "longitud": datos.longitud,
                    "precision_m": datos.precision_m,
                },
            )
            self._sesion.execute(
                SQL_VERSION_INICIAL,
                {
                    "id": uuid4(),
                    "hallazgo_id": hallazgo_id,
                    "especie": nombre_especie,
                    "atributos": json.dumps(datos.atributos, ensure_ascii=False),
                    "autor_id": datos.investigador_id,
                    "justificacion": JUSTIFICACION_INICIAL,
                },
            )
            self._sesion.execute(
                SQL_PUBLICO,
                {
                    "hallazgo_id": hallazgo_id,
                    "especie": nombre_especie,
                    "region": datos.region,
                    "departamento": datos.departamento,
                    "ecosistema": datos.ecosistema,
                    "fecha_hallazgo": datos.fecha_hallazgo,
                    "atributos_publicos": json.dumps(publicos, ensure_ascii=False),
                },
            )
            self._sesion.execute(
                SQL_AUDITORIA,
                {
                    "id": uuid4(),
                    "actor_id": datos.investigador_id,
                    "accion": ACCION_REGISTRAR,
                    "recurso_id": hallazgo_id,
                },
            )
            self._sesion.commit()
        except Exception:
            self._sesion.rollback()
            raise
        return hallazgo_id
