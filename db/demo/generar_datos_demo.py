"""Genera db/demo/datos-demo.sql: hallazgos de julio a noviembre de 2026 con historia.

Uso (desde la raíz del repo): python db/demo/generar_datos_demo.py
Solo hace falta si se cambian los hallazgos de abajo; el .sql generado se sube al repo.
"""
import json
from pathlib import Path

SALIDA = Path(__file__).with_name("datos-demo.sql")

INVESTIGADOR = "00000000-0000-0000-0000-0000000000aa"
CIENTIFICO = "00000000-0000-0000-0000-0000000000ab"

ESPECIES = {
    "rana": ("20000000-0000-0000-0000-000000000001", "Phyllobates terribilis"),
    "reinita": ("20000000-0000-0000-0000-000000000002", "Setophaga cerulea"),
    "azulejo": ("20000000-0000-0000-0000-000000000003", "Thraupis episcopus"),
}

EXP_CAUCA_I = "30000000-0000-0000-0000-000000000002"
EXP_CAUCA = "30000000-0000-0000-0000-000000000001"  # ya existe: 2026-10-05 a 2026-11-02
EXP_BOYACA = "30000000-0000-0000-0000-000000000003"
EXP_NARINO = "30000000-0000-0000-0000-000000000004"

LUGARES = {
    "Bosque húmedo": ("Pacífico", "Cauca", (2.571, -77.884)),
    "Páramo": ("Andina", "Boyacá", (5.695, -73.452)),
    "Manglar": ("Pacífico", "Nariño", (1.806, -78.764)),
}

