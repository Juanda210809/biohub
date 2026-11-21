"""Acceso de Reportes a SU base (BD Reportes): contar hallazgos y guardar los índices (HU-15).

- Lee campo.hallazgo_publico, la copia que llega por replicación (solo lectura para svc_reportes).
- Escribe en su esquema reportes. Nunca se conecta a la base operacional.

La sesión llega desde afuera (no se crea aquí), así las pruebas pueden darle una falsa.
"""
from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.dominio.indices import SIN_ECOSISTEMA, Conteo, IndiceEcosistema, Periodo, ReporteMensual

SQL_CONTAR = text(
    """
    SELECT COALESCE(NULLIF(trim(ecosistema), ''), :sin) AS ecosistema,
           count(*) AS hallazgos,
           count(DISTINCT especie) AS especies
    FROM campo.hallazgo_publico
    WHERE fecha_hallazgo >= :desde AND fecha_hallazgo < :hasta
    GROUP BY 1
    """
)

# Si dos generan el mismo mes a la vez, el segundo espera al primero (no se mezclan filas).
SQL_BLOQUEO = text("SELECT pg_advisory_xact_lock(hashtext('indice_presion'), :clave)")
SQL_BORRAR_MES = text("DELETE FROM reportes.indice_presion WHERE periodo = :periodo")
SQL_EJECUCION = text(
    """
    INSERT INTO reportes.ejecucion_indices (id, periodo, origen, solicitado_por)
    VALUES (:id, :periodo, :origen, :solicitado_por)
    RETURNING generado_en
    """
)
SQL_INDICE = text(
    """
    INSERT INTO reportes.indice_presion
        (periodo, ecosistema, hallazgos, especies_distintas, promedio_previo, indice, nivel, ejecucion_id)
    VALUES
        (:periodo, :ecosistema, :hallazgos, :especies_distintas, :promedio_previo, :indice, :nivel,
         :ejecucion)
    """
)
# La generación más reciente del mes es la dueña de sus filas (cada generación reemplaza las anteriores).
SQL_ULTIMA_EJECUCION = text(
    """
    SELECT origen, solicitado_por, generado_en
    FROM reportes.ejecucion_indices
    WHERE periodo = :periodo
    ORDER BY generado_en DESC
    LIMIT 1
    """
)
SQL_INDICES_DEL_MES = text(
    """
    SELECT ecosistema, hallazgos, especies_distintas, promedio_previo, indice, nivel
    FROM reportes.indice_presion
    WHERE periodo = :periodo
    ORDER BY indice DESC NULLS LAST, ecosistema
    """
)


class RepositorioIndicesSql:
    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def contar(self, desde: date, hasta: date) -> list[Conteo]:
        filas = self._sesion.execute(
            SQL_CONTAR, {"desde": desde, "hasta": hasta, "sin": SIN_ECOSISTEMA}
        ).all()
        return [Conteo(f.ecosistema, f.hallazgos, f.especies) for f in filas]

    def guardar(
        self, periodo: Periodo, indices: list[IndiceEcosistema], origen: str, solicitado_por: UUID | None
    ) -> ReporteMensual:
        """Reemplaza los índices del mes en UNA transacción: o quedan todos o ninguno."""
        try:
            clave = periodo.inicio.year * 100 + periodo.inicio.month
            self._sesion.execute(SQL_BLOQUEO, {"clave": clave})
            self._sesion.execute(SQL_BORRAR_MES, {"periodo": periodo.inicio})
            ejecucion = uuid4()
            generado_en = self._sesion.execute(
                SQL_EJECUCION,
                {
                    "id": ejecucion,
                    "periodo": periodo.inicio,
                    "origen": origen,
                    "solicitado_por": solicitado_por,
                },
            ).scalar_one()
            for i in indices:
                self._sesion.execute(
                    SQL_INDICE,
                    {
                        "periodo": periodo.inicio,
                        "ecosistema": i.ecosistema,
                        "hallazgos": i.hallazgos,
                        "especies_distintas": i.especies_distintas,
                        "promedio_previo": i.promedio_previo,
                        "indice": i.indice,
                        "nivel": i.nivel,
                        "ejecucion": ejecucion,
                    },
                )
            self._sesion.commit()
        except Exception:
            self._sesion.rollback()
            raise
        return ReporteMensual(periodo, origen, solicitado_por, generado_en, indices)

    def obtener(self, periodo: Periodo) -> ReporteMensual | None:
        ejecucion = self._sesion.execute(SQL_ULTIMA_EJECUCION, {"periodo": periodo.inicio}).first()
        if ejecucion is None:
            return None
        filas = self._sesion.execute(SQL_INDICES_DEL_MES, {"periodo": periodo.inicio}).all()
        indices = [
            IndiceEcosistema(
                f.ecosistema, f.hallazgos, f.especies_distintas, f.promedio_previo, f.indice, f.nivel
            )
            for f in filas
        ]
        return ReporteMensual(
            periodo, ejecucion.origen, ejecucion.solicitado_por, ejecucion.generado_en, indices
        )
