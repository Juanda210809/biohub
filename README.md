# BioHub

Sistema Nacional de Registro y Vigilancia de Biodiversidad · Ingeniería de Software 2.
Arquitectura basada en servicios: Kong como única puerta, 5 servicios FastAPI,
PostgreSQL con replicación lógica, Redis y un portal en React.

## Levantar todo en 3 pasos

```bash
git clone https://github.com/<organizacion>/biohub.git
cd biohub
cp .env.example .env            # en PowerShell: Copy-Item .env.example .env
docker compose up --build
```

La primera vez tarda varios minutos (descarga imágenes). Cuando termine:

| Qué | Dónde |
|---|---|
| Portal (estado del sistema) | http://localhost:5173 |
| Kong, la única puerta | http://localhost:8000 |
| Documentación de cada servicio | http://localhost:8000/api/v1/registro/docs (cambia `registro` por `gobernanza`, `identidad`, `consulta` o `reportes`) |

Si las 5 tarjetas del portal están en verde, todo está conectado.

## Estructura

| Carpeta | Qué hay | Responsable |
|---|---|---|
| `servicios/registro` | Registro y Gestión de Campo | Peña |
| `servicios/gobernanza` | Gobernanza Científica | Guarnizo |
| `servicios/reportes` | Reportes y Analítica | Guarnizo |
| `servicios/identidad` | Identidad y Autorización (incluye el PDP) | Matheus |
| `servicios/consulta` | Consulta Pública (y API externa) | Luna |
| `portal` | Portal Web (pantallas) | Luna |
| `gateway`, `db`, `docker-compose.yml`, `.github` | Kong, bases de datos, contenedores y CI | Arias |
| `pruebas` | Pruebas de aceptación del MVP | Matheus |
| `docs` | Guías y diagramas de la arquitectura | Todos |

## Guías

- [Primeros pasos](docs/GUIA-INICIO.md): instalar, levantar el proyecto y qué hacer si algo falla.
- [Cómo trabajamos](docs/COMO-TRABAJAR.md): ramas, commits, pull requests, tablas y permisos.
