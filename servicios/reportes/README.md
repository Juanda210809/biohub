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

## HU-15 · Índices de presión mensuales

### La fórmula (decisión del equipo)

Por cada **ecosistema** y cada **mes**:

```
índice = hallazgos del mes ÷ promedio mensual de hallazgos de los 3 meses anteriores
```

| Índice | Nivel | Se lee como |
|---|---|---|
| vacío | `SIN_HISTORIA` | No hubo hallazgos en los 3 meses anteriores: no hay contra qué comparar |
| menor que 0,75 | `BAJA` | Menos actividad de lo habitual (0 = ningún hallazgo este mes) |
| 0,75 a 1,25 | `NORMAL` | Lo habitual |
| mayor que 1,25 | `ALTA` | Más presión de lo habitual (1,50 = 50 % más) |

Los hallazgos sin ecosistema se agrupan como "Sin ecosistema". Los meses se cuentan en hora de
Colombia. Si el SRS o el profesor piden otra fórmula, se cambia en `app/dominio/indices.py`
(`calcular` y los umbrales) sin tocar lo demás.

### Cómo se genera

- **Automático:** al arrancar y luego cada hora, el servicio revisa si el mes que terminó ya tiene
  índices; si no, los genera (`app/programador.py`). Si el servicio estaba apagado el día 1, los
  genera apenas vuelve. `REPORTES_AUTOMATICO=0` lo apaga; `REPORTES_INTERVALO_S` cambia cada cuánto revisa.
- **Manual (ALTO_RANGO):** `POST /api/v1/reportes/indices/2026-10` genera o recalcula un mes.
  Recalcular reemplaza las filas de ese mes y deja registro en `reportes.ejecucion_indices`.
- **Consultar (ALTO_RANGO):** `GET /api/v1/reportes/indices/2026-10`, del índice más alto al más bajo.

```json
{
  "periodo": "2026-10", "origen": "MANUAL", "solicitadoPor": "…", "generadoEn": "…",
  "ecosistemas": [
    { "ecosistema": "Bosque húmedo", "hallazgos": 5, "especiesDistintas": 2,
      "promedioPrevio": 2.0, "indice": 2.5, "nivel": "ALTA" }
  ]
}
```

| Respuesta | Cuándo |
|---|---|
| `401 no_autenticado` / `403 sin_permiso` | Sin token / el rol no es ALTO_RANGO |
| `404 indices_no_generados` | Ese mes todavía no tiene índices |
| `422 periodo_invalido` | El mes no es AAAA-MM o todavía no empieza |

### Por qué no frena el registro de hallazgos (RNF-04)

Reportes calcula sobre **su propia base** (BD Reportes), que recibe una copia de
`campo.hallazgo_publico` por replicación lógica. Nunca se conecta a la base operacional, así que
generar los índices no compite con Registro. `svc_reportes` solo puede **leer** esa copia.

## Pruebas

| Tipo | Archivos | Qué prueban | Necesitan |
|---|---|---|---|
| Unitarias (36) | `test_indices.py`, `test_api_indices.py`, `test_programador.py`, `test_autorizacion.py`, `test_salud.py` | Fórmula, niveles, meses (cambio de año, hora de Colombia), rutas, PDP y programador automático | Nada |
| Integración (8) | `test_integracion_indices.py` (la base la prepara `bd_real.py`) | Contra PostgreSQL real con el script de `db/reportes` y la migración real: cálculo con datos de varios meses, recalcular sin duplicar, generación automática una sola vez, 4 generaciones simultáneas sin chocar y que Reportes solo lea la copia | Docker |

```bash
cd servicios/reportes
python -m pytest            # las de integración se saltan si Docker no está prendido; en el CI son obligatorias
```
