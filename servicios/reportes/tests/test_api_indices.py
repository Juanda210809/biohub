from datetime import date

from tests.conftest import ALTO_RANGO_ID

CABECERA = {"Authorization": "Bearer token-de-prueba"}


def test_sin_token_responde_401(cliente):
    assert cliente.post("/indices/2026-10").status_code == 401
    assert cliente.get("/indices/2026-10").json()["codigo"] == "no_autenticado"


def test_sin_permiso_responde_403_y_no_genera(cliente, repositorio, autorizador):
    autorizador.permitir = False

    respuesta = cliente.post("/indices/2026-10", headers=CABECERA)

    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "sin_permiso"
    assert repositorio.guardados == {}


def test_generar_pregunta_por_generar_reporte_y_consultar_por_ver_reportes(cliente, autorizador):
    cliente.post("/indices/2026-10", headers=CABECERA)
    cliente.get("/indices/2026-10", headers=CABECERA)

    assert [a for _, a, _ in autorizador.llamadas] == ["generar_reporte", "ver_reportes"]


def test_genera_los_indices_y_responde_201(cliente, repositorio):
    repositorio.hallazgos = [
        (date(2026, 10, 5), "Bosque húmedo", "A"),
        (date(2026, 10, 9), "Bosque húmedo", "B"),
        (date(2026, 10, 20), "Bosque húmedo", "B"),
        (date(2026, 8, 1), "Bosque húmedo", "A"),
        (date(2026, 9, 1), "Bosque húmedo", "A"),
        (date(2026, 9, 2), "Bosque húmedo", "A"),
    ]

    respuesta = cliente.post("/indices/2026-10", headers=CABECERA)

    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["periodo"] == "2026-10"
    assert datos["origen"] == "MANUAL"
    assert datos["solicitadoPor"] == str(ALTO_RANGO_ID)
    assert datos["ecosistemas"] == [
        {"ecosistema": "Bosque húmedo", "hallazgos": 3, "especiesDistintas": 2,
         "promedioPrevio": 1.0, "indice": 3.0, "nivel": "ALTA"}
    ]


def test_mes_invalido_o_futuro_responde_422(cliente, repositorio):
    invalido = cliente.post("/indices/octubre", headers=CABECERA)
    futuro = cliente.post("/indices/2027-01", headers=CABECERA)

    assert invalido.status_code == futuro.status_code == 422
    assert invalido.json()["codigo"] == futuro.json()["codigo"] == "periodo_invalido"
    assert repositorio.guardados == {}


def test_consultar_un_mes_sin_generar_responde_404(cliente):
    respuesta = cliente.get("/indices/2026-09", headers=CABECERA)

    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "indices_no_generados"


def test_consultar_devuelve_lo_generado(cliente):
    cliente.post("/indices/2026-10", headers=CABECERA)

    respuesta = cliente.get("/indices/2026-10", headers=CABECERA)

    assert respuesta.status_code == 200
    assert respuesta.json()["periodo"] == "2026-10"
