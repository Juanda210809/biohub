#!/bin/bash
# BD Operacional: usuarios por servicio y un esquema por servicio.
# Se ejecuta UNA sola vez, cuando la base se crea por primera vez.
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS postgis;

    -- Un usuario de base de datos por servicio
    CREATE ROLE svc_registro   LOGIN PASSWORD '${REGISTRO_DB_PASSWORD}';
    CREATE ROLE svc_gobernanza LOGIN PASSWORD '${GOBERNANZA_DB_PASSWORD}';
    CREATE ROLE svc_identidad  LOGIN PASSWORD '${IDENTIDAD_DB_PASSWORD}';
    CREATE ROLE replicador WITH REPLICATION LOGIN PASSWORD '${REPLICADOR_PASSWORD}';

    -- Cada servicio es dueño de su esquema y solo ve lo suyo por defecto
    CREATE SCHEMA campo      AUTHORIZATION svc_registro;
    CREATE SCHEMA gobernanza AUTHORIZATION svc_gobernanza;
    CREATE SCHEMA identidad  AUTHORIZATION svc_identidad;

    ALTER ROLE svc_registro   SET search_path = campo, public;
    ALTER ROLE svc_gobernanza SET search_path = gobernanza, campo, public;
    ALTER ROLE svc_identidad  SET search_path = identidad, public;

    -- Gobernanza necesita leer el esquema campo (reclasificar hallazgos).
    -- Los permisos de tabla específicos (GRANT) se agregan en las migraciones.
    GRANT USAGE ON SCHEMA campo TO svc_gobernanza;
EOSQL
