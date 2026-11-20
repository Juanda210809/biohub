"""Pruebas de integración de HU-15 contra un PostgreSQL real (ver tests/bd_real.py)."""
import threading
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.dominio.indices import Periodo, ServicioIndices
from app.main import generar_si_falta
from app.repositorio.indices import RepositorioIndicesSql
from tests.conftest import ALTO_RANGO_ID

AHORA = datetime(2026, 11, 20, 17, 0, tzinfo=UTC)

# (fecha, ecosistema, especie) en la copia de hallazgo_publico
DATOS = [
    # Jul-sep: 6 en bosque húmedo (promedio 2 al mes), 3 en manglar (promedio 1)
    *[(date(2026, m, 10), "Bosque húmedo", "Phyllobates terribilis") for m in (7, 8, 9) for _ in range(2)],
    *[(date(2026, m, 3), "Manglar", "Setophaga cerulea") for m in (7, 8, 9)],
    # Octubre: 5 en bosque húmedo con 2 especies, ninguno en manglar, 1 en páramo y 1 sin ecosistema
    *[(date(2026, 10, d), "Bosque húmedo", "Phyllobates terribilis") for d in (1, 5, 9)],
    *[(date(2026, 10, d), "Bosque húmedo", "Thraupis episcopus") for d in (15, 31)],
    (date(2026, 10, 12), "Páramo", "Thraupis episcopus"),
    (date(2026, 10, 20), None, "Thraupis episcopus"),
    # Fuera de rango: no deben contar para octubre
    (date(2026, 6, 30), "Bosque húmedo", "X"),
    (date(2026, 11, 1), "Bosque húmedo", "X"),
]


@pytest.fixture(scope="module")
def con_datos(bd):
    admin, reportes = bd
    with admin.begin() as c:
        c.execute(text("TRUNCATE campo.hallazgo_publico"))
        for fecha, ecosistema, especie in DATOS:
            c.execute(
                text(
                    "INSERT INTO campo.hallazgo_publico (hallazgo_id, especie, ecosistema, fecha_hallazgo) "
                    "VALUES (:id, :especie, :eco, :fecha)"
                ),
                {"id": uuid.uuid4(), "especie": especie, "eco": ecosistema, "fecha": fecha},
            )
    return admin, reportes


def _servicio(reportes):
    return ServicioIndices(RepositorioIndicesSql(sessionmaker(bind=reportes)()))


def test_calcula_los_indices_de_octubre_con_los_datos_reales(con_datos):
    _, reportes = con_datos

    reporte = _servicio(reportes).generar(Periodo.desde_texto("2026-10"), "MANUAL", ALTO_RANGO_ID, AHORA)

    filas = {
        i.ecosistema: (i.hallazgos, i.especies_distintas, i.indice, i.nivel) for i in reporte.ecosistemas
    }
    assert filas == {
        "Bosque húmedo": (5, 2, Decimal("2.50"), "ALTA"),
        "Manglar": (0, 0, Decimal("0.00"), "BAJA"),
        "Páramo": (1, 1, None, "SIN_HISTORIA"),
        "Sin ecosistema": (1, 1, None, "SIN_HISTORIA"),
    }


def test_lo_guardado_se_puede_consultar_despues(con_datos):
    _, reportes = con_datos
    _servicio(reportes).generar(Periodo.desde_texto("2026-10"), "MANUAL", ALTO_RANGO_ID, AHORA)

    reporte = _servicio(reportes).consultar(Periodo.desde_texto("2026-10"))

    assert reporte.origen == "MANUAL"
    assert reporte.solicitado_por == ALTO_RANGO_ID
    orden = [i.ecosistema for i in reporte.ecosistemas]
    assert orden == ["Bosque húmedo", "Manglar", "Páramo", "Sin ecosistema"]


def test_recalcular_reemplaza_sin_duplicar_y_deja_registro(con_datos):
    admin, reportes = con_datos
    for _ in range(3):
        _servicio(reportes).generar(Periodo.desde_texto("2026-09"), "MANUAL", ALTO_RANGO_ID, AHORA)

    with admin.connect() as c:
        filas = c.execute(
            text("SELECT count(*) FROM reportes.indice_presion WHERE periodo = '2026-09-01'")
        ).scalar()
        ejecuciones = c.execute(
            text("SELECT count(*) FROM reportes.ejecucion_indices WHERE periodo = '2026-09-01'")
        ).scalar()
    assert filas == 2  # bosque húmedo y manglar, una vez cada uno
    assert ejecuciones == 3


def test_la_generacion_automatica_hace_el_mes_anterior_una_sola_vez(con_datos, monkeypatch):
    admin, reportes = con_datos
    monkeypatch.setattr("app.main.motor", lambda: reportes)
    with admin.begin() as c:
        c.execute(text("DELETE FROM reportes.indice_presion WHERE periodo = '2026-10-01'"))
        c.execute(text("DELETE FROM reportes.ejecucion_indices WHERE periodo = '2026-10-01'"))

    primero = generar_si_falta(AHORA)
    segundo = generar_si_falta(AHORA)

    assert primero.periodo.texto == "2026-10"
    assert primero.origen == "AUTOMATICO"
    assert segundo is None


def test_dos_generaciones_del_mismo_mes_a_la_vez_no_chocan(con_datos):
    _, reportes = con_datos
    errores = []

    def generar():
        try:
            _servicio(reportes).generar(Periodo.desde_texto("2026-08"), "MANUAL", ALTO_RANGO_ID, AHORA)
        except Exception as error:  # noqa: BLE001 - se muestra en el assert de abajo
            errores.append(repr(error))

    hilos = [threading.Thread(target=generar) for _ in range(4)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join(timeout=30)

    assert errores == []
    reporte = _servicio(reportes).consultar(Periodo.desde_texto("2026-08"))
    assert sorted(i.ecosistema for i in reporte.ecosistemas) == ["Bosque húmedo", "Manglar"]


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO campo.hallazgo_publico (hallazgo_id, especie) VALUES (gen_random_uuid(), 'x')",
        "UPDATE campo.hallazgo_publico SET especie = 'x'",
        "DELETE FROM campo.hallazgo_publico",
    ],
    ids=["agregar", "cambiar", "borrar"],
)
def test_reportes_solo_lee_la_copia_de_hallazgos(con_datos, sql):
    _, reportes = con_datos

    with pytest.raises(Exception, match="permission denied"), reportes.begin() as c:
        c.execute(text(sql))
