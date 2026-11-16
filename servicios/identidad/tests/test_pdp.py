from dataclasses import replace

import pytest

from app.dominio.usuarios import Rol
from tests.conftest import INVESTIGADOR_ID


def preguntar(cliente, accion, token=None, recurso=None):
    respuesta = cliente.post(
        "/interno/autorizar", json={"token": token, "accion": accion, "recurso": recurso}
    )
    assert respuesta.status_code == 200
    return respuesta.json()


def test_investigador_puede_registrar_hallazgo_y_recibe_su_id(cliente, token_de):
    respuesta = preguntar(cliente, "registrar_hallazgo", token_de(Rol.INVESTIGADOR))

    assert respuesta["decision"] == "PERMITIR"
    assert respuesta["usuarioId"] == str(INVESTIGADOR_ID)
    assert respuesta["rol"] == "INVESTIGADOR"


@pytest.mark.parametrize(
    "rol", [Rol.CIENTIFICO_AUTORIZADO, Rol.ALTO_RANGO, Rol.AUDITOR, Rol.ADMINISTRADOR, None]
)
def test_los_demas_no_pueden_registrar_hallazgo(cliente, token_de, rol):
    assert preguntar(cliente, "registrar_hallazgo", token_de(rol))["decision"] == "DENEGAR"


def test_sin_token_se_niega(cliente):
    respuesta = preguntar(cliente, "registrar_hallazgo")
    assert respuesta["decision"] == "DENEGAR"
    assert respuesta["usuarioId"] is None


def test_con_token_falso_se_niega(cliente):
    assert preguntar(cliente, "registrar_hallazgo", "token-inventado")["decision"] == "DENEGAR"


def test_el_visitante_sin_sesion_ve_la_ficha_publica_solo_con_region(cliente):
    respuesta = preguntar(cliente, "ver_ficha_publica")
    assert respuesta["decision"] == "PERMITIR"
    assert respuesta["nivelUbicacion"] == "REGION"


def test_coordenadas_exactas_solo_para_alto_rango(cliente, token_de):
    alto_rango = preguntar(cliente, "ver_ubicacion", token_de(Rol.ALTO_RANGO))
    investigador = preguntar(cliente, "ver_ubicacion", token_de(Rol.INVESTIGADOR))
    visitante = preguntar(cliente, "ver_ubicacion")

    assert (alto_rango["decision"], alto_rango["nivelUbicacion"]) == ("PERMITIR", "EXACTA")
    assert investigador["decision"] == visitante["decision"] == "DENEGAR"


def test_despues_de_cerrar_sesion_se_niega(cliente, token_de):
    token = token_de(Rol.INVESTIGADOR)
    cliente.delete("/sesiones/actual", headers={"Authorization": f"Bearer {token}"})

    assert preguntar(cliente, "registrar_hallazgo", token)["decision"] == "DENEGAR"


def test_una_cuenta_desactivada_se_niega_aunque_su_token_no_haya_vencido(cliente, repositorio, token_de):
    token = token_de(Rol.INVESTIGADOR)
    repositorio.reemplazar(replace(repositorio.por_rol(Rol.INVESTIGADOR), activo=False))

    assert preguntar(cliente, "registrar_hallazgo", token)["decision"] == "DENEGAR"


def test_usa_el_rol_vigente_y_no_el_del_momento_del_login(cliente, repositorio, token_de):
    token = token_de(Rol.INVESTIGADOR)
    repositorio.reemplazar(replace(repositorio.por_rol(Rol.INVESTIGADOR), rol=Rol.AUDITOR))

    assert preguntar(cliente, "registrar_hallazgo", token)["decision"] == "DENEGAR"
    assert preguntar(cliente, "ver_historial", token)["decision"] == "PERMITIR"


def test_una_accion_desconocida_se_niega(cliente, token_de):
    assert preguntar(cliente, "borrar_todo", token_de(Rol.ADMINISTRADOR))["decision"] == "DENEGAR"


def test_si_la_base_falla_se_niega(cliente, repositorio, token_de):
    token = token_de(Rol.INVESTIGADOR)

    def base_caida(_):
        raise RuntimeError("la base no responde")

    repositorio.obtener = base_caida

    respuesta = preguntar(cliente, "registrar_hallazgo", token)
    assert respuesta["decision"] == "DENEGAR"


def test_mantiene_los_campos_que_leen_los_demas_servicios(cliente, token_de):
    respuesta = preguntar(cliente, "registrar_hallazgo", token_de(Rol.INVESTIGADOR), recurso=None)
    assert {"decision", "motivo"} <= respuesta.keys()
