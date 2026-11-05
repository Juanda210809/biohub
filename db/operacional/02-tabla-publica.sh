#!/bin/bash
# Tabla hallazgo_publico: el resumen SIN coordenadas de cada hallazgo.
# Es la única tabla que se copia (replicación lógica) a BD Consulta y BD Reportes.
# Su estructura debe ser IDÉNTICA en las 3 bases (ver db/consulta y db/reportes).
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE TABLE campo.hallazgo_publico (
        hallazgo_id        UUID PRIMARY KEY,
        especie            TEXT NOT NULL,
        region             TEXT,
        departamento       TEXT,
        ecosistema         TEXT,
        fecha_hallazgo     DATE,
        atributos_publicos JSONB NOT NULL DEFAULT '{}'::jsonb,
        version            INTEGER NOT NULL DEFAULT 1,
        actualizado_en     TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    ALTER TABLE campo.hallazgo_publico OWNER TO svc_registro;

    -- Gobernanza solo puede cambiar la especie, la versión y los atributos (reclasificación)
    GRANT SELECT ON campo.hallazgo_publico TO svc_gobernanza;
    GRANT UPDATE (especie, version, atributos_publicos, actualizado_en)
        ON campo.hallazgo_publico TO svc_gobernanza;

    -- El replicador solo puede leer esta tabla
    GRANT USAGE ON SCHEMA campo TO replicador;
    GRANT SELECT ON campo.hallazgo_publico TO replicador;

    -- Publicación: lo que se copia hacia las otras dos bases
    CREATE PUBLICATION pub_hallazgo_publico FOR TABLE campo.hallazgo_publico;
EOSQL