# (fecha, ecosistema, especie inicial, expedición, atributos, reclasificaciones)
# reclasificaciones: lista de (instante, especie nueva, justificación)
HALLAZGOS = [
    # Bosque húmedo · Cauca: 1, 1, 1, 3, 1  -> octubre ALTA, noviembre BAJA
    ("2026-07-16", "Bosque húmedo", "rana", EXP_CAUCA_I, {"temperaturaAgua": 21.5, "habitat": "quebrada", "longitudCuerpoMm": 42}, []),
    ("2026-08-09", "Bosque húmedo", "rana", EXP_CAUCA_I, {"temperaturaAgua": 22.0, "habitat": "hojarasca"}, []),
    ("2026-09-21", "Bosque húmedo", "rana", EXP_CAUCA_I, {"temperaturaAgua": 20.8, "habitat": "charca", "longitudCuerpoMm": 47}, []),
    ("2026-10-08", "Bosque húmedo", "rana", EXP_CAUCA, {"temperaturaAgua": 21.1, "habitat": "quebrada"}, []),
    ("2026-10-15", "Bosque húmedo", "rana", EXP_CAUCA, {"temperaturaAgua": 19.9, "habitat": "bosque húmedo", "longitudCuerpoMm": 39}, []),
    ("2026-10-27", "Bosque húmedo", "rana", EXP_CAUCA, {"temperaturaAgua": 22.4, "habitat": "quebrada"}, []),
    ("2026-11-01", "Bosque húmedo", "rana", EXP_CAUCA, {"temperaturaAgua": 21.7, "habitat": "charca"}, []),
    # Páramo · Boyacá: 1, 1, 1, 1, 1 -> NORMAL. Uno con tres versiones (HU-12).
    ("2026-07-24", "Páramo", "azulejo", EXP_BOYACA, {"altitudMsnm": 3420, "numeroIndividuos": 2, "comportamiento": "percha"}, []),
    ("2026-08-19", "Páramo", "azulejo", EXP_BOYACA, {"altitudMsnm": 3510, "numeroIndividuos": 1, "comportamiento": "alimentación"}, []),
    ("2026-09-18", "Páramo", "azulejo", EXP_BOYACA, {"altitudMsnm": 3380, "numeroIndividuos": 3, "comportamiento": "vuelo"}, [
        ("2026-10-07 10:30", "reinita", "Las fotografías muestran plumaje azul cerúleo con garganta blanca: corresponde a reinita cerúlea."),
        ("2026-11-10 16:15", "azulejo", "Análisis genético de la muestra LG-2026-114: confirma azulejo común. Se descarta la reinita cerúlea."),
    ]),
    ("2026-10-22", "Páramo", "azulejo", EXP_BOYACA, {"altitudMsnm": 3460, "numeroIndividuos": 2}, []),
    ("2026-11-12", "Páramo", "azulejo", EXP_BOYACA, {"altitudMsnm": 3490, "numeroIndividuos": 4, "comportamiento": "percha"}, []),
    # Manglar · Nariño: 2, 2, 2, 1, 3 -> octubre BAJA, noviembre ALTA. Uno reclasificado (HU-12).
    ("2026-07-05", "Manglar", "azulejo", EXP_NARINO, {"altitudMsnm": 2, "numeroIndividuos": 5, "comportamiento": "alimentación"}, []),
    ("2026-07-29", "Manglar", "azulejo", EXP_NARINO, {"altitudMsnm": 3, "numeroIndividuos": 3}, []),
    ("2026-08-14", "Manglar", "reinita", EXP_NARINO, {"altitudMsnm": 4, "numeroIndividuos": 1, "comportamiento": "percha"}, [
        ("2026-09-03 09:45", "azulejo", "Revisión de las grabaciones de canto: corresponde a azulejo común, no a reinita cerúlea."),
    ]),
    ("2026-08-30", "Manglar", "azulejo", EXP_NARINO, {"altitudMsnm": 2, "numeroIndividuos": 6, "comportamiento": "nidificación"}, []),
    ("2026-09-06", "Manglar", "azulejo", EXP_NARINO, {"altitudMsnm": 3, "numeroIndividuos": 2}, []),
    ("2026-09-25", "Manglar", "azulejo", EXP_NARINO, {"altitudMsnm": 1, "numeroIndividuos": 4, "comportamiento": "vuelo"}, []),
    ("2026-10-13", "Manglar", "azulejo", EXP_NARINO, {"altitudMsnm": 2, "numeroIndividuos": 2}, []),
    ("2026-11-04", "Manglar", "azulejo", EXP_NARINO, {"altitudMsnm": 3, "numeroIndividuos": 7, "comportamiento": "alimentación"}, []),
    ("2026-11-11", "Manglar", "azulejo", EXP_NARINO, {"altitudMsnm": 2, "numeroIndividuos": 3, "comportamiento": "percha"}, []),
    ("2026-11-18", "Manglar", "azulejo", EXP_NARINO, {"altitudMsnm": 4, "numeroIndividuos": 5}, []),
]

# Atributos que la ficha marca como públicos (observaciones nunca lo es).
PUBLICOS = {"temperaturaAgua", "longitudCuerpoMm", "habitat", "altitudMsnm", "numeroIndividuos", "comportamiento"}


def q(valor):
    if valor is None:
        return "NULL"
    return "'" + str(valor).replace("'", "''") + "'"


def uid(prefijo, n):
    return f"{prefijo}-0000-0000-0000-{n:012d}"


lineas = [
    "-- Datos de demostración de BioHub (julio a noviembre de 2026). Los carga db/demo/cargar-datos-demo.sh.",
    "-- Se pueden volver a cargar sin duplicar nada: cada fila tiene un id fijo y ON CONFLICT DO NOTHING.",
    "-- Generado con db/demo/generar_datos_demo.py: no editar a mano. Coordenadas aproximadas de cada zona.",
    "BEGIN;",
    "",
    "INSERT INTO campo.expedicion (id, nombre, fecha_inicio, fecha_fin) VALUES",
    f"    ({q(EXP_CAUCA_I)}, 'Monitoreo Pacífico Cauca 2026 (I)', '2026-07-01', '2026-09-30'),",
    f"    ({q(EXP_BOYACA)}, 'Expedición Páramos de Boyacá 2026', '2026-07-01', '2026-11-30'),",
    f"    ({q(EXP_NARINO)}, 'Expedición Manglares de Nariño 2026', '2026-07-01', '2026-11-30')",
    "ON CONFLICT (id) DO NOTHING;",
    "",
]

