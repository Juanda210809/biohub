from app.dominio.usuarios import Rol
from tests.conftest import CONTRASENA, INVESTIGADOR_ID


def iniciar(cliente, correo="investigador@biohub.local", contrasena=CONTRASENA):
    return cliente.post("/sesiones", json={"correo": correo, "contrasena": contrasena})


def cabecera(token):
    return {"Authorization": f"Bearer {token}"}


def test_inicia_sesion_y_responde_201_con_el_token(cliente):
    respuesta = iniciar(cliente)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["tipo"] == "Bearer"
    assert cuerpo["token"]
    assert "expiraEn" in cuerpo
    assert cuerpo["usuario"] == {
        "id": str(INVESTIGADOR_ID),
        "nombre": "Usuario investigador",
        "correo": "investigador@biohub.local",
        "rol": "INVESTIGADOR",
        "activo": True,
    }


def test_la_respuesta_nunca_incluye_el_hash(cliente):
    assert "hash" not in iniciar(cliente).text.lower()


def test_no_dice_si_fallo_el_correo_o_la_contrasena(cliente):
    mala_clave = iniciar(cliente, contrasena="equivocada")
    correo_inexistente = iniciar(cliente, correo="nadie@biohub.local")

    assert mala_clave.status_code == correo_inexistente.status_code == 401
    assert mala_clave.json() == correo_inexistente.json()
    assert mala_clave.json()["codigo"] == "credenciales_invalidas"


def test_sin_datos_responde_422(cliente):
    respuesta = cliente.post("/sesiones", json={})

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "peticion_invalida"


def test_ver_sesion_actual(cliente, token_de):
    respuesta = cliente.get("/sesiones/actual", headers=cabecera(token_de(Rol.AUDITOR)))

    assert respuesta.status_code == 200
    assert respuesta.json()["rol"] == "AUDITOR"


def test_ver_sesion_sin_token_responde_401(cliente):
    respuesta = cliente.get("/sesiones/actual")

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "no_autenticado"


def test_cerrar_sesion(cliente):
    token = iniciar(cliente).json()["token"]

    cerrar = cliente.delete("/sesiones/actual", headers=cabecera(token))
    despues = cliente.get("/sesiones/actual", headers=cabecera(token))

    assert cerrar.status_code == 204
    assert despues.status_code == 401
    assert despues.json()["codigo"] == "sesion_invalida"


def test_cerrar_sesion_con_token_invalido_responde_401(cliente):
    respuesta = cliente.delete("/sesiones/actual", headers=cabecera("no-es-un-token"))
    assert respuesta.status_code == 401
