"""Rutas de HU-01: iniciar sesión, ver la sesión actual y cerrarla."""
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.dependencias import Credenciales, extraer_token, obtener_autenticacion
from app.api.errores import ErrorApi
from app.api.esquemas import CredencialesEntrada, SesionSalida, UsuarioSalida
from app.dominio.autenticacion import CredencialesInvalidas, ServicioAutenticacion
from app.dominio.tokens import TokenInvalido, TokensNoConfigurados

router = APIRouter(prefix="/sesiones", tags=["sesiones"])

Autenticacion = Annotated[ServicioAutenticacion, Depends(obtener_autenticacion)]


def _sesion_invalida() -> ErrorApi:
    return ErrorApi(401, "sesion_invalida", "La sesión no es válida, venció o ya se cerró")


@router.post("", response_model=SesionSalida, status_code=status.HTTP_201_CREATED)
def iniciar_sesion(entrada: CredencialesEntrada, autenticacion: Autenticacion) -> SesionSalida:
    """Inicia sesión y devuelve un token JWT. Si falla, no dice si fue el correo o la contraseña."""
    try:
        sesion = autenticacion.iniciar_sesion(entrada.correo, entrada.contrasena)
    except CredencialesInvalidas:
        raise ErrorApi(401, "credenciales_invalidas", "Correo o contraseña incorrectos") from None
    except TokensNoConfigurados:
        raise ErrorApi(503, "tokens_no_configurados", "Falta configurar JWT_SECRET") from None
    return SesionSalida(
        token=sesion.token, expira_en=sesion.expira_en, usuario=UsuarioSalida.desde(sesion.usuario)
    )


@router.get("/actual", response_model=UsuarioSalida)
def ver_sesion_actual(credenciales: Credenciales, autenticacion: Autenticacion) -> UsuarioSalida:
    """El usuario dueño del token y su rol."""
    try:
        usuario = autenticacion.usuario_de_sesion(extraer_token(credenciales))
    except TokenInvalido:
        raise _sesion_invalida() from None
    return UsuarioSalida.desde(usuario)


@router.delete("/actual", status_code=status.HTTP_204_NO_CONTENT)
def cerrar_sesion(credenciales: Credenciales, autenticacion: Autenticacion) -> Response:
    """Cierra la sesión: desde ahora el PDP niega ese token."""
    try:
        autenticacion.cerrar_sesion(extraer_token(credenciales))
    except TokenInvalido:
        raise _sesion_invalida() from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
