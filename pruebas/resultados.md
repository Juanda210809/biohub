# Resultados de las pruebas de aceptación del MVP

## Pico de 60× sobre la ficha pública (HU-20) y registro durante el pico (HU-21)

**Fecha:** 2026-11-20 · **Equipo:** Intel Core i5-12450H, 16 GB de RAM, Windows con Docker Desktop (WSL 2) ·
**Commit de main:** `f564df6` (incluye la caché con el patrón Decorator) · **Herramienta:** Locust 2.32.4
(`pruebas/locustfile.py`) · **Base:** limpia (`docker compose down -v` antes de la corrida)

**Escenario:** 1 minuto de tráfico normal (1 visita/s a la ficha) y luego 10 minutos de pico a 60 visitas/s
(60×) sobre `GET /api/v1/consulta/hallazgos/{id}` por Kong, sin token. En las dos fases, un investigador
registra 2 hallazgos/s con `POST /api/v1/registro/hallazgos` y su token.

**Una sola ficha:** todo el pico va a la misma ficha (`00000000-0000-0000-0000-000000000001`). Es el escenario
que describe el enunciado (el tráfico hacia *esa ficha en particular* se multiplica por más de 60) y también
el mejor caso para la caché, porque casi todas las visitas se resuelven en Redis. Un pico repartido entre
muchas fichas distintas tendría más fallos de caché y más lecturas a la BD Consulta.

**Limitación:** la prueba corre en un solo PC, así que todos los contenedores comparten la misma CPU y
memoria. No demuestra el aislamiento real de recursos entre Consulta y Registro (RNF-03); muestra que,
aun compartiendo máquina, el registro sigue respondiendo durante el pico.

| Fase | Ficha: peticiones | Ficha: fallos | Ficha: p50 | Ficha: p95 | Ficha: p99 | Ficha: pet/s | Registro: POST | Registro: % 201 | Registro: p50 | Registro: p95 | Registro: p99 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| base (1 min) | 60 | 0 | 15 ms | 25 ms | 47 ms | 1,0 | 104 | 100 % | 69 ms | 80 ms | 95 ms |
| pico (10 min) | 35 907 | 0 | 140 ms | 220 ms | 270 ms | 59,8 | 1200 | 100 % | 74 ms | 94 ms | 110 ms |

**403 del registro durante la prueba:** 0 en total; 0 por saturación del PDP
(`docker compose logs --since <inicio> registro`, motivos `PDP no disponible...` y `Error interno del PDP...`).

**Caché con datos enmascarados (HU-20):** `redis-cli GET ficha_publica:00000000-0000-0000-0000-000000000001`
→ solo campos públicos (especie, región, departamento, ecosistema, fecha, atributos públicos, versión);
sin `latitud`, `longitud` ni `precision_m`. Además, `tests/test_consulta_cacheada.py` verifica que la caché
nunca guarda coordenadas.

| Historia | Meta | Resultado | ¿Cumple? |
|---|---|---|---|
| HU-20 · RNF-02 | Ficha p95 < 2 s en el pico de 60×, incluida la validación con el PDP | p95 = 220 ms, 0 fallos en 35 907 peticiones | Sí |
| HU-20 (criterio en Jira) | Ficha p99 < 2 s en el pico | p99 = 270 ms | Sí |
| HU-21 · RNF-03 | ≥ 99,9 % de 201 en el registro durante el pico | 100 % (1200 de 1200), 0 rechazos del PDP | Sí |

**Sobre el 95 % y el 99 %:** el SRS (RNF-02 y EQ-02), el Backlog, el documento de arquitectura y las
diapositivas de la Entrega 2 fijan la meta en el **95 %**; el criterio de HU-20 en Jira dice **99 %**. Se
reportan las dos cifras y se cumplen ambas. Se propuso al equipo corregir Jira a 95 %.

**Observaciones**

- Durante el pico, el registro casi no se degradó: la mediana pasó de 69 a 74 ms y el p95 de 80 a 94 ms.
- La mediana de la ficha subió de 15 a 140 ms con el pico: cada visita pasa por Kong, Consulta, el PDP
  (Identidad, un solo proceso) y Redis. Sigue muy por debajo de la meta de 2 s. Si hiciera falta más
  margen, las mejoras serían más instancias del PDP o reutilizar la conexión HTTP de Consulta hacia el PDP.
- Arranque en frío: como la base se acababa de crear, el primer inicio de sesión tardó 4,3 s y el primer
  registro 4,2 s (los contenedores aún estaban calentando). Por eso la fase base tiene 104 registros y no 120.
  No afecta las metas, que se miden en el pico. Unas pocas visitas al inicio del pico (menos del 0,01 %)
  también tardaron hasta 4,5 s mientras subían los 60 visitantes.
- Comparación con la corrida anterior, sin el Decorator (commit `93f6c73`): ficha p95 270 ms y p99 300 ms;
  registro 1201 de 1201 con 201. El Decorator no empeoró el rendimiento.
- La prueba crea unos 1300 hallazgos reales en la base local; se limpian con `docker compose down -v`.
