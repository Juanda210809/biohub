"""Pruebas de integración de HU-08 contra un PostgreSQL real (ver tests/bd_real.py).

Prueban los permisos de verdad, la transacción completa y dos reclasificaciones al mismo tiempo.
"""
import threading
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.dominio.reclasificacion import EspecieNoExiste, MismaEspecie, ServicioReclasificacion
from app.repositorio.hallazgos import RepositorioGobernanza
from tests.bd_real import AZULEJO, CERULEA, CIENTIFICO, RANA, registrar_hallazgo


def _servicio(gobernanza):
    """Un servicio con su propia sesión, como en cada petición HTTP."""
    return ServicioReclasificacion(RepositorioGobernanza(sessionmaker(bind=gobernanza)()))


def test_reclasifica_y_conserva_el_historial(bd):
    registro, gobernanza = bd
    hallazgo = registrar_hallazgo(registro)

    resultado = _servicio(gobernanza).reclasificar(hallazgo, AZULEJO, "Análisis genético", CIENTIFICO)

    assert (resultado.version, resultado.especie_anterior, resultado.especie_nueva) == (
        2, "Setophaga cerulea", "Thraupis episcopus"
    )
    with gobernanza.connect() as c:
        historial = c.execute(
            text(
                "SELECT numero, especie, justificacion, atributos, autor_id "
                "FROM gobernanza.hallazgo_version WHERE hallazgo_id = :h ORDER BY numero"
            ),
            {"h": hallazgo},
        ).all()
        actual = c.execute(
            text("SELECT especie_id, version_actual FROM campo.hallazgo WHERE id = :h"), {"h": hallazgo}
        ).one()
        publico = c.execute(
            text("SELECT especie, version, atributos_publicos FROM campo.hallazgo_publico "
                 "WHERE hallazgo_id = :h"),
            {"h": hallazgo},
        ).one()
    assert [(v.numero, v.especie) for v in historial] == [(1, "Setophaga cerulea"), (2, "Thraupis episcopus")]
    assert historial[1].atributos == {"altitudMsnm": 1200}  # conserva lo medido en campo
    assert historial[1].autor_id == CIENTIFICO
    assert tuple(actual) == (AZULEJO, 2)
    assert tuple(publico) == ("Thraupis episcopus", 2, {"altitudMsnm": 1200})
    with registro.connect() as c:
        auditoria = c.execute(
            text("SELECT accion, actor_id FROM campo.auditoria WHERE recurso_id = :h"), {"h": hallazgo}
        ).all()
    assert [tuple(a) for a in auditoria] == [("reclasificar", CIENTIFICO)]


def test_un_rechazo_no_deja_el_hallazgo_bloqueado(bd):
    registro, gobernanza = bd
    hallazgo = registrar_hallazgo(registro)

    with pytest.raises(MismaEspecie):
        _servicio(gobernanza).reclasificar(hallazgo, CERULEA, "Misma", CIENTIFICO)
    with pytest.raises(EspecieNoExiste):
        _servicio(gobernanza).reclasificar(hallazgo, uuid.uuid4(), "No existe", CIENTIFICO)

    # Si el rechazo hubiera dejado el bloqueo, esto se quedaría esperando.
    with gobernanza.connect() as c:
        c.execute(text("SET lock_timeout = '3s'"))
        c.execute(text("SELECT 1 FROM campo.hallazgo WHERE id = :h FOR UPDATE"), {"h": hallazgo})


def test_dos_reclasificaciones_a_la_vez_no_repiten_version(bd):
    registro, gobernanza = bd
    hallazgo = registrar_hallazgo(registro)
    versiones, errores = [], []

    def reclasificar(especie):
        try:
            resultado = _servicio(gobernanza).reclasificar(hallazgo, especie, "Concurrente", CIENTIFICO)
            versiones.append(resultado.version)
        except Exception as error:  # noqa: BLE001 - se muestra en el assert de abajo
            errores.append(repr(error))

    hilos = [threading.Thread(target=reclasificar, args=(e,)) for e in (AZULEJO, RANA)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join(timeout=30)

    assert errores == []
    assert sorted(versiones) == [2, 3]
    with gobernanza.connect() as c:
        numeros = c.execute(
            text("SELECT numero FROM gobernanza.hallazgo_version WHERE hallazgo_id = :h ORDER BY numero"),
            {"h": hallazgo},
        ).scalars().all()
    assert numeros == [1, 2, 3]


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE campo.hallazgo SET region = 'Otra' WHERE id = :h",
        "SELECT * FROM campo.ubicacion WHERE hallazgo_id = :h",
        "INSERT INTO campo.especie (id, tipo_especie_id, nombre_cientifico) "
        "VALUES (gen_random_uuid(), '10000000-0000-0000-0000-000000000001', 'Falsa ' || :h)",
        "DELETE FROM gobernanza.hallazgo_version WHERE hallazgo_id = :h",
        "UPDATE gobernanza.hallazgo_version SET especie = 'Otra' WHERE hallazgo_id = :h",
    ],
    ids=["cambiar_region", "ver_coordenadas", "crear_especie", "borrar_historial", "cambiar_historial"],
)
def test_gobernanza_no_puede_lo_que_no_le_toca(bd, sql):
    registro, gobernanza = bd
    hallazgo = registrar_hallazgo(registro)

    with pytest.raises(Exception, match="permission denied"), gobernanza.begin() as c:
        c.execute(text(sql), {"h": str(hallazgo)})


def test_el_que_espera_el_bloqueo_ve_la_especie_nueva(bd):
    """Reproduce siempre la carrera: otro cambia la especie mientras esta reclasificación espera."""
    registro, gobernanza = bd
    hallazgo = registrar_hallazgo(registro)
    resultado, errores = [], []

    with gobernanza.connect() as otro:
        transaccion = otro.begin()
        otro.execute(
            text("UPDATE campo.hallazgo SET especie_id = :e, version_actual = 2 WHERE id = :h"),
            {"e": AZULEJO, "h": hallazgo},
        )
        otro.execute(
            text(
                "INSERT INTO gobernanza.hallazgo_version "
                "(id, hallazgo_id, numero, especie, atributos, autor_id, justificacion) "
                "VALUES (:id, :h, 2, 'Thraupis episcopus', '{}'::jsonb, :a, 'Primero')"
            ),
            {"id": uuid.uuid4(), "h": hallazgo, "a": CIENTIFICO},
        )

        def esperar_y_reclasificar():
            try:
                resultado.append(_servicio(gobernanza).reclasificar(hallazgo, RANA, "Segundo", CIENTIFICO))
            except Exception as error:  # noqa: BLE001 - se muestra en el assert de abajo
                errores.append(repr(error))

        hilo = threading.Thread(target=esperar_y_reclasificar)
        hilo.start()
        hilo.join(timeout=1)
        assert hilo.is_alive(), "debería estar esperando el bloqueo del hallazgo"
        transaccion.commit()
        hilo.join(timeout=10)

    assert errores == []
    assert resultado[0].version == 3
    assert resultado[0].especie_anterior == "Thraupis episcopus"
