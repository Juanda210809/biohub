"""Acceso de Identidad a la base de datos: usuarios, roles y sesiones cerradas (esquema identidad)."""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.dominio.usuarios import Rol, Usuario

COLUMNAS = "id, nombre, correo, hash_contrasena, rol, activo"


def _a_usuario(fila) -> Usuario:
    return Usuario(
        id=fila.id,
        nombre=fila.nombre,
        correo=fila.correo,
        rol=Rol(fila.rol) if fila.rol else None,
        activo=fila.activo,
        hash_contrasena=fila.hash_contrasena,
    )


class RepositorioUsuarios:
    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def buscar_por_correo(self, correo: str) -> Usuario | None:
        fila = self._sesion.execute(
            text(f"SELECT {COLUMNAS} FROM identidad.usuario WHERE lower(correo) = lower(:correo)"),
            {"correo": correo},
        ).first()
        return _a_usuario(fila) if fila else None

    def obtener(self, usuario_id: UUID) -> Usuario | None:
        fila = self._sesion.execute(
            text(f"SELECT {COLUMNAS} FROM identidad.usuario WHERE id = :id"), {"id": usuario_id}
        ).first()
        return _a_usuario(fila) if fila else None

    def listar(self) -> list[Usuario]:
        filas = self._sesion.execute(
            text(f"SELECT {COLUMNAS} FROM identidad.usuario ORDER BY lower(correo)")
        ).all()
        return [_a_usuario(fila) for fila in filas]

    def cambiar_rol(
        self, usuario_id: UUID, rol_anterior: Rol | None, rol_nuevo: Rol | None, actor_id: UUID
    ) -> Usuario:
        """Cambia el rol y deja el cambio en identidad.cambio_rol, en una sola transacción."""
        try:
            fila = self._sesion.execute(
                text(
                    "UPDATE identidad.usuario SET rol = :rol, actualizado_en = now() "
                    f"WHERE id = :id RETURNING {COLUMNAS}"
                ),
                {"rol": rol_nuevo, "id": usuario_id},
            ).one()
            self._sesion.execute(
                text(
                    "INSERT INTO identidad.cambio_rol (id, usuario_id, rol_anterior, rol_nuevo, actor_id) "
                    "VALUES (:id, :usuario_id, :rol_anterior, :rol_nuevo, :actor_id)"
                ),
                {
                    "id": uuid4(),
                    "usuario_id": usuario_id,
                    "rol_anterior": rol_anterior,
                    "rol_nuevo": rol_nuevo,
                    "actor_id": actor_id,
                },
            )
            self._sesion.commit()
        except Exception:
            self._sesion.rollback()
            raise
        return _a_usuario(fila)

    def esta_revocada(self, jti: UUID) -> bool:
        fila = self._sesion.execute(
            text("SELECT 1 FROM identidad.sesion_revocada WHERE jti = :jti"), {"jti": jti}
        ).first()
        return fila is not None

    def revocar_sesion(self, jti: UUID, usuario_id: UUID, expira_en: datetime) -> None:
        try:
            self._sesion.execute(
                text(
                    "INSERT INTO identidad.sesion_revocada (jti, usuario_id, expira_en) "
                    "VALUES (:jti, :usuario_id, :expira_en) ON CONFLICT (jti) DO NOTHING"
                ),
                {"jti": jti, "usuario_id": usuario_id, "expira_en": expira_en},
            )
            self._sesion.commit()
        except Exception:
            self._sesion.rollback()
            raise
