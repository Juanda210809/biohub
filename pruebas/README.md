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
