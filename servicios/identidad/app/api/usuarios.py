"""Rutas del administrador para las cuentas internas (HU-02 asignar rol, HU-18 gestionar cuentas)."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencias import exigir_administrador, obtener_cuentas
from app.api.errores import ErrorApi
from app.api.esquemas import (
    AsignacionRolEntrada,
    CambiosCuentaEntrada,
    CuentaNuevaEntrada,
    UsuarioSalida,
)
from app.dominio.cuentas import (
    CorreoYaRegistrado,
    NoPuedeDesactivarseASiMismo,
    NoPuedeQuitarseAdministrador,
    ServicioCuentas,
    UsuarioNoExiste,
)
from app.dominio.usuarios import Usuario

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

Administrador = Annotated[Usuario, Depends(exigir_administrador)]
Cuentas = Annotated[ServicioCuentas, Depends(obtener_cuentas)]


def _no_existe() -> ErrorApi:
    return ErrorApi(404, "usuario_no_existe", "El usuario no existe")


def _correo_repetido() -> ErrorApi:
    return ErrorApi(409, "correo_ya_registrado", "Ya existe una cuenta con ese correo")


@router.get("", response_model=list[UsuarioSalida])
def listar_usuarios(_: Administrador, cuentas: Cuentas) -> list[UsuarioSalida]:
    """Todas las cuentas internas, activas y desactivadas, con su rol. Solo ADMINISTRADOR."""
    return [UsuarioSalida.desde(usuario) for usuario in cuentas.listar()]


@router.post("", response_model=UsuarioSalida, status_code=status.HTTP_201_CREATED)
def crear_cuenta(entrada: CuentaNuevaEntrada, _: Administrador, cuentas: Cuentas) -> UsuarioSalida:
    """Crea una cuenta activa y sin rol. Solo ADMINISTRADOR."""
    try:
        usuario = cuentas.crear(entrada.nombre, entrada.correo, entrada.contrasena)
    except CorreoYaRegistrado:
        raise _correo_repetido() from None
    return UsuarioSalida.desde(usuario)


@router.patch("/{usuario_id}", response_model=UsuarioSalida)
def modificar_cuenta(
    usuario_id: UUID, entrada: CambiosCuentaEntrada, _: Administrador, cuentas: Cuentas
) -> UsuarioSalida:
    """Cambia el nombre, el correo o la contraseña. Solo ADMINISTRADOR."""
    try:
        usuario = cuentas.modificar(usuario_id, entrada.nombre, entrada.correo, entrada.contrasena)
    except UsuarioNoExiste:
        raise _no_existe() from None
    except CorreoYaRegistrado:
        raise _correo_repetido() from None
    return UsuarioSalida.desde(usuario)


@router.post("/{usuario_id}/desactivar", response_model=UsuarioSalida)
def desactivar_cuenta(usuario_id: UUID, administrador: Administrador, cuentas: Cuentas) -> UsuarioSalida:
    """La cuenta no puede iniciar sesión y el PDP le niega todo. No se borra: conserva su autoría."""
    try:
        usuario = cuentas.desactivar(usuario_id, administrador)
    except UsuarioNoExiste:
        raise _no_existe() from None
    except NoPuedeDesactivarseASiMismo:
        raise ErrorApi(
            409, "no_puede_desactivarse", "No puede desactivar su propia cuenta"
        ) from None
    return UsuarioSalida.desde(usuario)


@router.post("/{usuario_id}/activar", response_model=UsuarioSalida)
def activar_cuenta(usuario_id: UUID, _: Administrador, cuentas: Cuentas) -> UsuarioSalida:
    """Vuelve a habilitar una cuenta desactivada. Solo ADMINISTRADOR."""
    try:
        usuario = cuentas.activar(usuario_id)
    except UsuarioNoExiste:
        raise _no_existe() from None
    return UsuarioSalida.desde(usuario)


@router.put("/{usuario_id}/rol", response_model=UsuarioSalida)
def asignar_rol(
    usuario_id: UUID, entrada: AsignacionRolEntrada, administrador: Administrador, cuentas: Cuentas
) -> UsuarioSalida:
    """Asigna uno de los 5 roles (o null para quitarlo). Los permisos cambian de inmediato."""
    try:
        usuario = cuentas.asignar_rol(usuario_id, entrada.rol, administrador)
    except UsuarioNoExiste:
        raise _no_existe() from None
    except NoPuedeQuitarseAdministrador:
        raise ErrorApi(
            409, "no_puede_quitarse_administrador", "No puede quitarse su propio rol de administrador"
        ) from None
    return UsuarioSalida.desde(usuario)
