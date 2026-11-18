# Servicio Gobernanza Científica

**Dueño:** Guarnizo
**Historias del MVP:** HU-08 Reclasificar hallazgo · HU-12 Reconstrucción histórica por fecha

| Qué | Dónde |
|---|---|
| Arranque de la app | `app/main.py` |
| Rutas (endpoints) | `app/api/` |
| Reglas del negocio | `app/dominio/` |
| Acceso a la base | `app/repositorio/` y `app/db.py` |
| Preguntar permisos al PDP | `app/autorizacion.py` |
| Pruebas | `tests/` |
| Migraciones (tablas) | `migraciones/` — esquema `gobernanza` |

## Crear una tabla nueva

```bash
docker compose exec gobernanza alembic revision -m "crea tabla X"
# edita el archivo nuevo en migraciones/versions/ (funciones upgrade y downgrade)
docker compose restart gobernanza   # al arrancar aplica las migraciones pendientes
```

## HU-08 · Reclasificar un hallazgo

`POST /api/v1/gobernanza/hallazgos/{hallazgoId}/reclasificaciones`

Encabezado: `Authorization: Bearer <token>` de un usuario con rol **CIENTIFICO_AUTORIZADO**
(por ejemplo `cientifico@biohub.local`, contraseña `BioHub2026!`).

```json
{ "especieId": "20000000-0000-0000-0000-000000000003", "justificacion": "Análisis genético del laboratorio" }
```

Responde `201` con la versión nueva:

```json
{
  "hallazgoId": "…", "version": 2,
  "especieAnterior": "Setophaga cerulea", "especieNueva": "Thraupis episcopus",
  "autorId": "…", "justificacion": "Análisis genético del laboratorio",
  "vigenteDesde": "2026-11-18T15:00:00Z"
}
```

| Respuesta | Cuándo |
|---|---|
| `401 no_autenticado` | Sin token |
| `403 sin_permiso` | El PDP niega (el rol no es CIENTIFICO_AUTORIZADO) |
| `404 hallazgo_no_existe` / `404 especie_no_existe` | El hallazgo o la especie no existen |
| `409 misma_especie` | El hallazgo ya es de esa especie |
| `422 peticion_invalida` | Falta la justificación o está vacía |

En **una sola transacción**: agrega la versión nueva a `gobernanza.hallazgo_version` (la anterior
nunca se borra y conserva sus atributos), cambia la especie en `campo.hallazgo`, actualiza
`campo.hallazgo_publico` y deja el registro en `campo.auditoria`. Quien autoriza sale del token,
no del cuerpo. El hallazgo se bloquea mientras dura la operación, así dos reclasificaciones al
mismo tiempo no repiten el número de versión.

## Pruebas

| Tipo | Archivos | Qué prueban | Necesitan |
|---|---|---|---|
| Unitarias (19) | `test_api_reclasificaciones.py`, `test_servicio_reclasificacion.py`, `test_autorizacion.py`, `test_salud.py` | Rutas, reglas y cliente del PDP con una base y un PDP falsos | Nada |
| Integración (8) | `test_integracion_reclasificacion.py` | Contra PostgreSQL real, con los scripts de `db/operacional` y las migraciones reales: transacción completa, historial, permisos de `svc_gobernanza` y dos reclasificaciones a la vez | Docker |

```bash
cd servicios/gobernanza
python -m pytest            # todas; las de integración se saltan si Docker no está prendido
```

En el CI las de integración son obligatorias: si no pueden correr, el PR queda en rojo.
