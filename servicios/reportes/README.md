# Servicio Reportes y Analítica

**Dueño:** Guarnizo
**Historias del MVP:** HU-15 Generar índices de presión mensuales

| Qué | Dónde |
|---|---|
| Arranque de la app | `app/main.py` |
| Rutas (endpoints) | `app/api/` |
| Reglas del negocio | `app/dominio/` |
| Acceso a la base | `app/repositorio/` y `app/db.py` |
| Preguntar permisos al PDP | `app/autorizacion.py` |
| Pruebas | `tests/` |
| Migraciones (tablas) | `migraciones/` — esquema `reportes` |

## Crear una tabla nueva

```bash
docker compose exec reportes alembic revision -m "crea tabla X"
# edita el archivo nuevo en migraciones/versions/ (funciones upgrade y downgrade)
docker compose restart reportes   # al arrancar aplica las migraciones pendientes
```
