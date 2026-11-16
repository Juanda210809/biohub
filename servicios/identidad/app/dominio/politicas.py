"""PDP: el único lugar donde se decide quién puede hacer qué (RNF-05).

Las reglas son datos (PERMISOS). Lo que no esté permitido se niega.
"""
from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from app.dominio.autenticacion import ServicioAutenticacion
from app.dominio.tokens import TokenInvalido
from app.dominio.usuarios import Rol, Usuario


class NivelUbicacion(StrEnum):
    REGION = "REGION"
    EXACTA = "EXACTA"


PERMISOS: dict[str, frozenset[Rol]] = {
    "registrar_hallazgo": frozenset({Rol.INVESTIGADOR}),
    "definir_ficha": frozenset({Rol.CIENTIFICO_AUTORIZADO}),
    "ver_ubicacion": frozenset({Rol.ALTO_RANGO}),
    "reclasificar": frozenset({Rol.CIENTIFICO_AUTORIZADO}),
    "ver_historial": frozenset({Rol.AUDITOR}),
    "generar_reporte": frozenset({Rol.ALTO_RANGO}),
    "ver_reportes": frozenset({Rol.ALTO_RANGO}),
    "gestionar_usuarios": frozenset({Rol.ADMINISTRADOR}),
}

# Del visitante sin sesión: se deciden sin tocar la base (pico de HU-20) y nunca dan coordenadas.
ACCIONES_PUBLICAS = frozenset({"ver_ficha_publica"})


@dataclass(frozen=True)
class Decision:
    permitir: bool
    motivo: str
    usuario_id: UUID | None = None
    rol: Rol | None = None
    nivel_ubicacion: NivelUbicacion = NivelUbicacion.REGION


def decidir(accion: str, usuario: Usuario) -> Decision:
    base = {"usuario_id": usuario.id, "rol": usuario.rol}
    if usuario.rol is None:
        return Decision(False, "El usuario no tiene un rol asignado", **base)
    roles = PERMISOS.get(accion)
    if roles is None:
        return Decision(False, f"Acción desconocida: {accion}", **base)
    if usuario.rol not in roles:
        return Decision(False, f"El rol {usuario.rol} no puede hacer '{accion}'", **base)
    nivel = NivelUbicacion.EXACTA if usuario.rol in PERMISOS["ver_ubicacion"] else NivelUbicacion.REGION
    return Decision(True, f"Permitido para el rol {usuario.rol}", nivel_ubicacion=nivel, **base)


class ServicioAutorizacion:
    def __init__(self, autenticacion: ServicioAutenticacion) -> None:
        self._autenticacion = autenticacion

    def autorizar(self, token: str | None, accion: str, recurso: str | None = None) -> Decision:
        if accion in ACCIONES_PUBLICAS:
            return Decision(True, "Consulta pública: solo región o departamento")
        if not token:
            return Decision(False, "Se requiere iniciar sesión")
        try:
            usuario = self._autenticacion.usuario_de_sesion(token)
        except TokenInvalido:
            return Decision(False, "Sesión inválida, vencida, cerrada o de una cuenta desactivada")
        return decidir(accion, usuario)

