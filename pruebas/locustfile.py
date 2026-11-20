"""Prueba de carga del MVP: pico de 60x sobre la ficha pública mientras se registran hallazgos.

- HU-20 (RNF-02): la ficha pública responde en menos de 2 s en el 95 % de las peticiones durante
  un pico de 60 veces el tráfico normal, incluida la validación con el PDP.
- HU-21 (RNF-03): durante ese mismo pico, al menos el 99,9 % de los registros responde 201.

Fases (se miden por separado):
  1. base: tráfico normal (1 visitante) y 1 investigador, durante BASE_SEGUNDOS.
  2. pico: 60 veces el tráfico normal (PICO_VISITANTES) y el mismo investigador, durante PICO_SEGUNDOS.

Uso (ver pruebas/README.md):
  locust -f pruebas/locustfile.py --headless --host http://localhost:8000
"""
import os
import time

from locust import HttpUser, LoadTestShape, constant_throughput, events, task

HALLAZGO_ID = os.getenv("HALLAZGO_ID", "00000000-0000-0000-0000-000000000001")
CORREO = os.getenv("CORREO_INVESTIGADOR", "investigador@biohub.local")
CONTRASENA = os.getenv("CONTRASENA_INVESTIGADOR", "BioHub2026!")

BASE_SEGUNDOS = int(os.getenv("BASE_SEGUNDOS", "60"))
PICO_SEGUNDOS = int(os.getenv("PICO_SEGUNDOS", "600"))
PICO_VISITANTES = int(os.getenv("PICO_VISITANTES", "60"))  # 60x el tráfico normal (1 visitante)
REGISTROS_POR_SEGUNDO = float(os.getenv("REGISTROS_POR_SEGUNDO", "2"))

META_P95_FICHA_MS = 2000
META_EXITO_REGISTRO = 0.999

# Cuerpo acordado con Peña (ficha de Anfibio).
HALLAZGO = {
    "especieId": "20000000-0000-0000-0000-000000000001",
    "expedicionId": "30000000-0000-0000-0000-000000000001",
    "fechaHallazgo": "2026-11-10",
    "latitud": 2.5,
    "longitud": -77.0,
    "precisionM": 10,
    "region": "Pacífico",
    "departamento": "Cauca",
    "ecosistema": "Bosque húmedo",
    "atributos": {"temperaturaAgua": 18.5, "longitudCuerpoMm": 45, "habitat": "quebrada"},
}

FICHA = "GET ficha pública"
REGISTRO = "POST registrar hallazgo"

_inicio = {"instante": None}


@events.test_start.add_listener
def _al_empezar(**_):
    _inicio["instante"] = time.monotonic()


def fase_actual() -> str:
    inicio = _inicio["instante"]
    if inicio is None or time.monotonic() - inicio < BASE_SEGUNDOS:
        return "base"
    return "pico"


def nombre(peticion: str) -> str:
    return f"{peticion} [{fase_actual()}]"


class Visitante(HttpUser):
    """Un visitante sin sesión que abre la ficha pública una vez por segundo."""

    wait_time = constant_throughput(1)

    @task
    def ver_ficha(self):
        with self.client.get(
            f"/api/v1/consulta/hallazgos/{HALLAZGO_ID}", name=nombre(FICHA), catch_response=True
        ) as respuesta:
            if respuesta.status_code == 200:
                respuesta.success()
            else:
                respuesta.failure(f"HTTP {respuesta.status_code}")


