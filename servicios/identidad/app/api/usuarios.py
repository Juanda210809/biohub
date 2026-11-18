"""Rutas del administrador para las cuentas internas: ver usuarios y asignar roles (HU-02)."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencias import exigir_administrador, obtener_cuentas
from app.api.errores import ErrorApi
from app.api.esquemas import AsignacionRolEntrada, UsuarioSalida
from app.dominio.cuentas import NoPuedeQuitarseAdministrador, ServicioCuentas, UsuarioNoExiste
from app.dominio.usuarios import Usuario

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

Administrador = Annotated[Usuario, Depends(exigir_administrador)]
Cuentas = Annotated[ServicioCuentas, Depends(obtener_cuentas)]


@router.get("", response_model=list[UsuarioSalida])
def listar_usuarios(_: Administrador, cuentas: Cuentas) -> list[UsuarioSalida]:
    """Todas las cuentas internas con su rol. Solo ADMINISTRADOR."""
    return [UsuarioSalida.desde(usuario) for usuario in cuentas.listar()]


@router.put("/{usuario_id}/rol", response_model=UsuarioSalida)
def asignar_rol(
    usuario_id: UUID, entrada: AsignacionRolEntrada, administrador: Administrador, cuentas: Cuentas
) -> UsuarioSalida:
    """Asigna uno de los 5 roles (o null para quitarlo). Los permisos cambian de inmediato."""
    try:
        usuario = cuentas.asignar_rol(usuario_id, entrada.rol, administrador)
    except UsuarioNoExiste:
        raise ErrorApi(404, "usuario_no_existe", "El usuario no existe") from None
    except NoPuedeQuitarseAdministrador:
        raise ErrorApi(
            409, "no_puede_quitarse_administrador", "No puede quitarse su propio rol de administrador"
        ) from None
    return UsuarioSalida.desde(usuario)
