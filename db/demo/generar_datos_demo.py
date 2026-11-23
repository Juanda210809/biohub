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
    "rana-franjas": ("20000000-0000-0000-0000-000000000004", "Dendrobates truncatus"),
    "gallito": ("20000000-0000-0000-0000-000000000005", "Rupicola peruvianus"),
    "flamenco": ("20000000-0000-0000-0000-000000000006", "Phoenicopterus ruber"),
}

TIPO_ANFIBIO = "10000000-0000-0000-0000-000000000001"
TIPO_AVE = "10000000-0000-0000-0000-000000000002"
# Las 3 primeras vienen con la migración de Registro; estas se suman al catálogo para la demo.
ESPECIES_NUEVAS = [
    ("rana-franjas", TIPO_ANFIBIO, "rana venenosa de franjas amarillas", False),
    ("gallito", TIPO_AVE, "gallito de roca andino", False),
    ("flamenco", TIPO_AVE, "flamenco americano", False),
]

EXP_CAUCA_I = "30000000-0000-0000-0000-000000000002"
EXP_CAUCA = "30000000-0000-0000-0000-000000000001"  # ya existe: 2026-10-05 a 2026-11-02
EXP_BOYACA = "30000000-0000-0000-0000-000000000003"
EXP_NARINO = "30000000-0000-0000-0000-000000000004"
EXP_GUAJIRA = "30000000-0000-0000-0000-000000000005"
EXP_CORDOBA = "30000000-0000-0000-0000-000000000006"
EXP_RISARALDA = "30000000-0000-0000-0000-000000000007"
EXP_SANTANDER = "30000000-0000-0000-0000-000000000008"
EXP_CASANARE = "30000000-0000-0000-0000-000000000009"
EXP_AMAZONAS = "30000000-0000-0000-0000-000000000010"

