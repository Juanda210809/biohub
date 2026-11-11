# Recorrido · Nicolás Matheus (Identidad y pruebas)

## Las 4 preguntas del recorrido

**1. ¿Por dónde entra una petición del navegador y a qué contenedor llega?**
Todo entra por Kong en el puerto 8000. En `gateway/kong.yml` cada ruta `/api/v1/<servicio>`
apunta al contenedor `<servicio>:8000` y Kong quita el prefijo (`strip_path`), así que el
servicio recibe `/salud`, `/docs`, etc. Los servicios no publican puertos hacia afuera, por eso
Kong es la única puerta. El portal (5173) solo sirve las pantallas; las llamadas van a Kong.

**2. ¿En qué base de datos y en qué esquema viven los datos de tu servicio?**
En la BD Operacional (`bd-operacional`, PostgreSQL + PostGIS), en el esquema `identidad`.
El servicio se conecta con su propio usuario `svc_identidad`, dueño de ese esquema
(`db/operacional/01-roles-y-esquemas.sh`). Las tablas se crean con migraciones de Alembic.

**3. ¿Cómo llega un hallazgo público desde la base operacional hasta la de consulta?**
Registro escribe el resumen sin coordenadas en `campo.hallazgo_publico` en la misma transacción
del hallazgo. Esa tabla está en la publicación `pub_hallazgo_publico` (`02-tabla-publica.sh`), y
BD Consulta y BD Reportes tienen una suscripción (`sub_consulta`, `sub_reportes`) que la copia
sola por replicación lógica, usando el usuario `replicador`, que solo puede leer esa tabla.
Las coordenadas (`campo.ubicacion`) nunca salen de la BD Operacional.

**4. ¿Qué tienes que hacer para que tu código llegue a `main`?**
Crear una rama `feature/SCRUM-NN-...` desde `main`, hacer commits, subirla con `git push`,
abrir un pull request con la plantilla, esperar el CI en verde (ruff, pytest, lint y build del
portal, construcción de contenedores) y una aprobación del dueño (CODEOWNERS). Luego
Squash and merge, borrar la rama y mover la historia a Listo en Jira.

## Pregunta clave de mi sección

**¿Qué recibe y qué devuelve `/interno/autorizar`, y qué pasa si tarda demasiado?**
Recibe `{"token", "accion", "recurso"}` y devuelve `{"decision": "PERMITIR" | "DENEGAR",
"motivo"}`. Los servicios lo llaman desde `app/autorizacion.py` con un tiempo máximo de 2 s.
Si el PDP no responde a tiempo, falla o no devuelve 200, el cliente toma la decisión como
DENEGAR (falla segura). Desde afuera Kong bloquea `/api/v1/identidad/interno` con 403.

## Mi duda

HU-20 (ficha rápida bajo pico) está asignada a mí, pero la caché con el patrón Decorator
(`ConsultaCacheada`) va en `servicios/consulta/app/cache.py`, que es la carpeta de Luna.
¿Quién implementa la caché? Mi propuesta: Luna hace la caché dentro de HU-05; yo hago que el
PDP decida en memoria para el visitante sin sesión y escribo la prueba de carga a 60× en `pruebas/`.
