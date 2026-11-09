"""Crea las tablas de Registro en el esquema campo (HU-03) y sus datos de ejemplo.

- Tablas: tipo_especie, especie, expedicion, revision_ficha, definicion_atributo, hallazgo,
  ubicacion y auditoria.
- Los atributos de un hallazgo NO se guardan en campo.hallazgo: viven en
  gobernanza.hallazgo_version (todos) y en campo.hallazgo_publico (solo los publicables).
- Gobernanza puede leer campo.hallazgo y cambiar SOLO especie_id y version_actual.
- campo.auditoria es de solo inserción, también para el dueño (svc_registro).
- Cada sentencia va en su propio op.execute. En el JSON de los datos de ejemplo siempre hay un
  espacio después de los dos puntos: SQLAlchemy toma ":algo" como un parámetro y fallaría.

Revision ID: 0001
Revises:
Create Date: 2026-11-09
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLAS = [
    """
    CREATE TABLE campo.tipo_especie (
        id      UUID PRIMARY KEY,
        nombre  TEXT NOT NULL UNIQUE
    )
    """,
    """
    CREATE TABLE campo.especie (
        id                UUID PRIMARY KEY,
        tipo_especie_id   UUID NOT NULL REFERENCES campo.tipo_especie (id),
        nombre_cientifico TEXT NOT NULL UNIQUE,
        nombre_comun      TEXT,
        en_peligro        BOOLEAN NOT NULL DEFAULT false
    )
    """,
    """
    CREATE TABLE campo.expedicion (
        id            UUID PRIMARY KEY,
        nombre        TEXT NOT NULL,
        fecha_inicio  DATE NOT NULL,
        fecha_fin     DATE,
        CONSTRAINT expedicion_fechas CHECK (fecha_fin IS NULL OR fecha_fin >= fecha_inicio)
    )
    """,
    """
    CREATE TABLE campo.revision_ficha (
        id               UUID PRIMARY KEY,
        tipo_especie_id  UUID NOT NULL REFERENCES campo.tipo_especie (id),
        numero           INTEGER NOT NULL CHECK (numero >= 1),
        estado           TEXT NOT NULL CHECK (estado IN ('BORRADOR', 'PUBLICADA', 'REEMPLAZADA')),
        publicada_en     TIMESTAMPTZ,
        CONSTRAINT revision_ficha_unica UNIQUE (tipo_especie_id, numero)
    )
    """,
    # Un tipo de especie tiene como máximo UNA revisión vigente (PUBLICADA).
    """
    CREATE UNIQUE INDEX revision_ficha_vigente
        ON campo.revision_ficha (tipo_especie_id) WHERE estado = 'PUBLICADA'
    """,
    """
    CREATE TABLE campo.definicion_atributo (
        id                UUID PRIMARY KEY,
        revision_ficha_id UUID NOT NULL REFERENCES campo.revision_ficha (id),
        clave             TEXT NOT NULL,
        etiqueta          TEXT NOT NULL,
        tipo              TEXT NOT NULL CHECK (tipo IN ('NUMERO', 'TEXTO', 'FECHA', 'SELECCION')),
        obligatorio       BOOLEAN NOT NULL DEFAULT false,
        reglas            JSONB NOT NULL DEFAULT '{}'::jsonb,
        publicable        BOOLEAN NOT NULL DEFAULT false,
        activo            BOOLEAN NOT NULL DEFAULT true,
        CONSTRAINT definicion_atributo_unica UNIQUE (revision_ficha_id, clave)
    )
    """,
    # investigador_id no tiene llave foránea: los usuarios viven en Identidad, otro servicio.
    """
    CREATE TABLE campo.hallazgo (
        id               UUID PRIMARY KEY,
        especie_id       UUID NOT NULL REFERENCES campo.especie (id),
        expedicion_id    UUID NOT NULL REFERENCES campo.expedicion (id),
        investigador_id  UUID NOT NULL,
        fecha_hallazgo   DATE NOT NULL,
        region           TEXT,
        departamento     TEXT,
        ecosistema       TEXT,
        version_actual   INTEGER NOT NULL DEFAULT 1
    )
    """,
    # La ubicación exacta: solo existe en esta base (RNF-05).
    """
    CREATE TABLE campo.ubicacion (
        hallazgo_id  UUID PRIMARY KEY REFERENCES campo.hallazgo (id),
        latitud      NUMERIC(9, 6) NOT NULL CHECK (latitud BETWEEN -90 AND 90),
        longitud     NUMERIC(9, 6) NOT NULL CHECK (longitud BETWEEN -180 AND 180),
        precision_m  NUMERIC(8, 2) CHECK (precision_m >= 0)
    )
    """,
    """
    CREATE TABLE campo.auditoria (
        id          UUID PRIMARY KEY,
        actor_id    UUID NOT NULL,
        accion      TEXT NOT NULL,
        recurso_id  UUID,
        instante    TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
]

