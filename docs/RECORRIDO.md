# Recorrido de la base (jueves 5 → sábado 7 de noviembre)

Objetivo: que el lunes 9, cuando arranca el Sprint 1, cada uno sepa **qué hace cada archivo,
por qué está ahí y dónde va a escribir su código**. No hay que programar nada nuevo todavía.

Al terminar debes poder responder sin mirar:

- ¿Por dónde entra una petición del navegador y a qué contenedor llega?
- ¿En qué base de datos y en qué esquema viven los datos de tu servicio?
- ¿Cómo llega un hallazgo público desde la base operacional hasta la de consulta?
- ¿Qué tienes que hacer para que tu código llegue a `main`?

---

## Día 1 (jueves): levantar todo y entender el mapa

| # | Qué hacer | Para qué |
|---|---|---|
| 1 | Seguir `docs/GUIA-INICIO.md` hasta ver las 5 tarjetas verdes en http://localhost:5173 | Comprobar que tu PC está lista |
| 2 | Leer `README.md` (raíz) | Ver quién es dueño de cada carpeta |
| 3 | Abrir `docs/diagramas/componentes.png` y tenerlo a la vista todo el recorrido | Es el mapa: cada caja es un contenedor |
| 4 | Leer `docker-compose.yml` de arriba a abajo | Cada bloque `services:` es una caja del diagrama |
| 5 | Correr `docker compose ps` y ubicar los 11 contenedores en el diagrama | Relacionar archivo ↔ diagrama ↔ lo que corre |

Preguntas para anotar:

1. ¿Qué puerto abre Kong y por qué los servicios **no** abren puertos hacia afuera?
2. ¿Por qué hay tres bases de datos y no una?
3. ¿Qué significa `env_file: .env` y por qué `.env` no se sube a GitHub?

## Día 2 (viernes): seguir el camino de una petición

Recorre estos archivos **en este orden**; es el mismo camino que hace una petición real.

| # | Archivo | Qué mirar |
|---|---|---|
| 1 | `gateway/kong.yml` | Cada `routes:` manda `/api/v1/<servicio>` a un contenedor. Busca la ruta bloqueada de `identidad/interno` y la de la API externa con `key-auth` y `rate-limiting` |
| 2 | `servicios/registro/app/main.py` | Cómo arranca un servicio FastAPI y la ruta `/salud` |
| 3 | `servicios/registro/app/config.py` y `app/db.py` | De dónde sale la conexión a la base (variables del compose) |
| 4 | `servicios/registro/app/autorizacion.py` | Cómo un servicio le pregunta a Identidad si alguien puede hacer algo. Si Identidad falla, **niega** |
| 5 | `servicios/identidad/app/api/pdp.py` | El otro lado de esa pregunta (hoy siempre dice `DENEGAR`; HU-01/HU-02 lo vuelven real) |
| 6 | `db/operacional/01-roles-y-esquemas.sh` | Un usuario de base por servicio y un esquema por servicio |
| 7 | `db/operacional/02-tabla-publica.sh` | La tabla `campo.hallazgo_publico`, los permisos por columna y la publicación |
| 8 | `db/consulta/01-copia-y-suscripcion.sh` | La suscripción que copia esa tabla a la base de consulta |
| 9 | `servicios/consulta/app/cache.py` y `app/api/externa.py` | Redis y la API para universidades |
| 10 | `portal/src/api.js` y `portal/src/App.jsx` | Cómo el portal llama al gateway y pinta las tarjetas |

Prueba con tus manos (en PowerShell, con el proyecto corriendo):

```powershell
curl.exe http://localhost:8000/api/v1/registro/salud
curl.exe http://localhost:8000/api/v1/consulta/salud
curl.exe http://localhost:8000/api/v1/identidad/interno/autorizar   # debe dar 403: Kong lo bloquea
curl.exe -H "apikey: clave-demo-universidad" http://localhost:8000/externa/v1/hallazgos
```

Y abre la documentación automática de tu servicio: `http://localhost:8000/api/v1/<tu-servicio>/docs`.

## Día 3 (sábado): tu carpeta, tu historia y tu primer pull request

1. Lee `docs/COMO-TRABAJAR.md` completo (ramas, pull requests, migraciones).
2. Lee `.github/workflows/ci.yml` y `.github/pull_request_template.md`: es lo que GitHub revisa en cada PR.
3. Lee el `README.md` de **tu** servicio y tu sección de abajo.
4. Abre en Jira tus historias (filtro «Asignado a mí») y lee los criterios de aceptación.
5. Haz el **PR de práctica** (abajo).

