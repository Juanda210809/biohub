"""Formas de las respuestas de la API de Reportes (JSON en camelCase)."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.dominio.indices import ReporteMensual


class EsquemaBase(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class IndiceSalida(EsquemaBase):
    ecosistema: str
    hallazgos: int
    especies_distintas: int
    promedio_previo: float
    indice: float | None
    nivel: str


class ReporteSalida(EsquemaBase):
    periodo: str
    origen: str
    solicitado_por: UUID | None
    generado_en: datetime
    ecosistemas: list[IndiceSalida]

    @classmethod
    def desde(cls, r: ReporteMensual) -> "ReporteSalida":
        def numero(valor: Decimal | None) -> float | None:
            return None if valor is None else float(valor)

        return cls(
            periodo=r.periodo.texto,
            origen=r.origen,
            solicitado_por=r.solicitado_por,
            generado_en=r.generado_en,
            ecosistemas=[
                IndiceSalida(
                    ecosistema=i.ecosistema,
                    hallazgos=i.hallazgos,
                    especies_distintas=i.especies_distintas,
                    promedio_previo=float(i.promedio_previo),
                    indice=numero(i.indice),
                    nivel=i.nivel,
                )
                for i in r.ecosistemas
            ],
        )
