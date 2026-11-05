#!/bin/bash
# BD Consulta: copia de hallazgo_publico (sin coordenadas) para la consulta pública.
# 1) crea la misma tabla, 2) crea el usuario de solo lectura, 3) se suscribe.
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

    CREATE ROLE svc_consulta LOGIN PASSWORD '${CONSULTA_DB_PASSWORD}';
    GRANT USAGE ON SCHEMA campo TO svc_consulta;
    GRANT SELECT ON campo.hallazgo_publico TO svc_consulta;
    ALTER ROLE svc_consulta SET search_path = campo, public;
    ALTER ROLE svc_consulta SET default_transaction_read_only = on;
EOSQL

# La suscripción va aparte: no puede crearse dentro de una transacción.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -c \
  "CREATE SUBSCRIPTION sub_consulta
     CONNECTION 'host=bd-operacional port=5432 dbname=${POSTGRES_DB} user=replicador password=${REPLICADOR_PASSWORD}'
     PUBLICATION pub_hallazgo_publico;"
