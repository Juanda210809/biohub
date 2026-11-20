"""Caso de uso del administrador: crear, modificar, desactivar cuentas y asignar roles (HU-02, HU-18).

No sabe nada de HTTP ni de SQL: recibe el repositorio por el constructor.
Las cuentas nunca se borran, solo se desactivan: así se conserva la autoría en el historial (RNF-09).
"""
from typing import Protocol
from uuid import UUID, uuid4

from app.dominio.contrasenas import RONDAS, hashear
from app.dominio.usuarios import Rol, Usuario


class UsuarioNoExiste(Exception):
    """No hay un usuario con ese id."""


class CorreoYaRegistrado(Exception):
    """Ya existe otra cuenta con ese correo."""


class NoPuedeQuitarseAdministrador(Exception):
    """Un administrador no puede quitarse su propio rol: el sistema podría quedar sin administrador."""


class NoPuedeDesactivarseASiMismo(Exception):
    """Un administrador no puede desactivar su propia cuenta."""


class RepositorioDeCuentas(Protocol):
    """Lo que el servicio necesita de la base de datos (lo implementa RepositorioUsuarios)."""

    def listar(self) -> list[Usuario]: ...

    def obtener(self, usuario_id: UUID) -> Usuario | None: ...

    def buscar_por_correo(self, correo: str) -> Usuario | None: ...

    def crear(self, usuario: Usuario) -> Usuario: ...

    def actualizar_datos(
        self, usuario_id: UUID, nombre: str, correo: str, hash_contrasena: str
    ) -> Usuario: ...

    def cambiar_activo(self, usuario_id: UUID, activo: bool) -> Usuario: ...

    def cambiar_rol(
        self, usuario_id: UUID, rol_anterior: Rol | None, rol_nuevo: Rol | None, actor_id: UUID
    ) -> Usuario: ...


def _normalizar(correo: str) -> str:
    return correo.strip().lower()


class ServicioCuentas:
    def __init__(self, repositorio: RepositorioDeCuentas, rondas: int = RONDAS) -> None:
        self._repositorio = repositorio
        self._rondas = rondas

    def listar(self) -> list[Usuario]:
        return self._repositorio.listar()

    def crear(self, nombre: str, correo: str, contrasena: str) -> Usuario:
        """La cuenta nace activa y SIN rol: no puede hacer nada hasta que el administrador le asigne uno."""
        correo = _normalizar(correo)
        if self._repositorio.buscar_por_correo(correo) is not None:
            raise CorreoYaRegistrado
        usuario = Usuario(
            id=uuid4(),
            nombre=nombre.strip(),
            correo=correo,
            rol=None,
            activo=True,
            hash_contrasena=hashear(contrasena, self._rondas),
        )
        return self._repositorio.crear(usuario)

    def modificar(
        self,
        usuario_id: UUID,
        nombre: str | None = None,
        correo: str | None = None,
        contrasena: str | None = None,
    ) -> Usuario:
        """Cambia solo los datos que lleguen; los demás quedan igual."""
        usuario = self._obtener(usuario_id)
        if correo is not None:
            correo = _normalizar(correo)
            otro = self._repositorio.buscar_por_correo(correo)
            if otro is not None and otro.id != usuario.id:
                raise CorreoYaRegistrado
        return self._repositorio.actualizar_datos(
            usuario.id,
            nombre.strip() if nombre is not None else usuario.nombre,
            correo if correo is not None else usuario.correo,
            hashear(contrasena, self._rondas) if contrasena is not None else usuario.hash_contrasena,
        )

    def desactivar(self, usuario_id: UUID, actor: Usuario) -> Usuario:
        """No puede iniciar sesión y el PDP le niega todo, pero la cuenta y su autoría se conservan."""
        usuario = self._obtener(usuario_id)
        if usuario.id == actor.id:
            raise NoPuedeDesactivarseASiMismo
        if not usuario.activo:
            return usuario
        return self._repositorio.cambiar_activo(usuario.id, False)

    def activar(self, usuario_id: UUID) -> Usuario:
        usuario = self._obtener(usuario_id)
        if usuario.activo:
            return usuario
        return self._repositorio.cambiar_activo(usuario.id, True)

    def asignar_rol(self, usuario_id: UUID, rol: Rol | None, actor: Usuario) -> Usuario:
        """Asigna un rol (o lo quita con None). El PDP lo aplica desde la siguiente petición."""
        usuario = self._obtener(usuario_id)
        if usuario.id == actor.id and rol != Rol.ADMINISTRADOR:
            raise NoPuedeQuitarseAdministrador
        if usuario.rol == rol:
            return usuario
        return self._repositorio.cambiar_rol(usuario.id, usuario.rol, rol, actor.id)

    def _obtener(self, usuario_id: UUID) -> Usuario:
        usuario = self._repositorio.obtener(usuario_id)
        if usuario is None:
            raise UsuarioNoExiste
        return usuario
