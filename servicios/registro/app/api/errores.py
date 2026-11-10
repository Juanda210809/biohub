"""Errores de la API de Registro con el formato del equipo: {"codigo", "mensaje", "detalles"}."""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ErrorApi(Exception):
    def __init__(
        self, estado: int, codigo: str, mensaje: str, detalles: list[dict] | None = None
    ) -> None:
        super().__init__(mensaje)
        self.estado = estado
        self.codigo = codigo
        self.mensaje = mensaje
        self.detalles = detalles or []


def _respuesta(estado: int, codigo: str, mensaje: str, detalles: list[dict]) -> JSONResponse:
    contenido = {"codigo": codigo, "mensaje": mensaje, "detalles": detalles}
    return JSONResponse(status_code=estado, content=contenido)


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(ErrorApi)
    async def manejar_error_api(_: Request, error: ErrorApi) -> JSONResponse:
        return _respuesta(error.estado, error.codigo, error.mensaje, error.detalles)

    @app.exception_handler(RequestValidationError)
    async def manejar_peticion_invalida(_: Request, error: RequestValidationError) -> JSONResponse:
        detalles = [
            {
                "campo": ".".join(str(parte) for parte in e["loc"] if parte != "body") or "cuerpo",
                "mensaje": e["msg"].removeprefix("Value error, "),
            }
            for e in error.errors()
        ]
        return _respuesta(422, "peticion_invalida", "La petición no es válida", detalles)
