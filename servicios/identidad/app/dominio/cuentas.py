"""Caso de uso del administrador: ver las cuentas y asignar roles (HU-02).

No sabe nada de HTTP ni de SQL: recibe el repositorio por el constructor.
"""
from typing import Protocol
from uuid import UUID

from app.dominio.usuarios import Rol, Usuario


class UsuarioNoExiste(Exception):
    """No hay un usuario con ese id."""


class NoPuedeQuitarseAdministrador(Exception):
    """Un administrador no puede quitarse su propio rol: el sistema podría quedar sin administrador."""


class RepositorioDeCuentas(Protocol):
    """Lo que el servicio necesita de la base de datos (lo implementa RepositorioUsuarios)."""

    def listar(self) -> list[Usuario]: ...

    def obtener(self, usuario_id: UUID) -> Usuario | None: ...

    def cambiar_rol(
        self, usuario_id: UUID, rol_anterior: Rol | None, rol_nuevo: Rol | None, actor_id: UUID
    ) -> Usuario: ...


class ServicioCuentas:
    def __init__(self, repositorio: RepositorioDeCuentas) -> None:
        self._repositorio = repositorio

    def listar(self) -> list[Usuario]:
        return self._repositorio.listar()

    def asignar_rol(self, usuario_id: UUID, rol: Rol | None, actor: Usuario) -> Usuario:
        """Asigna un rol (o lo quita con None). El PDP lo aplica desde la siguiente petición."""
        usuario = self._repositorio.obtener(usuario_id)
        if usuario is None:
            raise UsuarioNoExiste
        if usuario.id == actor.id and rol != Rol.ADMINISTRADOR:
            raise NoPuedeQuitarseAdministrador
        if usuario.rol == rol:
            return usuario
        return self._repositorio.cambiar_rol(usuario.id, usuario.rol, rol, actor.id)
