# Recorrido de Peña · Registro y Gestión de Campo

## 1. ¿Por dónde entra una petición del navegador y a qué contenedor llega?
Entra por Kong (localhost:8000), que es la única puerta de entrada: es el único contenedor
de servicios con puerto publicado hacia afuera (8000:8000). Kong mira la ruta
(/api/v1/<servicio>), quita el prefijo (strip_path) y manda la petición por la red interna
de Docker al contenedor del servicio (por ejemplo registro:8000). Los servicios no
publican puertos, así que nadie los alcanza sin pasar por Kong.

## 2. ¿En qué base y esquema viven los datos de mi servicio?
En la BD Operacional (contenedor bd-operacional, PostgreSQL + PostGIS), en el esquema
`campo`. Mi usuario de base de datos es svc_registro, dueño de ese esquema. Mis tablas
las creo con migraciones de Alembic. La tabla campo.hallazgo_publico ya existe.

## 3. ¿Cómo llega un hallazgo público desde la BD Operacional hasta la de Consulta?
Registro escribe la fila en campo.hallazgo_publico (sin coordenadas) al guardar el
hallazgo. La publicación pub_hallazgo_publico (la base corre con wal_level=logical) comparte
esa tabla. En bd-consulta existe una suscripción (sub_consulta) que se conecta con el
usuario replicador, de solo lectura, y copia la tabla y cada cambio automáticamente. Se
comprueba con "filas_hallazgo_publico" en /api/v1/consulta/salud o con un cliente SQL
en localhost:5443.

## 4. ¿Qué tengo que hacer para que mi código llegue a main?
Crear una rama desde main actualizado (feature/SCRUM-15-registrar-hallazgo), hacer commits
con la clave de Jira, subir la rama con git push y abrir un pull request llenando la
plantilla. Debe pasar el CI (ruff y pytest) y tener una aprobación del dueño de la carpeta.
Luego Squash and merge, Delete branch y mover la historia a Listo en Jira si cumple la
definición de terminado. Nadie sube directo a main.

## Pregunta clave: ¿qué columnas de hallazgo_publico puede cambiar Gobernanza y cuáles no?
Gobernanza puede leer toda la tabla (SELECT), pero solo puede hacer UPDATE de especie,
version, atributos_publicos y actualizado_en. No puede cambiar hallazgo_id, region,
departamento, ecosistema ni fecha_hallazgo: esas son de Registro. Tiene sentido porque
reclasificar cambia qué especie es el hallazgo, no dónde ni cuándo se encontró.

## Mi duda
HU-03 pide guardar el hallazgo como versión inicial de su historial. Según la arquitectura,
esa versión va en hallazgo_version, que pertenece al esquema de Gobernanza, dentro de la
misma transacción. Pero en db/operacional/01-roles-y-esquemas.sh svc_registro no tiene
permisos sobre ese esquema. ¿Quién crea esa tabla y da los permisos (GRANT)? ¿Y en qué
orden, si Registro y Gobernanza aplican sus migraciones al arrancar?
