# Servicio Identidad y Autorización

**Dueño:** Matheus
**Historias del MVP:** HU-01 Iniciar sesión · HU-02 Asignar rol · HU-18 Gestionar cuentas internas

| Qué | Dónde |
|---|---|
| Arranque de la app | `app/main.py` |
| Rutas (endpoints) | `app/api/` |
| Reglas del negocio | `app/dominio/` |
| Acceso a la base | `app/repositorio/` y `app/db.py` |
| El PDP (decide permisos para todo el sistema) | `app/api/pdp.py` |
| Pruebas | `tests/` |
| Migraciones (tablas) | `migraciones/` — esquema `identidad` |

## Crear una tabla nueva

```bash
docker compose exec identidad alembic revision -m "crea tabla X"
# edita el archivo nuevo en migraciones/versions/ (funciones upgrade y downgrade)
docker compose restart identidad   # al arrancar aplica las migraciones pendientes
```
