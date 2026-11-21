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

## Catálogo para el formulario de HU-03

Cualquier rol interno (acción `consultar_catalogo` del PDP); sin token 401, sin permiso 403.

| Ruta (por Kong) | Respuesta |
|---|---|
| `GET /api/v1/registro/especies` | `[{ id, nombreCientifico, nombreComun, tipoEspecieId, tipoEspecie }]`, por nombre científico |
| `GET /api/v1/registro/expediciones` | `[{ id, nombre, fechaInicio, fechaFin }]`, de la más reciente a la más antigua |

Con el `tipoEspecieId` de la especie elegida se pide `GET /api/v1/registro/tipos-especie/{id}/ficha` para armar los campos del formulario.

## Crear una tabla nueva

```bash
docker compose exec registro alembic revision -m "crea tabla X"
# edita el archivo nuevo en migraciones/versions/ (funciones upgrade y downgrade)
docker compose restart registro   # al arrancar aplica las migraciones pendientes
```


## Disponibilidad durante picos de consulta (HU-21)

**Qué se pide (EQ-03 / RNF-03):** durante un pico de consultas públicas (hasta 60 veces el tráfico normal), `POST /hallazgos` sigue disponible al menos el 99,9 % del tiempo.

**Qué ya cumple el diseño:**

- Registro y Consulta son contenedores distintos: un pico sobre la ficha pública no consume los procesos de Registro.
- Cada uno usa su propia base: Registro escribe en `bd-operacional` y Consulta lee de `bd-consulta` (copia por replicación lógica de `hallazgo_publico`).
- Registro no usa la caché Redis de la consulta pública.

**La dependencia que sí se comparte: el PDP.** Registro pregunta al PDP de Identidad antes de cada `POST /hallazgos` (tiempo máximo de espera: 2 s), y la consulta pública también lo consulta en cada petición. Si el pico satura al PDP, Registro **niega por falla segura** (403), aunque Registro esté sano. No se guardan decisiones del PDP en caché ni se permite cuando no responde: eso rompería RNF-05.

**Cómo se mide:**

- Escenario: durante el pico sobre `GET /api/v1/consulta/hallazgos/{id}`, se lanza `POST /api/v1/registro/hallazgos` con el token de `investigador@biohub.local`. La prueba de carga la escribe Matheus en `pruebas/` (comparte el pico con HU-20).
- Meta: al menos el 99,9 % de los POST responde 201 (máximo 1 fallo por cada 1000). La latencia se reporta, sin meta.
- Cuando Registro niega con 403, deja en su log el motivo del PDP (nunca el token ni se muestra al cliente). Un 403 por saturación del PDP tiene uno de dos motivos: `PDP no disponible o respuesta inválida: se niega (...)` (con `HTTP 503`, `ReadTimeout` o `ConnectError` al final) o `Error interno del PDP: se niega por seguridad` (este llega con 200 desde Identidad). Un 403 con otro motivo (rol incorrecto, sesión inválida) no es saturación. Se cuentan con `docker compose logs -t registro`, que incluye la hora.

**Limitación:** la prueba local no demuestra aislamiento real de recursos, porque todos los contenedores comparten la CPU y la memoria del mismo PC.

**Resultados de la medición** (prueba de carga de Matheus, SCRUM-33; detalle en `pruebas/resultados.md`). Local, i5-12450H con 16 GB; durante 10 minutos de pico a 60× sobre la ficha pública, con 2 `POST /hallazgos` por segundo:

| Medida | Resultado |
|---|---|
| POST con 201 durante el pico | 1201 de 1201 (100 %); la meta era al menos 99,9 % |
| 403 en el log de Registro | 0, así que 0 por saturación del PDP |
| Latencia sin pico (p50 / p95) | 68 ms / 80 ms |
| Latencia durante el pico (p50 / p95) | 71 ms / 140 ms (la latencia no tiene meta) |

**Conclusión:** en esta prueba el registro se mantuvo disponible durante el pico (criterios 1 y 3 de HU-21), y el PDP no se saturó. El criterio 2 (no compiten por los mismos recursos) se cumple por diseño, según la sección anterior. Quedan por la limitación: en un solo PC todos los contenedores comparten CPU, así que el resultado no demuestra aislamiento real de recursos.
