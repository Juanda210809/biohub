"""Generación automática de HU-15: cada hora revisa si el mes que terminó ya tiene índices.

Corre en un hilo aparte dentro del servicio (no hace falta cron ni otro contenedor). Si el
reporte del mes anterior no existe, lo genera; si ya existe, no hace nada. Así, aunque el servicio
esté apagado el día 1, lo genera apenas vuelva a arrancar. Un error se registra y se reintenta
en la siguiente vuelta: nunca tumba el servicio.
"""
import logging
import threading
from collections.abc import Callable
from datetime import UTC, datetime

registro = logging.getLogger(__name__)


class ProgramadorMensual:
    def __init__(self, tarea: Callable[[datetime], object], intervalo_s: float) -> None:
        self._tarea = tarea
        self._intervalo = intervalo_s
        self._parar = threading.Event()
        self._hilo: threading.Thread | None = None

    def una_vuelta(self) -> None:
        try:
            resultado = self._tarea(datetime.now(UTC))
            if resultado is not None:
                registro.info("Índices de presión generados automáticamente: %s", resultado)
        except Exception:
            registro.exception("No se pudieron generar los índices automáticos; se reintenta luego")

    def _bucle(self) -> None:
        while not self._parar.is_set():
            self.una_vuelta()
            self._parar.wait(self._intervalo)

    def iniciar(self) -> None:
        self._hilo = threading.Thread(target=self._bucle, name="indices-mensuales", daemon=True)
        self._hilo.start()

    def detener(self) -> None:
        self._parar.set()
        if self._hilo is not None:
            self._hilo.join(timeout=5)