for n, (fecha, eco, especie, exp, atributos, reclasificaciones) in enumerate(HALLAZGOS, start=1):
    hid = uid("60000000", n)
    region, depto, (lat, lon) = LUGARES[eco]
    lat = round(lat + (n % 5) * 0.011, 6)
    lon = round(lon - (n % 4) * 0.013, 6)
    publicos = {k: v for k, v in atributos.items() if k in PUBLICOS}
    versiones = [(f"{fecha} 15:00", especie, "Registro inicial", INVESTIGADOR)]
    versiones += [(inst, esp, just, CIENTIFICO) for inst, esp, just in reclasificaciones]
    actual = versiones[-1]
    esp_id_actual, esp_nombre_actual = ESPECIES[actual[1]]
    instante_actual = f"{actual[0]}-05"

    lineas.append(f"-- {n:02d}. {fecha} · {eco} · {depto}" + (f" · {len(versiones)} versiones" if len(versiones) > 1 else ""))
    lineas.append(
        "INSERT INTO campo.hallazgo (id, especie_id, expedicion_id, investigador_id, fecha_hallazgo, region, departamento, ecosistema, version_actual) VALUES "
        f"({q(hid)}, {q(esp_id_actual)}, {q(exp)}, {q(INVESTIGADOR)}, {q(fecha)}, {q(region)}, {q(depto)}, {q(eco)}, {len(versiones)}) ON CONFLICT (id) DO NOTHING;"
    )
    lineas.append(
        f"INSERT INTO campo.ubicacion (hallazgo_id, latitud, longitud, precision_m) VALUES ({q(hid)}, {lat}, {lon}, {5 + n % 4 * 5}) ON CONFLICT (hallazgo_id) DO NOTHING;"
    )
    for numero, (instante, esp, just, autor) in enumerate(versiones, start=1):
        lineas.append(
            "INSERT INTO gobernanza.hallazgo_version (id, hallazgo_id, numero, especie, atributos, autor_id, justificacion, vigente_desde) VALUES "
            f"({q(uid('61000000', n * 10 + numero))}, {q(hid)}, {numero}, {q(ESPECIES[esp][1])}, {q(json.dumps(atributos, ensure_ascii=False))}::jsonb, "
            f"{q(autor)}, {q(just)}, {q(instante + '-05')}) ON CONFLICT (id) DO NOTHING;"
        )
        accion = "registrar_hallazgo" if numero == 1 else "reclasificar"
        lineas.append(
            "INSERT INTO campo.auditoria (id, actor_id, accion, recurso_id, instante) VALUES "
            f"({q(uid('62000000', n * 10 + numero))}, {q(autor)}, {q(accion)}, {q(hid)}, {q(instante + '-05')}) ON CONFLICT (id) DO NOTHING;"
        )
    lineas.append(
        "INSERT INTO campo.hallazgo_publico (hallazgo_id, especie, region, departamento, ecosistema, fecha_hallazgo, atributos_publicos, version, actualizado_en) VALUES "
        f"({q(hid)}, {q(esp_nombre_actual)}, {q(region)}, {q(depto)}, {q(eco)}, {q(fecha)}, {q(json.dumps(publicos, ensure_ascii=False))}::jsonb, "
        f"{len(versiones)}, {q(instante_actual)}) ON CONFLICT (hallazgo_id) DO NOTHING;"
    )
    lineas.append("")

lineas.append("COMMIT;")
SALIDA.parent.mkdir(parents=True, exist_ok=True)
SALIDA.write_text("\n".join(lineas) + "\n", encoding="utf-8", newline="\n")
print(f"{len(HALLAZGOS)} hallazgos -> {SALIDA.name}")
