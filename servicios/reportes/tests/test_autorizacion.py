"""El cliente del PDP niega ante cualquier duda (falla segura)."""
from uuid import UUID

import httpx

from app import autorizacion


class _Respuesta:
    def __init__(self, estado, datos):
        self.status_code = estado
        self._datos = datos

    def json(self):
        return self._datos


def _con_respuesta(monkeypatch, estado, datos):
    monkeypatch.setattr(autorizacion.httpx, "post", lambda *a, **k: _Respuesta(estado, datos))


def test_permite_y_devuelve_el_usuario(monkeypatch):
    usuario = "00000000-0000-0000-0000-0000000000ab"
    _con_respuesta(monkeypatch, 200, {"decision": "PERMITIR", "usuarioId": usuario, "rol": "X"})

    decision = autorizacion.autorizar("t", "generar_reporte", "h")

    assert decision.permitido
    assert decision.usuario_id == UUID(usuario)


def test_niega_si_el_pdp_niega(monkeypatch):
    _con_respuesta(monkeypatch, 200, {"decision": "DENEGAR", "motivo": "no"})

    assert not autorizacion.autorizar("t", "generar_reporte").permitido


def test_niega_si_permite_sin_decir_el_usuario(monkeypatch):
    _con_respuesta(monkeypatch, 200, {"decision": "PERMITIR"})

    assert not autorizacion.autorizar("t", "generar_reporte").permitido


def test_niega_si_el_pdp_no_responde(monkeypatch):
    def caido(*a, **k):
        raise httpx.ConnectError("caido")

    monkeypatch.setattr(autorizacion.httpx, "post", caido)

    assert not autorizacion.autorizar("t", "generar_reporte").permitido
