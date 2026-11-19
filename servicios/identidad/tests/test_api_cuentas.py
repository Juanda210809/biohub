import pytest

from app.dominio.usuarios import Rol
from tests.conftest import CONTRASENA, INVESTIGADOR_ID

NUEVA = {"nombre": "Ana Pérez", "correo": "ana@biohub.local", "contrasena": "Clave-Nueva-1"}


def cabecera(token):
    return {"Authorization": f"Bearer {token}"}


def iniciar(cliente, correo, contrasena):
    return cliente.post("/sesiones", json={"correo": correo, "contrasena": contrasena})


def preguntar_al_pdp(cliente, token, accion):
    return cliente.post("/interno/autorizar", json={"token": token, "accion": accion}).json()["decision"]


# --- Crear -----------------------------------------------------------------------------------------
def test_el_administrador_crea_una_cuenta(cliente, token_de):
    respuesta = cliente.post("/usuarios", json=NUEVA, headers=cabecera(token_de(Rol.ADMINISTRADOR)))

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert (cuerpo["nombre"], cuerpo["correo"], cuerpo["rol"], cuerpo["activo"]) == (
        "Ana Pérez",
        "ana@biohub.local",
        None,
        True,
    )
    assert "contrasena" not in respuesta.text and "hash" not in respuesta.text.lower()


def test_la_cuenta_creada_inicia_sesion_pero_sin_rol_no_puede_nada(cliente, token_de):
    cliente.post("/usuarios", json=NUEVA, headers=cabecera(token_de(Rol.ADMINISTRADOR)))

    sesion = iniciar(cliente, "ana@biohub.local", "Clave-Nueva-1")

    assert sesion.status_code == 201
    assert preguntar_al_pdp(cliente, sesion.json()["token"], "registrar_hallazgo") == "DENEGAR"


def test_correo_repetido_responde_409(cliente, token_de):
    repetida = {**NUEVA, "correo": "auditor@biohub.local"}

    respuesta = cliente.post("/usuarios", json=repetida, headers=cabecera(token_de(Rol.ADMINISTRADOR)))

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "correo_ya_registrado"


@pytest.mark.parametrize(
    ("campo", "valor"),
    [("correo", "no-es-un-correo"), ("contrasena", "corta"), ("nombre", "   ")],
)
def test_datos_invalidos_responden_422(cliente, token_de, campo, valor):
    respuesta = cliente.post(
        "/usuarios", json={**NUEVA, campo: valor}, headers=cabecera(token_de(Rol.ADMINISTRADOR))
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["detalles"][0]["campo"] == campo


@pytest.mark.parametrize("rol", [Rol.INVESTIGADOR, Rol.ALTO_RANGO, Rol.AUDITOR, None])
def test_solo_el_administrador_crea_cuentas(cliente, token_de, rol):
    respuesta = cliente.post("/usuarios", json=NUEVA, headers=cabecera(token_de(rol)))

    assert respuesta.status_code == 403


# --- Modificar -------------------------------------------------------------------------------------
def test_el_administrador_modifica_una_cuenta(cliente, token_de):
    respuesta = cliente.patch(
        f"/usuarios/{INVESTIGADOR_ID}",
        json={"nombre": "Investigadora Principal"},
        headers=cabecera(token_de(Rol.ADMINISTRADOR)),
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["nombre"] == "Investigadora Principal"
    assert respuesta.json()["rol"] == "INVESTIGADOR"


def test_modificar_sin_datos_responde_422(cliente, token_de):
    respuesta = cliente.patch(
        f"/usuarios/{INVESTIGADOR_ID}", json={}, headers=cabecera(token_de(Rol.ADMINISTRADOR))
    )

    assert respuesta.status_code == 422


def test_modificar_con_el_correo_de_otro_responde_409(cliente, token_de):
    respuesta = cliente.patch(
        f"/usuarios/{INVESTIGADOR_ID}",
        json={"correo": "auditor@biohub.local"},
        headers=cabecera(token_de(Rol.ADMINISTRADOR)),
    )

    assert respuesta.status_code == 409


def test_modificar_un_usuario_inexistente_responde_404(cliente, token_de):
    respuesta = cliente.patch(
        "/usuarios/00000000-0000-0000-0000-000000000099",
        json={"nombre": "X"},
        headers=cabecera(token_de(Rol.ADMINISTRADOR)),
    )

    assert respuesta.status_code == 404


# --- Desactivar y activar --------------------------------------------------------------------------
def test_una_cuenta_desactivada_no_puede_iniciar_sesion(cliente, token_de):
    respuesta = cliente.post(
        f"/usuarios/{INVESTIGADOR_ID}/desactivar", headers=cabecera(token_de(Rol.ADMINISTRADOR))
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["activo"] is False
    assert iniciar(cliente, "investigador@biohub.local", CONTRASENA).status_code == 401


def test_al_desactivar_su_sesion_abierta_deja_de_servir(cliente, token_de):
    token_investigador = token_de(Rol.INVESTIGADOR)

    cliente.post(f"/usuarios/{INVESTIGADOR_ID}/desactivar", headers=cabecera(token_de(Rol.ADMINISTRADOR)))

    assert preguntar_al_pdp(cliente, token_investigador, "registrar_hallazgo") == "DENEGAR"


def test_desactivar_no_borra_la_cuenta(cliente, token_de):
    admin = cabecera(token_de(Rol.ADMINISTRADOR))
    cliente.post(f"/usuarios/{INVESTIGADOR_ID}/desactivar", headers=admin)

    usuarios = cliente.get("/usuarios", headers=admin).json()

    investigador = next(u for u in usuarios if u["id"] == str(INVESTIGADOR_ID))
    assert (investigador["activo"], investigador["rol"]) == (False, "INVESTIGADOR")


def test_activar_devuelve_el_acceso(cliente, token_de):
    admin = cabecera(token_de(Rol.ADMINISTRADOR))
    cliente.post(f"/usuarios/{INVESTIGADOR_ID}/desactivar", headers=admin)

    respuesta = cliente.post(f"/usuarios/{INVESTIGADOR_ID}/activar", headers=admin)

    assert respuesta.json()["activo"] is True
    assert iniciar(cliente, "investigador@biohub.local", CONTRASENA).status_code == 201


def test_el_administrador_no_puede_desactivarse_a_si_mismo(cliente, repositorio, token_de):
    admin = repositorio.por_rol(Rol.ADMINISTRADOR)

    respuesta = cliente.post(
        f"/usuarios/{admin.id}/desactivar", headers=cabecera(token_de(Rol.ADMINISTRADOR))
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "no_puede_desactivarse"


def test_solo_el_administrador_desactiva(cliente, token_de):
    respuesta = cliente.post(
        f"/usuarios/{INVESTIGADOR_ID}/desactivar", headers=cabecera(token_de(Rol.ALTO_RANGO))
    )

    assert respuesta.status_code == 403
