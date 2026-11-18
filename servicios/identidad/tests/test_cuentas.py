from uuid import UUID

import pytest

from app.dominio.cuentas import NoPuedeQuitarseAdministrador, UsuarioNoExiste
from app.dominio.usuarios import Rol


def test_asigna_un_rol_y_deja_el_cambio_registrado(cuentas, repositorio):
    admin = repositorio.por_rol(Rol.ADMINISTRADOR)
    investigador = repositorio.por_rol(Rol.INVESTIGADOR)

    actualizado = cuentas.asignar_rol(investigador.id, Rol.AUDITOR, admin)

    assert actualizado.rol == Rol.AUDITOR
    assert repositorio.cambios_rol == [(investigador.id, Rol.INVESTIGADOR, Rol.AUDITOR, admin.id)]


def test_puede_quitar_el_rol(cuentas, repositorio):
    admin = repositorio.por_rol(Rol.ADMINISTRADOR)
    auditor = repositorio.por_rol(Rol.AUDITOR)

    assert cuentas.asignar_rol(auditor.id, None, admin).rol is None


def test_asignar_el_mismo_rol_no_registra_un_cambio(cuentas, repositorio):
    admin = repositorio.por_rol(Rol.ADMINISTRADOR)
    auditor = repositorio.por_rol(Rol.AUDITOR)

    cuentas.asignar_rol(auditor.id, Rol.AUDITOR, admin)

    assert repositorio.cambios_rol == []


def test_usuario_que_no_existe(cuentas, repositorio):
    admin = repositorio.por_rol(Rol.ADMINISTRADOR)

    with pytest.raises(UsuarioNoExiste):
        cuentas.asignar_rol(UUID("00000000-0000-0000-0000-000000000099"), Rol.AUDITOR, admin)


@pytest.mark.parametrize("rol", [Rol.AUDITOR, None])
def test_un_administrador_no_puede_quitarse_su_propio_rol(cuentas, repositorio, rol):
    admin = repositorio.por_rol(Rol.ADMINISTRADOR)

    with pytest.raises(NoPuedeQuitarseAdministrador):
        cuentas.asignar_rol(admin.id, rol, admin)
    assert repositorio.cambios_rol == []


def test_lista_todas_las_cuentas(cuentas):
    assert len(cuentas.listar()) == 6
