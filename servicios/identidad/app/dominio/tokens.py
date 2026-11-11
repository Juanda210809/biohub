"""Tokens de sesión: JWT de corta duración firmados con JWT_SECRET (HU-01).

El rol no va en el token: el PDP lo lee de la base, así un cambio de rol aplica de inmediato.
"""
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt

from app.dominio.usuarios import Usuario

ALGORITMO = "HS256"


class TokenInvalido(Exception):
    """El token falta, está alterado, venció o no se pudo leer."""


class TokensNoConfigurados(Exception):
    """Falta JWT_SECRET."""


@dataclass(frozen=True)
class TokenEmitido:
    token: str
    jti: UUID
    expira_en: datetime


@dataclass(frozen=True)
class DatosToken:
    usuario_id: UUID
    jti: UUID
    expira_en: datetime


def _ahora() -> datetime:
    return datetime.now(UTC)


class ServicioTokens:
    def __init__(self, secreto: str, minutos: int = 60, reloj: Callable[[], datetime] = _ahora) -> None:
        self._secreto = secreto
        self._minutos = minutos
        self._reloj = reloj

    def emitir(self, usuario: Usuario) -> TokenEmitido:
        if not self._secreto:
            raise TokensNoConfigurados
        ahora = self._reloj()
        expira_en = ahora + timedelta(minutes=self._minutos)
        jti = uuid4()
        carga = {"sub": str(usuario.id), "jti": str(jti), "iat": ahora, "exp": expira_en}
        return TokenEmitido(jwt.encode(carga, self._secreto, algorithm=ALGORITMO), jti, expira_en)

    def leer(self, token: str | None) -> DatosToken:
        if not self._secreto or not token:
            raise TokenInvalido
        try:
            carga = jwt.decode(
                token, self._secreto, algorithms=[ALGORITMO], options={"require": ["sub", "jti", "exp"]}
            )
            return DatosToken(
                usuario_id=UUID(carga["sub"]),
                jti=UUID(carga["jti"]),
                expira_en=datetime.fromtimestamp(carga["exp"], UTC),
            )
        except (jwt.PyJWTError, ValueError, TypeError):
            raise TokenInvalido from None
