#!/bin/bash
# Carga los datos de demostración (db/demo/datos-demo.sql) en la base operacional.
#
# Corre una sola vez como el servicio "datos-demo" de docker-compose:
#   1. Espera a que Registro y Gobernanza creen sus tablas (sus migraciones corren al arrancar).
#   2. Carga los hallazgos de demostración. Si ya estaban, no duplica nada.
#   3. Espera a que lleguen por replicación a la BD Reportes, para que el reporte automático
#      del mes anterior (HU-15) se calcule con datos. Reportes arranca después de este paso.
set -euo pipefail

export PGUSER="$POSTGRES_USER" PGPASSWORD="$POSTGRES_PASSWORD" PGDATABASE="$POSTGRES_DB"
ESPERA_MAXIMA=300
TOTAL_DEMO=57

consultar() {
  psql -h "$1" -v ON_ERROR_STOP=1 -Atc "$2" 2>/dev/null || true
}

esperar() {
  local descripcion="$1" base="$2" sentencia="$3" esperado="$4" inicio=$SECONDS
  until [ "$(consultar "$base" "$sentencia")" = "$esperado" ]; do
    if (( SECONDS - inicio > ESPERA_MAXIMA )); then
      echo "datos-demo: no se cumplió a tiempo: $descripcion" >&2
      exit 1
    fi
    sleep 2
  done
  echo "datos-demo: $descripcion"
}

esperar "tablas de Registro y Gobernanza listas" bd-operacional \
  "SELECT to_regclass('campo.hallazgo') IS NOT NULL
      AND to_regclass('gobernanza.hallazgo_version') IS NOT NULL
      AND EXISTS (SELECT 1 FROM campo.expedicion WHERE id = '30000000-0000-0000-0000-000000000001')" t

psql -h bd-operacional -v ON_ERROR_STOP=1 -q -f /demo/datos-demo.sql
echo "datos-demo: hallazgos de demostración cargados"

esperar "copia en BD Reportes al día" bd-reportes \
  "SELECT count(*) FROM campo.hallazgo_publico WHERE hallazgo_id::text LIKE '60000000-%'" "$TOTAL_DEMO"
