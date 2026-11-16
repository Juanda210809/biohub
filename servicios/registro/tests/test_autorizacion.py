from uuid import UUID

import httpx
import pytest

from app.autorizacion import autorizar

USUARIO_ID = "00000000-0000-0000-0000-0000000000aa"
PDP = "app.autorizacion.httpx.post"


def pdp_responde(monkeypatch, respuesta):
    """Reemplaza la llamada HTTP al PDP y guarda lo que se le envió."""
    enviado = {}

    def falso(url, **kwargs):
        enviado.update(url=url, **kwargs)
        return respuesta

    monkeypatch.setattr(PDP, falso)
    return enviado


def pdp_falla(monkeypatch, error):
    def falso(url, **kwargs):
        raise error

    monkeypatch.setattr(PDP, falso)


def test_permitir_con_usuario_id(monkeypatch):
    pdp_responde(
        monkeypatch,
        httpx.Response(
            200,
            json={
                "decision": "PERMITIR",
                "motivo": "ok",
                "usuarioId": USUARIO_ID,
                "rol": "INVESTIGADOR",
                "nivelUbicacion": "REGION",
            },
        ),
    )

    decision = autorizar("token", "registrar_hallazgo")

    assert decision.permitido is True
    assert decision.usuario_id == UUID(USUARIO_ID)
    assert decision.rol == "INVESTIGADOR"


def test_envia_token_accion_y_recurso_al_pdp(monkeypatch):
    enviado = pdp_responde(monkeypatch, httpx.Response(200, json={"decision": "DENEGAR"}))

    autorizar("mi-token", "registrar_hallazgo", "recurso-1")

    assert enviado["url"].endswith("/interno/autorizar")
    assert enviado["json"] == {"token": "mi-token", "accion": "registrar_hallazgo", "recurso": "recurso-1"}
    assert enviado["timeout"] == 2.0


def test_denegar(monkeypatch):
    pdp_responde(monkeypatch, httpx.Response(200, json={"decision": "DENEGAR", "motivo": "rol no permitido"}))

    decision = autorizar("token", "registrar_hallazgo")

    assert decision.permitido is False
    assert decision.motivo == "rol no permitido"


@pytest.mark.parametrize(
    "respuesta",
    [
        httpx.Response(200, json={"decision": "PERMITIR", "motivo": "ok"}),  # sin usuarioId
        httpx.Response(200, json={"decision": "PERMITIR", "usuarioId": None}),
        httpx.Response(200, json={"decision": "PERMITIR", "usuarioId": "no-es-un-uuid"}),
        httpx.Response(500, json={"decision": "PERMITIR", "usuarioId": USUARIO_ID}),
        httpx.Response(200, text="<html>no es json</html>"),
        httpx.Response(200, json=["no", "es", "un", "objeto"]),
    ],
    ids=["sin-usuario-id", "usuario-id-nulo", "usuario-id-invalido", "estado-500", "no-json", "lista"],
)
def test_respuestas_raras_se_niegan(monkeypatch, respuesta):
    pdp_responde(monkeypatch, respuesta)

    decision = autorizar("token", "registrar_hallazgo")

    assert decision.permitido is False
    assert decision.usuario_id is None


@pytest.mark.parametrize(
    "error",
    [httpx.ConnectError("sin red"), httpx.ReadTimeout("tardó más de 2 s")],
    ids=["error-de-red", "tiempo-agotado"],
)
def test_si_el_pdp_no_responde_se_niega(monkeypatch, error):
    pdp_falla(monkeypatch, error)

    assert autorizar("token", "registrar_hallazgo").permitido is False
