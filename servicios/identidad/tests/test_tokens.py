from datetime import UTC, datetime, timedelta

import pytest

from app.dominio.tokens import ServicioTokens, TokenInvalido, TokensNoConfigurados
from tests.conftest import SECRETO


def test_emite_y_lee_un_token(tokens, repositorio):
    usuario = repositorio.por_rol(None)
    emitido = tokens.emitir(usuario)

    datos = tokens.leer(emitido.token)

    assert datos.usuario_id == usuario.id
    assert datos.jti == emitido.jti


def test_cada_token_tiene_su_propio_jti(tokens, repositorio):
    usuario = repositorio.por_rol(None)
    assert tokens.emitir(usuario).jti != tokens.emitir(usuario).jti


def test_rechaza_un_token_alterado(tokens, repositorio):
    token = tokens.emitir(repositorio.por_rol(None)).token
    alterado = token[:-2] + ("AA" if not token.endswith("AA") else "BB")

    with pytest.raises(TokenInvalido):
        tokens.leer(alterado)


def test_rechaza_un_token_firmado_con_otra_clave(repositorio):
    ajeno = ServicioTokens("otra-clave-distinta-de-la-del-servicio").emitir(repositorio.por_rol(None))

    with pytest.raises(TokenInvalido):
        ServicioTokens(SECRETO).leer(ajeno.token)


def test_rechaza_un_token_vencido(repositorio):
    hace_dos_horas = datetime.now(UTC) - timedelta(hours=2)
    vencido = ServicioTokens(SECRETO, minutos=60, reloj=lambda: hace_dos_horas).emitir(
        repositorio.por_rol(None)
    )

    with pytest.raises(TokenInvalido):
        ServicioTokens(SECRETO).leer(vencido.token)


@pytest.mark.parametrize("token", ["", None, "no-es-un-jwt", "a.b.c"])
def test_rechaza_basura(tokens, token):
    with pytest.raises(TokenInvalido):
        tokens.leer(token)


def test_sin_clave_no_emite_ni_acepta_tokens(tokens, repositorio):
    sin_clave = ServicioTokens("")
    token = tokens.emitir(repositorio.por_rol(None)).token

    with pytest.raises(TokensNoConfigurados):
        sin_clave.emitir(repositorio.por_rol(None))
    with pytest.raises(TokenInvalido):
        sin_clave.leer(token)
