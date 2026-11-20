# Servicio Identidad y Autorización

**Dueño:** Matheus
**Historias del MVP:** HU-01 Iniciar sesión · HU-02 Asignar rol · HU-18 Gestionar cuentas internas

| Qué | Dónde |
|---|---|
| Arranque de la app | `app/main.py` |
| Rutas (endpoints) | `app/api/` |
| Reglas del negocio | `app/dominio/` |
| Acceso a la base | `app/repositorio/` y `app/db.py` |
| El PDP (decide permisos para todo el sistema) | rutas en `app/api/pdp.py`, reglas en `app/dominio/politicas.py` |
| Pruebas | `tests/` |
| Migraciones (tablas) | `migraciones/` — esquema `identidad` |

## Rutas (por Kong: `http://localhost:8000/api/v1/identidad`)

| Método y ruta | Qué hace | Respuesta |
|---|---|---|
| `POST /sesiones` | Inicia sesión con `{"correo", "contrasena"}` | 201 `{token, tipo, expiraEn, usuario}` · 401 `credenciales_invalidas` |
| `GET /sesiones/actual` | Quién tiene la sesión (con `Authorization: Bearer <token>`) | 200 usuario · 401 |
| `DELETE /sesiones/actual` | Cierra la sesión: el PDP niega ese token desde ese momento | 204 · 401 |
| `GET /usuarios` | Lista las cuentas internas (activas y desactivadas) con su rol | 200 · 401 · 403 |
| `POST /usuarios` | Crea una cuenta con `{"nombre", "correo", "contrasena"}`: nace activa y sin rol | 201 · 403 · 409 · 422 |
| `PATCH /usuarios/{id}` | Cambia `nombre`, `correo` y/o `contrasena` (solo los que lleguen) | 200 · 403 · 404 · 409 · 422 |
| `POST /usuarios/{id}/desactivar` | Desactiva la cuenta: no inicia sesión y el PDP le niega todo | 200 · 403 · 404 · 409 |
| `POST /usuarios/{id}/activar` | Vuelve a habilitar una cuenta desactivada | 200 · 403 · 404 |
| `PUT /usuarios/{id}/rol` | Asigna un rol con `{"rol": "AUDITOR"}`, o lo quita con `{"rol": null}` | 200 · 403 · 404 · 409 · 422 |

Todas las rutas de `/usuarios` son solo para ADMINISTRADOR (acción `gestionar_usuarios` del PDP).

El token es un JWT firmado con `JWT_SECRET` que dura `TOKEN_MINUTOS` (60 por defecto).
Si el correo o la contraseña fallan, la respuesta es la misma: no dice cuál dato falló (HU-01).

Al cambiar un rol (HU-02), los permisos cambian desde la siguiente petición, aunque el usuario
no cierre sesión. Cada cambio queda en `identidad.cambio_rol` (quién, a quién, de qué rol a cuál
y cuándo), que es de solo inserción. Un administrador no puede quitarse su propio rol (409).

Las cuentas nunca se borran, solo se desactivan (HU-18): la base no permite `DELETE` en
`identidad.usuario`, así que el autor de cada versión de un hallazgo siempre se puede consultar (RNF-09).
Una cuenta desactivada no puede iniciar sesión y sus sesiones abiertas dejan de servir de inmediato.
Un administrador no puede desactivar su propia cuenta (409). El correo es único sin importar mayúsculas (409).

## Usuarios de demostración (SOLO desarrollo local)

Los crea la migración `0001`. Contraseña de todos: `BioHub2026!`

| Correo | Rol | id |
|---|---|---|
| `investigador@biohub.local` | INVESTIGADOR | `00000000-0000-0000-0000-0000000000aa` (el mismo de los datos de prueba de Registro) |
| `cientifico@biohub.local` | CIENTIFICO_AUTORIZADO | `...0000ab` |
| `altorango@biohub.local` | ALTO_RANGO | `...0000ac` |
| `auditor@biohub.local` | AUDITOR | `...0000ad` |
| `admin@biohub.local` | ADMINISTRADOR | `...0000ae` |
| `sinrol@biohub.local` | (sin rol: no puede usar funciones internas) | `...0000af` |

## Contrato del PDP (`POST /interno/autorizar`, solo dentro de la red de Docker)

Pregunta: `{"token": "<jwt o null>", "accion": "registrar_hallazgo", "recurso": null}`

Respuesta (siempre 200):

```json
{"decision": "PERMITIR", "motivo": "...", "usuarioId": "<uuid>", "rol": "INVESTIGADOR", "nivelUbicacion": "REGION"}
```

- `decision` y `motivo` no cambian: el `app/autorizacion.py` de cada servicio sigue funcionando igual.
- `usuarioId` y `rol` son del usuario del token (sirven, por ejemplo, para el autor de la versión 1).
- `nivelUbicacion` es `EXACTA` solo para ALTO_RANGO; para todos los demás, `REGION`.
- Niega si no hay token, si es falso o venció, si la sesión se cerró, si la cuenta está desactivada,
  si el usuario no tiene rol, si la acción no existe o si algo falla (falla segura).
- El rol se lee de la base en cada pregunta: si el administrador lo cambia, aplica de inmediato.

| Acción | PERMITIR para |
|---|---|
| `registrar_hallazgo` | INVESTIGADOR |
| `definir_ficha` | CIENTIFICO_AUTORIZADO |
| `ver_ubicacion` | ALTO_RANGO |
| `reclasificar` | CIENTIFICO_AUTORIZADO |
| `ver_historial` | AUDITOR |
| `generar_reporte`, `ver_reportes` | ALTO_RANGO |
| `gestionar_usuarios` | ADMINISTRADOR |
| `ver_ficha_publica` | Todos, también sin sesión (nivel REGION, se decide sin tocar la base) |
| cualquier otra | nadie |

¿Necesitas una acción nueva? Pídela a Matheus: es una línea en `PERMISOS` (`app/dominio/politicas.py`).

## Crear una tabla nueva

```bash
docker compose exec identidad alembic revision -m "crea tabla X"
# edita el archivo nuevo en migraciones/versions/ (funciones upgrade y downgrade)
docker compose restart identidad   # al arrancar aplica las migraciones pendientes
```
