# Servicio Consulta Pública

**Dueño:** Luna
**Historias del MVP:** HU-05 Consultar ficha pública · HU-06 Ver región o departamento · HU-13 API externa · HU-20 Caché

| Qué | Dónde |
|---|---|
| Arranque de la app | `app/main.py` |
| Rutas (endpoints) | `app/api/` |
| Reglas del negocio | `app/dominio/` |
| Acceso a la base | `app/repositorio/` y `app/db.py` |
| Preguntar permisos al PDP | `app/autorizacion.py` |
| Pruebas | `tests/` |

Este servicio **no crea tablas**: solo lee la copia de `hallazgo_publico`
que llega por replicación a la BD Consulta. Su usuario de base es de solo lectura.
