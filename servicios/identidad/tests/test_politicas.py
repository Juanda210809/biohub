import pytest

from app.dominio.politicas import PERMISOS, NivelUbicacion, decidir
from app.dominio.usuarios import Rol
from tests.conftest import nuevo_usuario

TODOS_LOS_ROLES = list(Rol)


@pytest.mark.parametrize("accion", sorted(PERMISOS))
@pytest.mark.parametrize("rol", TODOS_LOS_ROLES)
def test_solo_los_roles_de_la_tabla_reciben_permitir(accion, rol):
    decision = decidir(accion, nuevo_usuario(1, rol))
    assert decision.permitir is (rol in PERMISOS[accion])


def test_registrar_hallazgo_es_solo_para_investigador():
    assert PERMISOS["registrar_hallazgo"] == {Rol.INVESTIGADOR}


def test_coordenadas_exactas_solo_para_alto_rango():
    assert PERMISOS["ver_ubicacion"] == {Rol.ALTO_RANGO}


def test_un_usuario_sin_rol_no_puede_nada():
    for accion in PERMISOS:
        assert decidir(accion, nuevo_usuario(1, None)).permitir is False


def test_una_accion_desconocida_se_niega():
    decision = decidir("borrar_todo", nuevo_usuario(1, Rol.ADMINISTRADOR))
    assert decision.permitir is False
    assert "desconocida" in decision.motivo


def test_la_decision_incluye_el_id_y_el_rol():
    usuario = nuevo_usuario(0xAA, Rol.INVESTIGADOR)
    decision = decidir("registrar_hallazgo", usuario)
    assert (decision.usuario_id, decision.rol) == (usuario.id, Rol.INVESTIGADOR)


@pytest.mark.parametrize("rol", TODOS_LOS_ROLES)
def test_solo_alto_rango_tiene_nivel_exacto(rol):
    accion = next(a for a, roles in sorted(PERMISOS.items()) if rol in roles)
    decision = decidir(accion, nuevo_usuario(1, rol))
    esperado = NivelUbicacion.EXACTA if rol == Rol.ALTO_RANGO else NivelUbicacion.REGION
    assert decision.permitir is True
    assert decision.nivel_ubicacion == esperado
