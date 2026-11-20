# Resultados de las pruebas de aceptación del MVP

## Pico de 60× sobre la ficha pública (HU-20) y registro durante el pico (HU-21)

**Fecha:** 2026-11-19 · **Equipo:** Intel Core i5-12450H, 16 GB de RAM, Windows con Docker Desktop (WSL 2) ·
**Commit de main:** `93f6c73` · **Herramienta:** Locust 2.32.4 (`pruebas/locustfile.py`)

**Escenario:** 1 minuto de tráfico normal (1 visita/s a la ficha) y luego 10 minutos de pico a 60 visitas/s
(60×) sobre `GET /api/v1/consulta/hallazgos/{id}` por Kong, sin token. En las dos fases, un investigador
registra 2 hallazgos/s con `POST /api/v1/registro/hallazgos` y su token.

**Limitación:** la prueba corre en un solo PC, así que todos los contenedores comparten la misma CPU y
memoria. No demuestra el aislamiento real de recursos entre Consulta y Registro (RNF-03); muestra que,
aun compartiendo máquina, el registro sigue respondiendo durante el pico.

| Fase | Ficha: peticiones | Ficha: fallos | Ficha: p50 | Ficha: p95 | Ficha: pet/s | Registro: POST | Registro: % 201 | Registro: p50 | Registro: p95 |
|---|---|---|---|---|---|---|---|---|---|
| base (1 min) | 60 | 0 | 16 ms | 24 ms | 1,0 | 120 | 100 % | 68 ms | 80 ms |
| pico (10 min) | 35 943 | 0 | 190 ms | 270 ms | 59,9 | 1201 | 100 % | 71 ms | 140 ms |

**403 del registro durante la prueba:** 0 en total; 0 por saturación del PDP
(`docker compose logs --since <inicio> registro`, motivos `PDP no disponible...` y `Error interno del PDP...`).

**Caché con datos enmascarados (HU-20):** `redis-cli GET ficha_publica:00000000-0000-0000-0000-000000000001`
→ solo campos públicos (especie, región, departamento, ecosistema, fecha, atributos públicos, versión);
sin `latitud`, `longitud` ni `precision_m`.

| Historia | Meta | Resultado | ¿Cumple? |
|---|---|---|---|
| HU-20 · RNF-02 | Ficha p95 < 2 s en el pico de 60×, incluida la validación con el PDP | p95 = 270 ms, 0 fallos en 35 943 peticiones | ✅ Sí |
| HU-21 · RNF-03 | ≥ 99,9 % de 201 en el registro durante el pico | 100 % (1201 de 1201), 0 rechazos del PDP | ✅ Sí |

**Observaciones**

- Durante el pico, el registro casi no se degradó: la mediana pasó de 68 a 71 ms y el p95 de 80 a 140 ms.
- La mediana de la ficha subió de 16 a 190 ms con el pico: cada visita pasa por Kong, Consulta, el PDP
  (Identidad, un solo proceso) y Redis. Sigue muy por debajo de la meta de 2 s. Si hiciera falta más
  margen, las mejoras serían más instancias del PDP o reutilizar la conexión HTTP de Consulta hacia el PDP.
- La prueba creó unos 1300 hallazgos reales en la base local; se limpian con `docker compose down -v`.
