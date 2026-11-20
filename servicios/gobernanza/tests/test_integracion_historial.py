"""Pruebas de integración de HU-12 contra un PostgreSQL real (ver tests/bd_real.py).

Guardan versiones con fechas distintas (como si se hubieran reclasificado en enero, junio y
noviembre) y reconstruyen el hallazgo en varias fechas, igual que lo haría un auditor.
"""
import time
import uuid
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.dominio.historial import ServicioHistorial, SinVersionEnFecha
from app.repositorio.hallazgos import RepositorioGobernanza
from tests.bd_real import CIENTIFICO, INVESTIGADOR

SQL_VERSION = text(
    "INSERT INTO gobernanza.hallazgo_version "
    "(id, hallazgo_id, numero, especie, atributos, autor_id, justificacion, vigente_desde) "
    "VALUES (:id, :h, :n, :especie, CAST(:atributos AS jsonb), :autor, :justificacion, :desde)"
)

HISTORIA = [
    (1, "Setophaga cerulea", '{"altitudMsnm": 1200}', INVESTIGADOR, "Registro inicial",
     datetime(2026, 1, 10, 14, 0, tzinfo=UTC)),
    (2, "Thraupis episcopus", '{"altitudMsnm": 1200}', CIENTIFICO, "Análisis genético",
     datetime(2026, 6, 1, 15, 0, tzinfo=UTC)),
    # 03:30 UTC del 2 de noviembre = 10:30 p. m. del 1 de noviembre en Colombia
    (3, "Phyllobates terribilis", '{"altitudMsnm": 900}', CIENTIFICO, "Revisión del museo",
     datetime(2026, 11, 2, 3, 30, tzinfo=UTC)),
]


def _historia(gobernanza, filas=HISTORIA) -> uuid.UUID:
    hallazgo = uuid.uuid4()
    with gobernanza.begin() as c:
        for numero, especie, atributos, autor, justificacion, desde in filas:
            c.execute(
                SQL_VERSION,
                {
                    "id": uuid.uuid4(), "h": hallazgo, "n": numero, "especie": especie,
                    "atributos": atributos, "autor": autor, "justificacion": justificacion,
                    "desde": desde,
                },
            )
    return hallazgo


def _servicio(gobernanza):
    return ServicioHistorial(RepositorioGobernanza(sessionmaker(bind=gobernanza)()))


@pytest.mark.parametrize(
    ("fecha", "version_esperada"),
    [
        (date(2026, 1, 10), 1),   # el mismo día del registro
        (date(2026, 3, 15), 1),
        (date(2026, 6, 1), 2),    # el día de la reclasificación ya cuenta
        (date(2026, 10, 31), 2),
        (date(2026, 11, 1), 3),   # 10:30 p. m. en Colombia: todavía es 1 de noviembre
        (date(2027, 1, 1), 3),
    ],
)
def test_reconstruye_la_version_vigente_en_cada_fecha(bd, fecha, version_esperada):
    _, gobernanza = bd
    hallazgo = _historia(gobernanza)

    reconstruccion = _servicio(gobernanza).reconstruir(hallazgo, fecha)

    assert reconstruccion.en_fecha.numero == version_esperada
    assert reconstruccion.actual.numero == 3


def test_muestra_autor_justificacion_y_lo_que_cambio_hasta_hoy(bd):
    _, gobernanza = bd
    hallazgo = _historia(gobernanza)

    r = _servicio(gobernanza).reconstruir(hallazgo, date(2026, 3, 15))

    assert (r.en_fecha.especie, r.en_fecha.autor_id, r.en_fecha.justificacion) == (
        "Setophaga cerulea", INVESTIGADOR, "Registro inicial"
    )
    assert r.versiones_posteriores == 2
    assert [(c.campo, c.antes, c.ahora) for c in r.cambios] == [
        ("especie", "Setophaga cerulea", "Phyllobates terribilis"),
        ("atributos.altitudMsnm", 1200, 900),
    ]


def test_antes_del_registro_avisa_desde_cuando_existe(bd):
    _, gobernanza = bd
    hallazgo = _historia(gobernanza)

    with pytest.raises(SinVersionEnFecha) as error:
        _servicio(gobernanza).reconstruir(hallazgo, date(2026, 1, 9))

    assert error.value.primera_version == HISTORIA[0][5]


def test_responde_en_menos_de_5_segundos_con_mucho_historial(bd):
    """Criterio de HU-12: la reconstrucción tarda menos de 5 segundos."""
    _, gobernanza = bd
    # Ruido: 300 hallazgos más con 20 versiones cada uno (6000 filas).
    with gobernanza.begin() as c:
        c.execute(
            text(
                "INSERT INTO gobernanza.hallazgo_version "
                "(id, hallazgo_id, numero, especie, atributos, autor_id, justificacion, vigente_desde) "
                "SELECT gen_random_uuid(), h.id, n, 'Especie ' || n, '{}'::jsonb, :autor, 'Carga', "
                "       timestamptz '2026-01-01' + n * interval '1 day' "
                "FROM (SELECT gen_random_uuid() AS id FROM generate_series(1, 300)) h, "
                "     generate_series(1, 20) n"
            ),
            {"autor": CIENTIFICO},
        )
    hallazgo = _historia(gobernanza)

    inicio = time.perf_counter()
    for _ in range(20):
        _servicio(gobernanza).reconstruir(hallazgo, date(2026, 7, 1))
    promedio = (time.perf_counter() - inicio) / 20

    assert promedio < 5
    assert promedio < 0.5  # margen amplio: con el índice debería tardar milisegundos
