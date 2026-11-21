import threading

from app.programador import ProgramadorMensual


def test_una_vuelta_llama_la_tarea_con_la_hora():
    llamadas = []
    ProgramadorMensual(lambda ahora: llamadas.append(ahora), 3600).una_vuelta()

    assert len(llamadas) == 1
    assert llamadas[0].tzinfo is not None


def test_un_error_no_tumba_el_programador():
    def falla(_):
        raise RuntimeError("base caída")

    ProgramadorMensual(falla, 3600).una_vuelta()  # no lanza


def test_corre_en_segundo_plano_y_se_detiene():
    corrio = threading.Event()
    programador = ProgramadorMensual(lambda _: corrio.set(), 0.05)

    programador.iniciar()
    assert corrio.wait(2)
    programador.detener()
    assert not programador._hilo.is_alive()
