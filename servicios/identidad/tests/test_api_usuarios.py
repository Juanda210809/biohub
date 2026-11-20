import pytest

from app.dominio.usuarios import Rol
from tests.conftest import INVESTIGADOR_ID


def cabecera(token):
    return {"Authorization": f"Bearer {token}"}


def asignar(cliente, token, usuario_id, rol):
    return cliente.put(f"/usuarios/{usuario_id}/rol", json={"rol": rol}, headers=cabecera(token))


def preguntar_al_pdp(cliente, token, accion):
    return cliente.post("/interno/autorizar", json={"token": token, "accion": accion}).json()["decision"]


def test_el_administrador_asigna_un_rol(cliente, token_de):
    respuesta = asignar(cliente, token_de(Rol.ADMINISTRADOR), INVESTIGADOR_ID, "AUDITOR")

    assert respuesta.status_code == 200
    assert respuesta.json()["rol"] == "AUDITOR"
    assert respuesta.json()["id"] == str(INVESTIGADOR_ID)


@pytest.mark.parametrize("rol", [r.value for r in Rol])
def test_se_puede_asignar_cualquiera_de_los_cinco_roles(cliente, token_de, rol):
    respuesta = asignar(cliente, token_de(Rol.ADMINISTRADOR), INVESTIGADOR_ID, rol)

    assert respuesta.status_code == 200
    assert respuesta.json()["rol"] == rol


def test_un_rol_que_no_existe_responde_422(cliente, token_de):
    respuesta = asignar(cliente, token_de(Rol.ADMINISTRADOR), INVESTIGADOR_ID, "SUPERUSUARIO")

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "peticion_invalida"


def test_al_cambiar_el_rol_cambian_los_permisos(cliente, token_de):
    token_investigador = token_de(Rol.INVESTIGADOR)
    assert preguntar_al_pdp(cliente, token_investigador, "registrar_hallazgo") == "PERMITIR"

    asignar(cliente, token_de(Rol.ADMINISTRADOR), INVESTIGADOR_ID, "AUDITOR")

    assert preguntar_al_pdp(cliente, token_investigador, "registrar_hallazgo") == "DENEGAR"
    assert preguntar_al_pdp(cliente, token_investigador, "ver_historial") == "PERMITIR"


def test_un_usuario_sin_rol_no_puede_usar_funciones_internas(cliente, token_de):
    token_investigador = token_de(Rol.INVESTIGADOR)

    respuesta = asignar(cliente, token_de(Rol.ADMINISTRADOR), INVESTIGADOR_ID, None)

    assert respuesta.status_code == 200
    assert respuesta.json()["rol"] is None
    assert preguntar_al_pdp(cliente, token_investigador, "registrar_hallazgo") == "DENEGAR"


@pytest.mark.parametrize(
    "rol", [Rol.INVESTIGADOR, Rol.CIENTIFICO_AUTORIZADO, Rol.ALTO_RANGO, Rol.AUDITOR, None]
)
def test_solo_el_administrador_puede_asignar_roles(cliente, token_de, rol):
    respuesta = asignar(cliente, token_de(rol), INVESTIGADOR_ID, "ALTO_RANGO")

    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "sin_permiso"


def test_sin_sesion_responde_401(cliente):
    respuesta = cliente.put(f"/usuarios/{INVESTIGADOR_ID}/rol", json={"rol": "AUDITOR"})

    assert respuesta.status_code == 401


def test_usuario_inexistente_responde_404(cliente, token_de):
    respuesta = asignar(
        cliente, token_de(Rol.ADMINISTRADOR), "00000000-0000-0000-0000-000000000099", "AUDITOR"
    )

    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "usuario_no_existe"


def test_el_administrador_no_puede_quitarse_su_rol(cliente, repositorio, token_de):
    admin = repositorio.por_rol(Rol.ADMINISTRADOR)

    respuesta = asignar(cliente, token_de(Rol.ADMINISTRADOR), admin.id, "AUDITOR")

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "no_puede_quitarse_administrador"


def test_el_administrador_lista_los_usuarios(cliente, token_de):
    respuesta = cliente.get("/usuarios", headers=cabecera(token_de(Rol.ADMINISTRADOR)))

    assert respuesta.status_code == 200
    assert len(respuesta.json()) == 6
    assert "hash" not in respuesta.text.lower()


def test_listar_usuarios_es_solo_para_el_administrador(cliente, token_de):
    respuesta = cliente.get("/usuarios", headers=cabecera(token_de(Rol.ALTO_RANGO)))

    assert respuesta.status_code == 403
