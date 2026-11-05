#!/bin/bash
# BD Reportes: copia de hallazgo_publico + esquema propio para los resultados de los reportes.
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE SCHEMA campo;
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

    CREATE ROLE svc_reportes LOGIN PASSWORD '${REPORTES_DB_PASSWORD}';
    GRANT USAGE ON SCHEMA campo TO svc_reportes;
    GRANT SELECT ON campo.hallazgo_publico TO svc_reportes;

    -- Aquí guarda Reportes sus resultados (reportes e índices de presión)
    CREATE SCHEMA reportes AUTHORIZATION svc_reportes;
    ALTER ROLE svc_reportes SET search_path = reportes, campo, public;
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -c \
  "CREATE SUBSCRIPTION sub_reportes
     CONNECTION 'host=bd-operacional port=5432 dbname=${POSTGRES_DB} user=replicador password=${REPLICADOR_PASSWORD}'
     PUBLICATION pub_hallazgo_publico;"