LUGARES = {
    "Bosque húmedo": ("Pacífico", "Cauca", (2.571, -77.884)),
    "Páramo": ("Andina", "Boyacá", (5.695, -73.452)),
    "Manglar": ("Pacífico", "Nariño", (1.806, -78.764)),
    "Laguna costera": ("Caribe", "La Guajira", (11.392, -73.140)),
    "Bosque seco": ("Caribe", "Córdoba", (8.512, -75.705)),
    "Bosque de niebla": ("Andina", "Risaralda", (4.733, -75.546)),
    "Robledal": ("Andina", "Santander", (6.142, -73.394)),
    "Sabana inundable": ("Orinoquía", "Casanare", (5.881, -71.891)),
    "Selva amazónica": ("Amazonía", "Amazonas", (-4.112, -69.951)),
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
    # Laguna costera · La Guajira (Caribe): 1, 1, 1, 2, 2 -> octubre ALTA
    ("2026-07-12", "Laguna costera", "flamenco", EXP_GUAJIRA, {"altitudMsnm": 1, "numeroIndividuos": 120, "comportamiento": "alimentación"}, []),
    ("2026-08-21", "Laguna costera", "flamenco", EXP_GUAJIRA, {"altitudMsnm": 2, "numeroIndividuos": 85}, []),
    ("2026-09-14", "Laguna costera", "flamenco", EXP_GUAJIRA, {"altitudMsnm": 1, "numeroIndividuos": 210, "comportamiento": "nidificación"}, []),
    ("2026-10-04", "Laguna costera", "flamenco", EXP_GUAJIRA, {"altitudMsnm": 1, "numeroIndividuos": 160, "comportamiento": "alimentación"}, []),
    ("2026-10-19", "Laguna costera", "flamenco", EXP_GUAJIRA, {"altitudMsnm": 2, "numeroIndividuos": 95, "comportamiento": "vuelo"}, []),
    ("2026-11-15", "Laguna costera", "flamenco", EXP_GUAJIRA, {"altitudMsnm": 1, "numeroIndividuos": 140}, []),
    ("2026-11-21", "Laguna costera", "flamenco", EXP_GUAJIRA, {"altitudMsnm": 1, "numeroIndividuos": 230, "comportamiento": "alimentación"}, []),
    # Bosque seco · Córdoba (Caribe): 1, 1, 1, 1, 2 -> octubre NORMAL
    ("2026-07-20", "Bosque seco", "rana-franjas", EXP_CORDOBA, {"temperaturaAgua": 26.4, "habitat": "hojarasca", "longitudCuerpoMm": 31}, []),
    ("2026-08-11", "Bosque seco", "rana-franjas", EXP_CORDOBA, {"temperaturaAgua": 27.1, "habitat": "quebrada"}, []),
    ("2026-09-09", "Bosque seco", "rana-franjas", EXP_CORDOBA, {"temperaturaAgua": 25.8, "habitat": "hojarasca", "longitudCuerpoMm": 28}, []),
    ("2026-10-24", "Bosque seco", "rana-franjas", EXP_CORDOBA, {"temperaturaAgua": 26.0, "habitat": "charca"}, []),
    ("2026-11-08", "Bosque seco", "rana-franjas", EXP_CORDOBA, {"temperaturaAgua": 26.9, "habitat": "hojarasca", "longitudCuerpoMm": 33}, []),
    ("2026-11-17", "Bosque seco", "rana-franjas", EXP_CORDOBA, {"temperaturaAgua": 27.3, "habitat": "quebrada"}, []),
    # Bosque de niebla · Risaralda (Andina): 2, 2, 1, 1, 2 -> octubre BAJA
    ("2026-07-08", "Bosque de niebla", "gallito", EXP_RISARALDA, {"altitudMsnm": 2180, "numeroIndividuos": 4, "comportamiento": "percha"}, []),
    ("2026-07-30", "Bosque de niebla", "gallito", EXP_RISARALDA, {"altitudMsnm": 2240, "numeroIndividuos": 6}, []),
    ("2026-08-12", "Bosque de niebla", "gallito", EXP_RISARALDA, {"altitudMsnm": 2310, "numeroIndividuos": 3, "comportamiento": "alimentación"}, []),
    ("2026-08-26", "Bosque de niebla", "gallito", EXP_RISARALDA, {"altitudMsnm": 2205, "numeroIndividuos": 5, "comportamiento": "percha"}, []),
    ("2026-09-17", "Bosque de niebla", "gallito", EXP_RISARALDA, {"altitudMsnm": 2150, "numeroIndividuos": 2}, []),
    ("2026-10-21", "Bosque de niebla", "gallito", EXP_RISARALDA, {"altitudMsnm": 2260, "numeroIndividuos": 3, "comportamiento": "vuelo"}, []),
    ("2026-11-06", "Bosque de niebla", "gallito", EXP_RISARALDA, {"altitudMsnm": 2290, "numeroIndividuos": 7, "comportamiento": "percha"}, []),
    ("2026-11-19", "Bosque de niebla", "gallito", EXP_RISARALDA, {"altitudMsnm": 2230, "numeroIndividuos": 4}, []),
    # Robledal · Santander (Andina), donde la reinita pasa el invierno: 0, 0, 2, 1, 2 -> octubre ALTA
    ("2026-09-12", "Robledal", "reinita", EXP_SANTANDER, {"altitudMsnm": 2050, "numeroIndividuos": 1, "comportamiento": "alimentación"}, []),
    ("2026-09-28", "Robledal", "reinita", EXP_SANTANDER, {"altitudMsnm": 2120, "numeroIndividuos": 2, "comportamiento": "percha"}, []),
    ("2026-10-10", "Robledal", "reinita", EXP_SANTANDER, {"altitudMsnm": 2190, "numeroIndividuos": 1}, []),
    ("2026-11-03", "Robledal", "reinita", EXP_SANTANDER, {"altitudMsnm": 2080, "numeroIndividuos": 3, "comportamiento": "alimentación"}, []),
    ("2026-11-16", "Robledal", "reinita", EXP_SANTANDER, {"altitudMsnm": 2150, "numeroIndividuos": 2, "comportamiento": "percha"}, []),
    # Sabana inundable · Casanare (Orinoquía): 1, 1, 1, 1, 1 -> octubre NORMAL
    ("2026-07-15", "Sabana inundable", "azulejo", EXP_CASANARE, {"altitudMsnm": 180, "numeroIndividuos": 3, "comportamiento": "percha"}, []),
    ("2026-08-05", "Sabana inundable", "azulejo", EXP_CASANARE, {"altitudMsnm": 175, "numeroIndividuos": 2}, []),
    ("2026-09-02", "Sabana inundable", "azulejo", EXP_CASANARE, {"altitudMsnm": 190, "numeroIndividuos": 4, "comportamiento": "alimentación"}, []),
    ("2026-10-17", "Sabana inundable", "azulejo", EXP_CASANARE, {"altitudMsnm": 182, "numeroIndividuos": 2, "comportamiento": "vuelo"}, []),
    ("2026-11-01", "Sabana inundable", "azulejo", EXP_CASANARE, {"altitudMsnm": 178, "numeroIndividuos": 5}, []),
    # Selva amazónica · Amazonas (Amazonía): 1, 1, 1, 0, 1 -> octubre BAJA (sin hallazgos ese mes)
    ("2026-07-26", "Selva amazónica", "azulejo", EXP_AMAZONAS, {"altitudMsnm": 95, "numeroIndividuos": 2, "comportamiento": "alimentación"}, []),
    ("2026-08-17", "Selva amazónica", "azulejo", EXP_AMAZONAS, {"altitudMsnm": 88, "numeroIndividuos": 3}, []),
    ("2026-09-23", "Selva amazónica", "azulejo", EXP_AMAZONAS, {"altitudMsnm": 102, "numeroIndividuos": 1, "comportamiento": "percha"}, []),
    ("2026-11-02", "Selva amazónica", "azulejo", EXP_AMAZONAS, {"altitudMsnm": 91, "numeroIndividuos": 4, "comportamiento": "vuelo"}, []),
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
    f"    ({q(EXP_NARINO)}, 'Expedición Manglares de Nariño 2026', '2026-07-01', '2026-11-30'),",
    f"    ({q(EXP_GUAJIRA)}, 'Censo de flamencos La Guajira 2026', '2026-07-01', '2026-11-30'),",
    f"    ({q(EXP_CORDOBA)}, 'Monitoreo Bosque Seco Córdoba 2026', '2026-07-01', '2026-11-30'),",
    f"    ({q(EXP_RISARALDA)}, 'Expedición Bosques de Niebla Risaralda 2026', '2026-07-01', '2026-11-30'),",
    f"    ({q(EXP_SANTANDER)}, 'Monitoreo Robledales de Santander 2026', '2026-09-01', '2026-11-30'),",
    f"    ({q(EXP_CASANARE)}, 'Expedición Sabanas de Casanare 2026', '2026-07-01', '2026-11-30'),",
    f"    ({q(EXP_AMAZONAS)}, 'Expedición Amazonas 2026', '2026-07-01', '2026-11-30')",
    "ON CONFLICT (id) DO NOTHING;",
    "",
    "INSERT INTO campo.especie (id, tipo_especie_id, nombre_cientifico, nombre_comun, en_peligro) VALUES",
    ",\n".join(
        f"    ({q(ESPECIES[clave][0])}, {q(tipo)}, {q(ESPECIES[clave][1])}, {q(comun)}, {str(peligro).lower()})"
        for clave, tipo, comun, peligro in ESPECIES_NUEVAS
    ),
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
