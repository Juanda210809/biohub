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
