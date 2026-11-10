# Servicio Registro y Gestión de Campo

**Dueño:** Peña
**Historias del MVP:** HU-03 Registrar hallazgo · HU-04 Definir atributos de la ficha · HU-21 Registro disponible durante picos de consulta

| Qué | Dónde |
|---|---|
| Arranque de la app | `app/main.py` |
| Rutas (endpoints) | `app/api/` |
| Reglas del negocio | `app/dominio/` |
| Acceso a la base | `app/repositorio/` y `app/db.py` |
| Preguntar permisos al PDP | `app/autorizacion.py` |
| Pruebas | `tests/` |
| Migraciones (tablas) | `migraciones/` — esquema `campo` |

## Crear una tabla nueva

```bash
docker compose exec registro alembic revision -m "crea tabla X"
# edita el archivo nuevo en migraciones/versions/ (funciones upgrade y downgrade)
docker compose restart registro   # al arrancar aplica las migraciones pendientes
```
