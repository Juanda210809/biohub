from uuid import UUID

import pytest

from app.dominio.autenticacion import CredencialesInvalidas
from app.dominio.contrasenas import verificar
from app.dominio.cuentas import (
    CorreoYaRegistrado,
    NoPuedeDesactivarseASiMismo,
    NoPuedeQuitarseAdministrador,
    UsuarioNoExiste,
)
from app.dominio.usuarios import Rol
from tests.conftest import CONTRASENA, INVESTIGADOR_ID


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


# --- HU-18: crear, modificar, desactivar ---------------------------------------------------------
def test_crea_una_cuenta_activa_y_sin_rol(cuentas, repositorio):
    usuario = cuentas.crear("Ana Pérez", "Ana@BioHub.local ", "Clave-Nueva-1")

    assert usuario.correo == "ana@biohub.local"
    assert usuario.rol is None
    assert usuario.activo is True
    assert repositorio.obtener(usuario.id) == usuario


def test_la_contrasena_se_guarda_como_hash(cuentas):
    usuario = cuentas.crear("Ana", "ana@biohub.local", "Clave-Nueva-1")

    assert usuario.hash_contrasena != "Clave-Nueva-1"
    assert verificar("Clave-Nueva-1", usuario.hash_contrasena)


def test_no_crea_dos_cuentas_con_el_mismo_correo(cuentas):
    with pytest.raises(CorreoYaRegistrado):
        cuentas.crear("Otro", "INVESTIGADOR@biohub.local", "Clave-Nueva-1")


def test_la_cuenta_nueva_puede_iniciar_sesion(cuentas, autenticacion):
    cuentas.crear("Ana", "ana@biohub.local", "Clave-Nueva-1")

    assert autenticacion.iniciar_sesion("ana@biohub.local", "Clave-Nueva-1").usuario.correo == (
        "ana@biohub.local"
    )


def test_modifica_solo_los_datos_que_llegan(cuentas, repositorio):
    antes = repositorio.obtener(INVESTIGADOR_ID)

    despues = cuentas.modificar(INVESTIGADOR_ID, nombre="Nuevo Nombre")

    assert despues.nombre == "Nuevo Nombre"
    assert (despues.correo, despues.hash_contrasena, despues.rol) == (
        antes.correo,
        antes.hash_contrasena,
        antes.rol,
    )


def test_cambiar_la_contrasena_cambia_con_cual_se_entra(cuentas, autenticacion):
    cuentas.modificar(INVESTIGADOR_ID, contrasena="Otra-Clave-9")

    with pytest.raises(CredencialesInvalidas):
        autenticacion.iniciar_sesion("investigador@biohub.local", CONTRASENA)
    assert autenticacion.iniciar_sesion("investigador@biohub.local", "Otra-Clave-9")


def test_no_puede_usar_el_correo_de_otra_cuenta(cuentas):
    with pytest.raises(CorreoYaRegistrado):
        cuentas.modificar(INVESTIGADOR_ID, correo="auditor@biohub.local")


def test_puede_dejar_su_mismo_correo(cuentas):
    assert cuentas.modificar(INVESTIGADOR_ID, correo="Investigador@biohub.local").correo == (
        "investigador@biohub.local"
    )


def test_modificar_un_usuario_que_no_existe(cuentas):
    with pytest.raises(UsuarioNoExiste):
        cuentas.modificar(UUID("00000000-0000-0000-0000-000000000099"), nombre="X")


def test_una_cuenta_desactivada_no_puede_iniciar_sesion(cuentas, repositorio, autenticacion):
    cuentas.desactivar(INVESTIGADOR_ID, repositorio.por_rol(Rol.ADMINISTRADOR))

    with pytest.raises(CredencialesInvalidas):
        autenticacion.iniciar_sesion("investigador@biohub.local", CONTRASENA)


def test_desactivar_no_borra_la_cuenta_ni_su_rol(cuentas, repositorio):
    cuentas.desactivar(INVESTIGADOR_ID, repositorio.por_rol(Rol.ADMINISTRADOR))

    usuario = repositorio.obtener(INVESTIGADOR_ID)
    assert usuario is not None
    assert usuario.activo is False
    assert usuario.rol == Rol.INVESTIGADOR
    assert len(cuentas.listar()) == 6


def test_activar_devuelve_el_acceso(cuentas, repositorio, autenticacion):
    cuentas.desactivar(INVESTIGADOR_ID, repositorio.por_rol(Rol.ADMINISTRADOR))

    cuentas.activar(INVESTIGADOR_ID)

    assert autenticacion.iniciar_sesion("investigador@biohub.local", CONTRASENA)


def test_un_administrador_no_puede_desactivarse_a_si_mismo(cuentas, repositorio):
    admin = repositorio.por_rol(Rol.ADMINISTRADOR)

    with pytest.raises(NoPuedeDesactivarseASiMismo):
        cuentas.desactivar(admin.id, admin)
    assert repositorio.obtener(admin.id).activo is True