---

## Qué le toca a cada uno

| Persona | Carpetas | Historias (Jira) | En el Sprint 1 |
|---|---|---|---|
| Juan David Guarnizo | `servicios/gobernanza`, `servicios/reportes` | HU-08, HU-12, HU-15 | HU-08 |
| Juan David Peña | `servicios/registro` | HU-03, HU-04, HU-21 | HU-03 |
| Ana María Luna | `servicios/consulta`, `portal` | HU-05, HU-06, HU-07 | HU-05, HU-06 |
| Nicolás Matheus | `servicios/identidad`, `pruebas` | HU-01, HU-02, HU-18, HU-20 | HU-01 |
| Nicolás Arias | `docker-compose.yml`, `gateway`, `db`, `.github` | HU-13, HU-14 | HU-13 |

### Peña · Registro
- Estudia a fondo: `servicios/registro/`, `migraciones/env.py`, `db/operacional/02-tabla-publica.sh`.
- Tu tabla principal (`campo.hallazgo`) la creas con una migración de Alembic, nunca a mano.
- Cada vez que guardes un hallazgo debes escribir también su fila en `campo.hallazgo_publico` **sin coordenadas**: de eso vive la consulta pública de Luna.
- Pregunta clave: ¿qué columnas de `hallazgo_publico` puede cambiar Gobernanza y cuáles no?

### Luna · Consulta y portal
- Estudia: `servicios/consulta/`, `db/consulta/`, `portal/src/`.
- Consulta **solo lee** (su usuario de base es de solo lectura). Los datos le llegan por replicación desde Registro.
- La ficha pública muestra región o departamento; las coordenadas (HU-07) solo salen si Identidad dice `PERMITIR`.
- Pregunta clave: si Registro inserta una fila nueva, ¿cuánto tarda en verse en `bd-consulta` y cómo lo compruebas?

### Matheus · Identidad y pruebas
- Estudia: `servicios/identidad/` (sobre todo `app/api/pdp.py` y `tests/test_pdp.py`), `app/autorizacion.py` de cualquier otro servicio, `pruebas/README.md`.
- Eres el «portero»: todos los servicios te preguntan antes de mostrar algo sensible. Si tu servicio falla, todos niegan.
- La ruta `/interno/...` no es accesible desde fuera (Kong la bloquea); solo la usan los otros contenedores.
- Pregunta clave: ¿qué recibe y qué devuelve `/interno/autorizar`, y qué pasa si tarda demasiado?

### Arias · Infraestructura y gateway
- Estudia: `docker-compose.yml`, `gateway/kong.yml`, todo `db/`, `.github/workflows/ci.yml`.
- Eres el revisor de cualquier cambio a contenedores, bases o CI.
- HU-13 y HU-14 viven casi enteras en `kong.yml`: rutas, `key-auth`, `rate-limiting` y consumidores.
- Pregunta clave: ¿cómo comprobarías que la petición número 61 dentro de un minuto se rechaza? (ver `pruebas/README.md`).

### Guarnizo · Gobernanza y reportes
- Estudia: `servicios/gobernanza/`, `servicios/reportes/`, `db/reportes/`.
- Gobernanza reclasifica sin borrar nunca la versión anterior; Reportes calcula sobre su propia copia de la base para no frenar el registro.

---

## PR de práctica (obligatorio antes del lunes)

Sirve para que todos hayan hecho el ciclo completo una vez **sin riesgo**.

```powershell
git checkout main
git pull
git checkout -b practica/tu-nombre
```

Crea el archivo `docs/equipo/tu-nombre.md` con:

1. Tus respuestas a las 4 preguntas del inicio de esta guía.
2. La respuesta a la «pregunta clave» de tu sección.
3. Una duda que te haya quedado (no vale «ninguna»).

```powershell
git add docs/equipo/tu-nombre.md
git commit -m "Practica: recorrido de tu-nombre"
git push -u origin practica/tu-nombre
```

En GitHub: **Compare & pull request** → llena la plantilla → crear. Espera el CI en verde y la
aprobación de Juan David → **Squash and merge** → **Delete branch**.

Las dudas de todos se resuelven en la reunión del lunes antes de empezar el sprint.

## Checklist del sábado en la noche

- [ ] El proyecto corre en mi PC y veo las 5 tarjetas verdes.
- [ ] Sé en qué carpeta voy a trabajar y qué no debo tocar.
- [ ] Leí mis historias en Jira y sus criterios de aceptación.
- [ ] Mi PR de práctica está fusionado en `main`.
- [ ] Acepté la invitación al repositorio en GitHub.
