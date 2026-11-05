# Cómo trabajamos

## Reglas de oro

1. Solo se desarrollan las 15 historias con etiqueta **MVP** en Jira.
2. **Nada entra a `main` sin pull request revisado y CI en verde.**
3. Cada persona trabaja en **su carpeta** (ver README). Si necesitas cambiar algo de otro, avísale.
4. Un bloqueo de más de medio día se dice en el grupo.

## Ramas: una por historia

`main` es la versión oficial y siempre debe funcionar. Para cada historia se crea una rama
que sale de `main`, y al terminar se une con un pull request.

Nombre de la rama: `feature/SCRUM-15-registrar-hallazgo` (la clave de Jira la enlaza con la historia).

```powershell
# 1. Traer lo último de main
git checkout main
git pull

# 2. Crear la rama de tu historia
git checkout -b feature/SCRUM-15-registrar-hallazgo

# 3. Trabajar y guardar avances (varias veces al día)
git add .
git commit -m "SCRUM-15: agrega validacion de la ficha"

# 4. Subir tu rama a GitHub
git push -u origin feature/SCRUM-15-registrar-hallazgo

# 5. Si main cambió mientras trabajabas, trae esos cambios a tu rama
git checkout main
git pull
git checkout feature/SCRUM-15-registrar-hallazgo
git merge main
```

6. En GitHub: **Compare & pull request** → llena la plantilla → crea el pull request.
7. Espera **CI en verde** y **una aprobación** → **Squash and merge** → **Delete branch**.
8. En Jira, mueve la historia a «Listo» solo si cumple la definición de terminado.

## Revisar el pull request de un compañero

- ¿Cumple los criterios de aceptación de la historia?
- ¿Tiene pruebas y pasan?
- ¿No sube `.env` ni contraseñas?
- ¿Respeta las rutas acordadas?

Se aprueba o se comenta en menos de 24 horas.

## Dónde va cada cosa dentro de un servicio

| Qué | Dónde |
|---|---|
| Rutas (endpoints) | `app/api/<recurso>.py`, y se registran en `app/main.py` con `app.include_router(...)` |
| Reglas del negocio (por ejemplo, el patrón Strategy) | `app/dominio/` |
| Consultas a la base | `app/repositorio/` usando `app/db.py` |
| Pruebas | `tests/test_<algo>.py` |

## Crear o cambiar tablas (migraciones)

Nadie crea tablas a mano. Cada servicio tiene sus migraciones en `migraciones/` y sus tablas
viven en **su esquema** (`campo`, `gobernanza`, `identidad` o `reportes`).

```powershell
docker compose exec registro alembic revision -m "crea tabla hallazgo"
# Edita el archivo nuevo en servicios/registro/migraciones/versions/
docker compose restart registro    # al arrancar aplica las migraciones pendientes
```

Ejemplo del contenido de una migración:

```python
def upgrade() -> None:
    op.execute("""
        CREATE TABLE campo.hallazgo (
            id UUID PRIMARY KEY,
            especie_id UUID NOT NULL,
            fecha_hallazgo DATE NOT NULL,
            version_actual INTEGER NOT NULL DEFAULT 1
        )
    """)

def downgrade() -> None:
    op.execute("DROP TABLE campo.hallazgo")
```

La tabla `campo.hallazgo_publico` ya existe y se copia sola a BD Consulta y BD Reportes.
Si hay que cambiarla, se coordina con Arias: debe cambiar igual en las 3 bases.

## Permisos: siempre por el PDP (RNF-05)

Ningún servicio decide permisos por su cuenta. Antes de una operación sensible:

```python
from fastapi import Header, HTTPException

from app.autorizacion import autorizar

@router.get("/hallazgos/{hallazgo_id}/ubicacion")
def ver_ubicacion(hallazgo_id: str, authorization: str = Header(default="")):
    token = authorization.removeprefix("Bearer ")
    if not autorizar(token, "ver_ubicacion", hallazgo_id):
        raise HTTPException(status_code=403, detail="Sin permiso")
    ...
```

Hoy el PDP niega todo. Cuando Matheus implemente las reglas (HU-01, HU-02), empezará a permitir según el rol.

## Convenciones

- JSON en español y camelCase: `fechaHallazgo`, `versionEsperada`.
- Errores: `{"codigo": "VERSION_CONFLICTO", "mensaje": "...", "detalles": [...]}`.
- Fechas en UTC, formato ISO 8601: `2026-11-04T15:30:00Z`.
- Commits: `SCRUM-15: agrega POST /hallazgos`.
