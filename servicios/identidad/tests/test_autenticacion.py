from dataclasses import replace

import pytest

from app.dominio.autenticacion import CredencialesInvalidas
from app.dominio.tokens import TokenInvalido
from app.dominio.usuarios import Rol
from tests.conftest import CONTRASENA, INVESTIGADOR_ID


def test_con_credenciales_validas_inicia_sesion(autenticacion, tokens):
    sesion = autenticacion.iniciar_sesion("investigador@biohub.local", CONTRASENA)

    assert sesion.usuario.id == INVESTIGADOR_ID
    assert tokens.leer(sesion.token).usuario_id == INVESTIGADOR_ID


def test_el_correo_no_distingue_mayusculas_ni_espacios(autenticacion):
    sesion = autenticacion.iniciar_sesion("  Investigador@BioHub.local ", CONTRASENA)
    assert sesion.usuario.id == INVESTIGADOR_ID


@pytest.mark.parametrize(
    ("correo", "contrasena"),
    [
        ("investigador@biohub.local", "clave-equivocada"),
        ("nadie@biohub.local", CONTRASENA),
    ],
)
def test_credenciales_invalidas_dan_el_mismo_error(autenticacion, correo, contrasena):
    with pytest.raises(CredencialesInvalidas):
        autenticacion.iniciar_sesion(correo, contrasena)


def test_una_cuenta_desactivada_no_inicia_sesion(autenticacion, repositorio):
    repositorio.reemplazar(replace(repositorio.por_rol(Rol.INVESTIGADOR), activo=False))

    with pytest.raises(CredencialesInvalidas):
        autenticacion.iniciar_sesion("investigador@biohub.local", CONTRASENA)


def test_usuario_de_sesion_devuelve_al_dueno_del_token(autenticacion, token_de):
    assert autenticacion.usuario_de_sesion(token_de(Rol.AUDITOR)).rol == Rol.AUDITOR


def test_despues_de_cerrar_sesion_el_token_ya_no_sirve(autenticacion, token_de):
    token = token_de(Rol.INVESTIGADOR)

    autenticacion.cerrar_sesion(token)

    with pytest.raises(TokenInvalido):
        autenticacion.usuario_de_sesion(token)


def test_cerrar_sesion_solo_cierra_ese_token(autenticacion, token_de):
    primero = token_de(Rol.INVESTIGADOR)
    segundo = token_de(Rol.INVESTIGADOR)

    autenticacion.cerrar_sesion(primero)

    assert autenticacion.usuario_de_sesion(segundo).rol == Rol.INVESTIGADOR
