# Infraestructura local y pruebas

## Acceso de desarrollo

Las bases se publican solamente en la interfaz local del PC:

- Operacional: 127.0.0.1:5442.
- Consulta: 127.0.0.1:5443.
- Reportes: 127.0.0.1:5444.

Los servicios siguen usando los nombres Docker bd-operacional, bd-consulta y bd-reportes en el puerto 5432. No deben cambiar a localhost dentro de sus contenedores. Redis y los cinco servicios no publican puertos en el host. La API administrativa de Kong tampoco se publica.

Esta restriccion impide exponer los puertos SQL en todas las interfaces del host; no constituye aislamiento entre todos los contenedores, que siguen compartiendo la red de Compose. El despliegue local usa HTTP; TLS y el dominio publico requieren configurar el entorno de despliegue.

## Pruebas

Desde la raiz del repo, con Docker Desktop activo:

    python -m pip install -r gateway/requirements-test.txt ruff
    python -m pytest gateway/tests db/tests -q -W error
    ruff check gateway/tests db/tests

Las pruebas de db/tests construyen y levantan los 11 contenedores actuales en un proyecto Compose con nombre unico. Usan .env.example, puertos temporales y volumenes propios, que se eliminan al terminar. No usan la base de desarrollo ni requieren crear .env.

Se verifica la configuracion y la publicacion real de los puertos SQL, conexiones de los servicios, replicacion de una fila nueva a ambas copias, rechazo de escritura con svc_consulta, Redis, portal y entrada por Kong. La respuesta externa actual sigue siendo un marcador: el 200 demuestra conectividad, no que el inventario real este implementado o libre de coordenadas.

Si Docker no esta disponible, las pruebas de integracion fallan explicitamente. El CI ejecuta las pruebas del gateway y las de infraestructura en trabajos separados.

## Integracion con main del 13 de noviembre

Se incorporaron las migraciones de Gobernanza y el registro de hallazgos de main.
Se agregaron dos pruebas: el caso de uso real de Registro guarda hallazgo, ubicacion,
version inicial y auditoria, y replica solo datos publicos; por HTTP, una solicitud
sin credencial o con token invalido es rechazada sin insertar hallazgos.

La prueba de guardado ejecuta el caso de uso dentro del contenedor, con SQL real.
No sustituye una prueba HTTP autorizada: el PDP de main todavia deniega todo.
El listado externo de Consulta sigue siendo provisional.

## Fallos de transaccion y permisos SQL

La integracion inyecta un error en la ultima escritura (auditoria) dentro de la base
exclusiva de pruebas. Comprueba que las cinco tablas conserven sus cantidades y que
las replicas coincidan con operacional despues de un commit posterior replicado.
El trigger temporal se elimina en finally. No se modifica la base de desarrollo.

Se prueban 17 operaciones prohibidas para Consulta, Reportes, Registro, Gobernanza,
Identidad y el replicador. Se exige SQLSTATE 42501 (permiso insuficiente), no cualquier
error. La transaccion se abre READ WRITE para verificar los permisos de tabla aun
cuando el usuario tenga solo lectura por defecto; no se alteran sus permisos.
Todas las operaciones se revierten incluso si una autorizacion inesperada las permite.

Las pruebas unitarias de servicios/registro/tests/test_transaccion_repositorio.py
cubren fallos en cada una de las cinco escrituras, en commit y la confirmacion exitosa.
Estas pruebas no demuestran aislamiento frente a un usuario propietario malicioso
que cambie sus propios permisos o el esquema; verifican las operaciones SQL indicadas.
