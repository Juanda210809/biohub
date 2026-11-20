# Resultados de las pruebas de aceptación del MVP

## Pico de 60× sobre la ficha pública (HU-20) y registro durante el pico (HU-21)

**Fecha:** AAAA-MM-DD · **Equipo:** (procesador, RAM) · **Commit de main:** `xxxxxxx`

**Limitación:** la prueba corre en un solo PC, así que todos los contenedores comparten la misma CPU y
memoria. No demuestra el aislamiento real de recursos entre Consulta y Registro (RNF-03); muestra que,
aun compartiendo máquina, el registro sigue respondiendo durante el pico.

| Fase | Ficha: peticiones | Ficha: fallos | Ficha: p50 | Ficha: p95 | Registro: POST | Registro: % 201 | Registro: p50 | Registro: p95 |
|---|---|---|---|---|---|---|---|---|
| base (1 min) | | | | | | | | |
| pico (10 min) | | | | | | | | |

**403 del registro durante el pico:** total ___, de ellos por saturación del PDP ___
(`PDP no disponible...` o `Error interno del PDP...`).

**Caché con datos enmascarados (HU-20):** `redis-cli GET ficha_publica:00000000-0000-0000-0000-000000000001`
→ solo campos públicos; sin `latitud`, `longitud` ni `precision_m`.

| Historia | Meta | Resultado | ¿Cumple? |
|---|---|---|---|
| HU-20 · RNF-02 | Ficha p95 < 2 s en el pico de 60× | | |
| HU-21 · RNF-03 | ≥ 99,9 % de 201 en el registro durante el pico | | |
