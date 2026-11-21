"""Caso de uso de HU-15: índices de presión mensuales por ecosistema.

Fórmula (decisión del equipo, documentada en el README):
    índice = hallazgos del ecosistema en el mes ÷ promedio mensual de los 3 meses anteriores

- 1,00 es lo habitual; 1,50 es 50 % más actividad de lo normal; 0,50 la mitad.
- Sin hallazgos en los 3 meses anteriores no hay contra qué comparar: el índice queda vacío.
- Un ecosistema que tuvo actividad antes y ninguna este mes aparece con índice 0 (caída total).
- Los hallazgos sin ecosistema se agrupan como "Sin ecosistema".

No sabe nada de HTTP ni de SQL: recibe el repositorio por el constructor.
"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Protocol
from uuid import UUID

HORA_COLOMBIA = timezone(timedelta(hours=-5), "America/Bogota")
MESES_DE_REFERENCIA = 3
SIN_ECOSISTEMA = "Sin ecosistema"
# Niveles para leer el índice de un vistazo (decisión del equipo; se ajustan aquí).
UMBRAL_BAJA = Decimal("0.75")
UMBRAL_ALTA = Decimal("1.25")


class PeriodoInvalido(Exception):
    """El mes no tiene el formato AAAA-MM o todavía no ha empezado."""


class IndicesNoGenerados(Exception):
    """Ese mes todavía no tiene índices calculados."""


@dataclass(frozen=True)
class Periodo:
    """Un mes del calendario, guardado como su primer día."""

    inicio: date

    @classmethod
    def desde_texto(cls, texto: str) -> "Periodo":
        try:
            anio, mes = texto.split("-")
            if len(anio) != 4 or len(mes) != 2:
                raise ValueError
            return cls(date(int(anio), int(mes), 1))
        except ValueError:
            raise PeriodoInvalido(f"El mes debe tener el formato AAAA-MM: {texto!r}") from None

    @classmethod
    def anterior_a(cls, momento: datetime) -> "Periodo":
        """El mes que terminó justo antes de `momento`, en hora de Colombia."""
        hoy = momento.astimezone(HORA_COLOMBIA).date()
        return cls(hoy.replace(day=1)).desplazar(-1)

    def desplazar(self, meses: int) -> "Periodo":
        total = self.inicio.year * 12 + self.inicio.month - 1 + meses
        return Periodo(date(total // 12, total % 12 + 1, 1))

    @property
    def fin(self) -> date:
        return self.desplazar(1).inicio

    @property
    def texto(self) -> str:
        return self.inicio.strftime("%Y-%m")


@dataclass(frozen=True)
class Conteo:
    """Lo que el repositorio cuenta por ecosistema en un rango de fechas."""

    ecosistema: str
    hallazgos: int
    especies: int = 0


@dataclass(frozen=True)
class IndiceEcosistema:
    ecosistema: str
    hallazgos: int
    especies_distintas: int
    promedio_previo: Decimal
    indice: Decimal | None
    nivel: str  # SIN_HISTORIA, BAJA, NORMAL o ALTA


@dataclass(frozen=True)
class ReporteMensual:
    periodo: Periodo
    origen: str  # AUTOMATICO o MANUAL
    solicitado_por: UUID | None
    generado_en: datetime
    ecosistemas: list[IndiceEcosistema]


class RepositorioIndices(Protocol):
    def contar(self, desde: date, hasta: date) -> list[Conteo]: ...

    def guardar(
        self, periodo: Periodo, indices: list[IndiceEcosistema], origen: str, solicitado_por: UUID | None
    ) -> ReporteMensual: ...

    def obtener(self, periodo: Periodo) -> ReporteMensual | None: ...


def _redondear(valor: Decimal) -> Decimal:
    return valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def nivel_de(indice: Decimal | None) -> str:
    if indice is None:
        return "SIN_HISTORIA"
    if indice < UMBRAL_BAJA:
        return "BAJA"
    if indice > UMBRAL_ALTA:
        return "ALTA"
    return "NORMAL"


def calcular(mes: list[Conteo], previos: list[Conteo]) -> list[IndiceEcosistema]:
    """Une el mes con los 3 anteriores. Orden: índice de mayor a menor, los vacíos al final."""
    del_mes = {c.ecosistema: c for c in mes}
    total_previo = {c.ecosistema: c.hallazgos for c in previos}
    resultado = []
    for ecosistema in sorted(set(del_mes) | {e for e, n in total_previo.items() if n > 0}):
        actual = del_mes.get(ecosistema, Conteo(ecosistema, 0, 0))
        promedio = Decimal(total_previo.get(ecosistema, 0)) / MESES_DE_REFERENCIA
        indice = _redondear(Decimal(actual.hallazgos) / promedio) if promedio > 0 else None
        resultado.append(
            IndiceEcosistema(
                ecosistema=ecosistema,
                hallazgos=actual.hallazgos,
                especies_distintas=actual.especies,
                promedio_previo=_redondear(promedio),
                indice=indice,
                nivel=nivel_de(indice),
            )
        )
    return sorted(resultado, key=lambda i: (i.indice is None, -(i.indice or 0), i.ecosistema))


class ServicioIndices:
    def __init__(self, repositorio: RepositorioIndices) -> None:
        self._repositorio = repositorio

    def generar(
        self, periodo: Periodo, origen: str, solicitado_por: UUID | None, ahora: datetime
    ) -> ReporteMensual:
        """Calcula y guarda los índices del mes. Si ya existían, los reemplaza (se recalcula)."""
        mes_actual = Periodo.anterior_a(ahora).desplazar(1)
        if periodo.inicio > mes_actual.inicio:
            raise PeriodoInvalido("No se pueden generar índices de un mes que no ha empezado")
        mes = self._repositorio.contar(periodo.inicio, periodo.fin)
        previos = self._repositorio.contar(periodo.desplazar(-MESES_DE_REFERENCIA).inicio, periodo.inicio)
        return self._repositorio.guardar(periodo, calcular(mes, previos), origen, solicitado_por)

    def consultar(self, periodo: Periodo) -> ReporteMensual:
        reporte = self._repositorio.obtener(periodo)
        if reporte is None:
            raise IndicesNoGenerados
        return reporte

    def generar_mes_anterior_si_falta(self, ahora: datetime) -> ReporteMensual | None:
        """Lo que corre solo cada hora: si el mes que terminó no tiene índices, los genera."""
        periodo = Periodo.anterior_a(ahora)
        if self._repositorio.obtener(periodo) is not None:
            return None
        return self.generar(periodo, "AUTOMATICO", None, ahora)
