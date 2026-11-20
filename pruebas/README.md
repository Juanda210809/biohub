# Pruebas de aceptación del MVP

**Responsable:** Matheus. Se ejecutan en la semana 3 contra el sistema completo (`docker compose up`).

| Prueba | Meta | Historia · ASR |
|---|---|---|
| Pico de 60× sobre la ficha pública (k6 o Locust) | < 2 s en el 95 % | HU-20 · RNF-02 |
| Registrar hallazgos durante el pico | Responden con normalidad | HU-21 · RNF-03 |
| Pedir coordenadas con cada rol y sin sesión | Solo ALTO_RANGO; 0 coordenadas fuera de la BD Operacional | HU-07 · RNF-05 |
| Reclasificar sin justificación y dos ediciones a la vez | 422 y 409; versión anterior intacta | HU-08 · RNF-09 |
| Reconstruir un hallazgo en una fecha pasada | < 5 s | HU-12 · RNF-09 |
| 80 peticiones en un minuto con la misma clave | 60 pasan, el resto 429 | HU-14 · RNF-06 |
| Registrar con el reporte mensual corriendo | ≤ 2 s de diferencia | HU-15 · RNF-04 |
| Agregar un atributo a una ficha | Sin cambiar código ni reiniciar | HU-04 · RNF-01 |

Los resultados se anotan en `resultados.md`.

Prueba rápida de la cuota (Kong) ya disponible:

```powershell
# En PowerShell: 65 peticiones seguidas con la clave de prueba; las últimas deben dar 429
1..65 | ForEach-Object { curl.exe -s -o NUL -w "%{http_code}`n" -H "apikey: clave-demo-universidad" http://localhost:8000/externa/v1/hallazgos }
```

## Prueba de carga: pico de 60× (HU-20) con registro en paralelo (HU-21)

Archivo: `locustfile.py`. Una sola corrida mide las dos historias, en dos fases:

| Fase | Duración | Ficha pública (`GET /api/v1/consulta/hallazgos/{id}`, sin token) | Registro (`POST /api/v1/registro/hallazgos`, token de investigador) |
|---|---|---|---|
| base | 1 min | 1 petición/s (tráfico normal, supuesto) | 2 POST/s |
| pico | 10 min | 60 peticiones/s (60× el normal) | 2 POST/s (unos 1200 en total) |

Metas: ficha con p95 < 2 s en el pico (HU-20) y al menos 99,9 % de 201 en el registro durante el pico (HU-21).
Cada POST crea un hallazgo real: se corre **en local** y al final se limpia con `docker compose down -v`.

### Cómo correrla (PowerShell, en la carpeta `biohub`)

```powershell
docker compose up -d --build
python -m venv .venv
.venv\Scripts\python -m pip install -r pruebas\requirements.txt
.venv\Scripts\locust -f pruebas\locustfile.py --headless --host http://localhost:8000 --csv pruebas\salida\carga --html pruebas\salida\reporte.html
```

Al terminar, Locust imprime el resumen por fase y el veredicto. El reporte gráfico queda en
`pruebas\salida\reporte.html` (la carpeta `salida/` no se sube). Para una prueba corta de ensayo:
`$env:BASE_SEGUNDOS=10; $env:PICO_SEGUNDOS=30` antes del comando (luego `Remove-Item Env:BASE_SEGUNDOS, Env:PICO_SEGUNDOS`).

### Contar los 403 de saturación del PDP

Un 403 del registro **no** siempre es saturación. Registro deja el motivo en su log (SCRUM-34):

```powershell
docker compose logs -t registro | Select-String "denegado \(403\)"
docker compose logs -t registro | Select-String "PDP no disponible|Error interno del PDP" | Measure-Object
```

Solo cuentan como saturación `PDP no disponible o respuesta inválida...` y `Error interno del PDP...`.
Un 403 por rol o por sesión vencida es un error de la prueba, no del sistema.