PERMISOS = [
    # Gobernanza lee el hallazgo y, al reclasificar, cambia solo la especie y la versión actual.
    "GRANT SELECT ON campo.hallazgo TO svc_gobernanza",
    "GRANT UPDATE (especie_id, version_actual) ON campo.hallazgo TO svc_gobernanza",
    # La auditoría es compartida y de solo inserción.
    "GRANT INSERT ON campo.auditoria TO svc_gobernanza",
    "REVOKE UPDATE, DELETE, TRUNCATE ON campo.auditoria FROM svc_registro",
]

DATOS_DE_EJEMPLO = [
    """
    INSERT INTO campo.tipo_especie (id, nombre) VALUES
        ('10000000-0000-0000-0000-000000000001', 'Anfibio'),
        ('10000000-0000-0000-0000-000000000002', 'Ave')
    """,
    """
    INSERT INTO campo.especie (id, tipo_especie_id, nombre_cientifico, nombre_comun, en_peligro) VALUES
        ('20000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001',
         'Phyllobates terribilis', 'rana dorada venenosa', true),
        ('20000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000002',
         'Setophaga cerulea', 'reinita cerúlea', true),
        ('20000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000002',
         'Thraupis episcopus', 'azulejo común', false)
    """,
    """
    INSERT INTO campo.expedicion (id, nombre, fecha_inicio, fecha_fin) VALUES
        ('30000000-0000-0000-0000-000000000001', 'Expedición Pacífico Cauca 2026',
         '2026-10-05', '2026-11-02')
    """,
    """
    INSERT INTO campo.revision_ficha (id, tipo_especie_id, numero, estado, publicada_en) VALUES
        ('40000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001',
         1, 'PUBLICADA', now()),
        ('40000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000002',
         1, 'PUBLICADA', now())
    """,
    """
    INSERT INTO campo.definicion_atributo
        (id, revision_ficha_id, clave, etiqueta, tipo, obligatorio, reglas, publicable) VALUES
        ('50000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001',
         'temperaturaAgua', 'Temperatura del agua (°C)', 'NUMERO', true,
         '{"minimo": 0, "maximo": 40, "unidad": "°C"}', true),
        ('50000000-0000-0000-0000-000000000002', '40000000-0000-0000-0000-000000000001',
         'longitudCuerpoMm', 'Longitud del cuerpo (mm)', 'NUMERO', false,
         '{"minimo": 5, "maximo": 300, "unidad": "mm"}', true),
        ('50000000-0000-0000-0000-000000000003', '40000000-0000-0000-0000-000000000001',
         'habitat', 'Hábitat', 'SELECCION', false,
         '{"opciones": ["quebrada", "charca", "bosque húmedo", "hojarasca"]}', true),
        ('50000000-0000-0000-0000-000000000004', '40000000-0000-0000-0000-000000000001',
         'observaciones', 'Observaciones', 'TEXTO', false,
         '{"longitudMaxima": 500}', false),
        ('50000000-0000-0000-0000-000000000005', '40000000-0000-0000-0000-000000000002',
         'altitudMsnm', 'Altitud (msnm)', 'NUMERO', true,
         '{"minimo": 0, "maximo": 5000, "unidad": "msnm"}', true),
        ('50000000-0000-0000-0000-000000000006', '40000000-0000-0000-0000-000000000002',
         'numeroIndividuos', 'Número de individuos', 'NUMERO', true,
         '{"minimo": 1, "maximo": 500}', true),
        ('50000000-0000-0000-0000-000000000007', '40000000-0000-0000-0000-000000000002',
         'comportamiento', 'Comportamiento', 'SELECCION', false,
         '{"opciones": ["percha", "vuelo", "alimentación", "nidificación"]}', true),
        ('50000000-0000-0000-0000-000000000008', '40000000-0000-0000-0000-000000000002',
         'observaciones', 'Observaciones', 'TEXTO', false,
         '{"longitudMaxima": 500}', false)
    """,
]


def upgrade() -> None:
    for sentencia in TABLAS + PERMISOS + DATOS_DE_EJEMPLO:
        op.execute(sentencia)


def downgrade() -> None:
    # En orden inverso: primero las tablas que apuntan a otras.
    for tabla in (
        "auditoria",
        "ubicacion",
        "hallazgo",
        "definicion_atributo",
        "revision_ficha",
        "expedicion",
        "especie",
        "tipo_especie",
    ):
        op.execute(f"DROP TABLE campo.{tabla}")
