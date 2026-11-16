"""Caso de uso: iniciar sesión, saber quién tiene la sesión y cerrarla (HU-01).

No sabe nada de HTTP ni de SQL: recibe el repositorio y los tokens por el constructor.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.dominio.contrasenas import hash_de_relleno, verificar
from app.dominio.tokens import ServicioTokens, TokenInvalido
from app.dominio.usuarios import Usuario


class CredencialesInvalidas(Exception):
    """Correo o contraseña incorrectos, o cuenta desactivada. No dice cuál."""


class RepositorioDeUsuarios(Protocol):
    """Lo que el servicio necesita de la base de datos (lo implementa RepositorioUsuarios)."""

    def buscar_por_correo(self, correo: str) -> Usuario | None: ...

    def obtener(self, usuario_id: UUID) -> Usuario | None: ...

    def esta_revocada(self, jti: UUID) -> bool: ...

    def revocar_sesion(self, jti: UUID, usuario_id: UUID, expira_en: datetime) -> None: ...


@dataclass(frozen=True)
class SesionIniciada:
    token: str
    expira_en: datetime
    usuario: Usuario


class ServicioAutenticacion:
    def __init__(self, repositorio: RepositorioDeUsuarios, tokens: ServicioTokens) -> None:
        self._repositorio = repositorio
        self._tokens = tokens

    def iniciar_sesion(self, correo: str, contrasena: str) -> SesionIniciada:
        usuario = self._repositorio.buscar_por_correo(correo.strip().lower())
        if usuario is None:
            verificar(contrasena, hash_de_relleno())
            raise CredencialesInvalidas
        if not verificar(contrasena, usuario.hash_contrasena) or not usuario.activo:
            raise CredencialesInvalidas
        emitido = self._tokens.emitir(usuario)
        return SesionIniciada(emitido.token, emitido.expira_en, usuario)

    def usuario_de_sesion(self, token: str | None) -> Usuario:
        """El dueño de una sesión vigente; TokenInvalido si no la hay."""
        datos = self._tokens.leer(token)
        if self._repositorio.esta_revocada(datos.jti):
            raise TokenInvalido
        usuario = self._repositorio.obtener(datos.usuario_id)
        if usuario is None or not usuario.activo:
            raise TokenInvalido
        return usuario

    def cerrar_sesion(self, token: str | None) -> None:
        datos = self._tokens.leer(token)
        self._repositorio.revocar_sesion(datos.jti, datos.usuario_id, datos.expira_en)