class Investigador(HttpUser):
    """El investigador que sigue registrando hallazgos durante el pico (siempre hay exactamente 1)."""

    fixed_count = 1
    wait_time = constant_throughput(REGISTROS_POR_SEGUNDO)

    def on_start(self):
        # Un token al inicio: dura 60 min y la prueba completa dura unos 11.
        # Reintenta unos segundos por si un servicio todavía está arrancando.
        for _ in range(10):
            respuesta = self.client.post(
                "/api/v1/identidad/sesiones",
                json={"correo": CORREO, "contrasena": CONTRASENA},
                name="POST iniciar sesión",
            )
            if respuesta.status_code == 201:
                self.cabeceras = {"Authorization": f"Bearer {respuesta.json()['token']}"}
                return
            time.sleep(1)
        raise RuntimeError(f"No se pudo iniciar sesión como {CORREO} (HTTP {respuesta.status_code})")

    @task
    def registrar(self):
        with self.client.post(
            "/api/v1/registro/hallazgos",
            json=HALLAZGO,
            headers=self.cabeceras,
            name=nombre(REGISTRO),
            catch_response=True,
        ) as respuesta:
            if respuesta.status_code == 201:
                respuesta.success()
            elif respuesta.status_code == 403:
                respuesta.failure("HTTP 403 (ver el motivo en: docker compose logs -t registro)")
            else:
                respuesta.failure(f"HTTP {respuesta.status_code}")


class Fases(LoadTestShape):
    """1 visitante en la fase base y PICO_VISITANTES en el pico. El investigador va aparte (fixed_count)."""

    def tick(self):
        tiempo = self.get_run_time()
        if tiempo < BASE_SEGUNDOS:
            return (1 + 1, 10)
        if tiempo < BASE_SEGUNDOS + PICO_SEGUNDOS:
            return (1 + PICO_VISITANTES, 20)
        return None


def _exito(fila) -> float:
    """Fracción de peticiones exitosas (para el registro: las que respondieron 201)."""
    return (fila.num_requests - fila.num_failures) / fila.num_requests if fila.num_requests else 0.0


def _veredicto(cumple: bool) -> str:
    return "CUMPLE" if cumple else "NO CUMPLE"


@events.quitting.add_listener
def _resumen(environment, **_):
    """Imprime el resultado por fase y el veredicto de HU-20 y HU-21 al terminar."""
    estadisticas = environment.runner.stats

    def fila(peticion, metodo, fase):
        return estadisticas.get(f"{peticion} [{fase}]", metodo)

    print("\n" + "=" * 72)
    print("RESUMEN DE LA PRUEBA (copiar en pruebas/resultados.md)")
    print("=" * 72)
    for fase in ("base", "pico"):
        ficha = fila(FICHA, "GET", fase)
        registro = fila(REGISTRO, "POST", fase)
        print(f"\n[{fase}]")
        print(
            f"  Ficha pública: {ficha.num_requests} peticiones, {ficha.num_failures} fallos, "
            f"p50 {ficha.get_response_time_percentile(0.5):.0f} ms, "
            f"p95 {ficha.get_response_time_percentile(0.95):.0f} ms, "
            f"{ficha.total_rps:.1f} pet/s"
        )
        print(
            f"  Registro:      {registro.num_requests} peticiones, "
            f"{_exito(registro) * 100:.2f} % con 201, "
            f"p50 {registro.get_response_time_percentile(0.5):.0f} ms, "
            f"p95 {registro.get_response_time_percentile(0.95):.0f} ms"
        )

    ficha = fila(FICHA, "GET", "pico")
    registro = fila(REGISTRO, "POST", "pico")
    p95 = ficha.get_response_time_percentile(0.95)
    exito = _exito(registro)
    print("\nVEREDICTO")
    print(
        f"  HU-20 ficha p95 < {META_P95_FICHA_MS} ms en el pico: "
        f"{_veredicto(p95 < META_P95_FICHA_MS)} ({p95:.0f} ms)"
    )
    print(
        f"  HU-21 registro >= 99,9 % con 201 en el pico: "
        f"{_veredicto(exito >= META_EXITO_REGISTRO)} ({exito * 100:.2f} %, {registro.num_requests} POST)"
    )
    if registro.num_requests < 1000:
        print("  Aviso: con menos de 1000 POST no se puede afirmar el 99,9 %.")
    if estadisticas.errors:
        print("\nERRORES")
        for error in sorted(estadisticas.errors.values(), key=lambda e: -e.occurrences):
            print(f"  {error.occurrences:>5} x {error.name}: {error.error}")
    print("=" * 72)
