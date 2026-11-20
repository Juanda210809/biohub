"""Falsos y fixtures compartidos: las pruebas de Identidad no usan la base de datos real."""
from dataclasses import replace
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.api.dependencias import obtener_cuentas, obtener_repositorio, obtener_tokens
from app.dominio.autenticacion import ServicioAutenticacion
from app.dominio.contrasenas import hashear
from app.dominio.cuentas import CorreoYaRegistrado, ServicioCuentas
from app.dominio.tokens import ServicioTokens
from app.dominio.usuarios import Rol, Usuario
from app.main import app

SECRETO = "secreto-solo-para-las-pruebas-de-identidad"
CONTRASENA = "Clave-Correcta-2026"
HASH = hashear(CONTRASENA, rondas=4)  # pocas rondas para que las pruebas sean rápidas

INVESTIGADOR_ID = UUID("00000000-0000-0000-0000-0000000000aa")


def nuevo_usuario(numero: int, rol: Rol | None, activo: bool = True) -> Usuario:
    nombre = rol.lower() if rol else "sinrol"
    return Usuario(
        id=UUID(f"00000000-0000-0000-0000-0000000000{numero:02x}"),
        nombre=f"Usuario {nombre}",
        correo=f"{nombre}@biohub.local",
        rol=rol,
        activo=activo,
        hash_contrasena=HASH,
    )


class RepositorioFalso:
    """Reemplaza a RepositorioUsuarios: guarda todo en memoria."""

    def __init__(self) -> None:
        usuarios = [
            nuevo_usuario(0xAA, Rol.INVESTIGADOR),
            nuevo_usuario(0xAB, Rol.CIENTIFICO_AUTORIZADO),
            nuevo_usuario(0xAC, Rol.ALTO_RANGO),
            nuevo_usuario(0xAD, Rol.AUDITOR),
            nuevo_usuario(0xAE, Rol.ADMINISTRADOR),
            nuevo_usuario(0xAF, None),
        ]
        self.usuarios = {u.id: u for u in usuarios}
        self.revocadas: dict[UUID, UUID] = {}
        self.cambios_rol: list[tuple] = []

    def por_rol(self, rol: Rol | None) -> Usuario:
        return next(u for u in self.usuarios.values() if u.rol == rol)

    def reemplazar(self, usuario: Usuario) -> None:
        self.usuarios[usuario.id] = usuario

    def buscar_por_correo(self, correo):
        return next((u for u in self.usuarios.values() if u.correo.lower() == correo.lower()), None)

    def obtener(self, usuario_id):
        return self.usuarios.get(usuario_id)

    def esta_revocada(self, jti):
        return jti in self.revocadas

    def revocar_sesion(self, jti, usuario_id, expira_en):
        self.revocadas[jti] = usuario_id

    def listar(self):
        return sorted(self.usuarios.values(), key=lambda u: u.correo)

    def crear(self, usuario):
        if self.buscar_por_correo(usuario.correo) is not None:
            raise CorreoYaRegistrado
        self.usuarios[usuario.id] = usuario
        return usuario

    def actualizar_datos(self, usuario_id, nombre, correo, hash_contrasena):
        actual = self.usuarios[usuario_id]
        self.usuarios[usuario_id] = replace(
            actual, nombre=nombre, correo=correo, hash_contrasena=hash_contrasena
        )
        return self.usuarios[usuario_id]

    def cambiar_activo(self, usuario_id, activo):
        self.usuarios[usuario_id] = replace(self.usuarios[usuario_id], activo=activo)
        return self.usuarios[usuario_id]

    def cambiar_rol(self, usuario_id, rol_anterior, rol_nuevo, actor_id):
        self.cambios_rol.append((usuario_id, rol_anterior, rol_nuevo, actor_id))
        self.usuarios[usuario_id] = replace(self.usuarios[usuario_id], rol=rol_nuevo)
        return self.usuarios[usuario_id]


@pytest.fixture
def repositorio():
    return RepositorioFalso()


@pytest.fixture
def tokens():
    return ServicioTokens(SECRETO, minutos=60)


@pytest.fixture
def autenticacion(repositorio, tokens):
    return ServicioAutenticacion(repositorio, tokens)


@pytest.fixture
def cuentas(repositorio):
    return ServicioCuentas(repositorio, rondas=4)


@pytest.fixture
def token_de(repositorio, tokens):
    """token_de(Rol.INVESTIGADOR) da un token válido de ese usuario."""
    return lambda rol: tokens.emitir(repositorio.por_rol(rol)).token


@pytest.fixture
def cliente(repositorio, tokens, cuentas):
    app.dependency_overrides[obtener_repositorio] = lambda: repositorio
    app.dependency_overrides[obtener_tokens] = lambda: tokens
    app.dependency_overrides[obtener_cuentas] = lambda: cuentas
    yield TestClient(app)
    app.dependency_overrides.clear()
