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

El token es un JWT firmado con `JWT_SECRET` que dura `TOKEN_MINUTOS` (60 por defecto).
Si el correo o la contraseña fallan, la respuesta es la misma: no dice cuál dato falló (HU-01).

## Usuarios de demostración (SOLO desarrollo local)

Los crea la migración `0001`. Contraseña de todos: `BioHub2026!`

| Correo | Rol | id |
|---|---|---|
| `investigador@biohub.local` | INVESTIGADOR | `00000000-0000-0000-0000-0000000000aa` (= `INVESTIGADOR_PRUEBA_ID` de Registro) |
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
