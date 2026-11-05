#!/bin/bash
# Un hallazgo de ejemplo para comprobar que la replicación funciona:
# debe aparecer también en BD Consulta y BD Reportes.
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    INSERT INTO campo.hallazgo_publico
        (hallazgo_id, especie, region, departamento, ecosistema, fecha_hallazgo)
    VALUES
        ('00000000-0000-0000-0000-000000000001', 'Especie de prueba',
         'Amazonía', 'Amazonas', 'Bosque húmedo', '2026-01-10');
EOSQL
