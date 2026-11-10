CABECERA = {"Authorization": "Bearer token-de-prueba"}


def test_sin_token_responde_401(cliente, cuerpo):
    respuesta = cliente.post("/hallazgos", json=cuerpo)

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "no_autenticado"


def test_sin_permiso_responde_403_y_no_guarda(cliente, repositorio, autorizador, cuerpo):
    autorizador.permitir = False

    respuesta = cliente.post("/hallazgos", json=cuerpo, headers=CABECERA)

    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "sin_permiso"
    assert repositorio.registrado is None


def test_registra_el_hallazgo_y_responde_201(cliente, repositorio, autorizador, cuerpo):
    respuesta = cliente.post("/hallazgos", json=cuerpo, headers=CABECERA)

    assert respuesta.status_code == 201
    assert respuesta.json() == {"hallazgoId": str(repositorio.hallazgo_id), "version": 1}
    assert autorizador.llamadas == [("token-de-prueba", "registrar_hallazgo", None)]
    datos, nombre_especie, publicos = repositorio.registrado
    assert float(datos.latitud) == 2.512345
    assert datos.region == "Pacifico"
    assert nombre_especie == "Phyllobates terribilis"
    assert publicos == {"temperaturaAgua": 18.5, "habitat": "quebrada"}


def test_basta_con_el_departamento(cliente, cuerpo):
    del cuerpo["region"]

    respuesta = cliente.post("/hallazgos", json=cuerpo, headers=CABECERA)

    assert respuesta.status_code == 201


def test_especie_inexistente_responde_404(cliente, repositorio, cuerpo):
    repositorio.especie = None

    respuesta = cliente.post("/hallazgos", json=cuerpo, headers=CABECERA)

    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "especie_no_existe"


def test_expedicion_inexistente_responde_404(cliente, repositorio, cuerpo):
    repositorio.expedicion_existe = False

    respuesta = cliente.post("/hallazgos", json=cuerpo, headers=CABECERA)

    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "expedicion_no_existe"


def test_ficha_invalida_responde_422_con_los_campos(cliente, repositorio, cuerpo):
    cuerpo["atributos"] = {"temperaturaAgua": 99, "habitat": "mar"}

    respuesta = cliente.post("/hallazgos", json=cuerpo, headers=CABECERA)

    assert respuesta.status_code == 422
    asunto = respuesta.json()
    assert asunto["codigo"] == "ficha_invalida"
    assert [d["campo"] for d in asunto["detalles"]] == ["habitat", "temperaturaAgua"]
    assert repositorio.registrado is None


def test_latitud_fuera_de_rango_responde_422(cliente, cuerpo):
    cuerpo["latitud"] = 200

    respuesta = cliente.post("/hallazgos", json=cuerpo, headers=CABECERA)

    assert respuesta.status_code == 422
    asunto = respuesta.json()
    assert asunto["codigo"] == "peticion_invalida"
    assert asunto["detalles"][0]["campo"] == "latitud"


def test_exige_region_o_departamento(cliente, cuerpo):
    del cuerpo["region"]
    del cuerpo["departamento"]

    respuesta = cliente.post("/hallazgos", json=cuerpo, headers=CABECERA)

    assert respuesta.status_code == 422
    asunto = respuesta.json()
    assert asunto["codigo"] == "peticion_invalida"
    assert asunto["detalles"] == [
        {"campo": "cuerpo", "mensaje": "Debe indicar al menos la region o el departamento"}
    ]


def test_ficha_de_un_tipo_de_especie(cliente, repositorio):
    respuesta = cliente.get(f"/tipos-especie/{repositorio.ficha.tipo_especie_id}/ficha")

    assert respuesta.status_code == 200
    ficha = respuesta.json()
    assert ficha["nombre"] == "Anfibio"
    assert ficha["revision"] == 1
    assert [a["clave"] for a in ficha["atributos"]] == ["habitat", "observaciones", "temperaturaAgua"]
    assert ficha["atributos"][2]["obligatorio"] is True


def test_ficha_inexistente_responde_404(cliente, repositorio):
    repositorio.ficha = None

    respuesta = cliente.get("/tipos-especie/10000000-0000-0000-0000-000000000099/ficha")

    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "ficha_no_existe"
