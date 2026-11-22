# Portal Web

**Dueña:** Luna · React + Vite + Leaflet (mapas con OpenStreetMap)

Ábrelo en `http://localhost:5173` (no en `127.0.0.1`: Kong solo acepta ese origen por CORS).

## Estructura común

| Qué | Dónde |
|---|---|
| Páginas, rutas y qué rol ve cada una en el menú | `src/paginas.js` |
| Llamadas al backend por Kong (manda el token, maneja 401 y 403) | `src/api.js` → `pedir()` |
| Sesión (token y usuario en `sessionStorage`) | `src/sesion.js` y `src/SesionContexto.jsx` → `useSesion()` |
| Menú lateral, barra superior y pie | `src/componentes/Plantilla.jsx` |
| Iniciar sesión (HU-01, base) | `src/paginas/entrar/Entrar.jsx` |
| Navegación por hash (`#/registro`) | `src/navegacion.js` |

- Las rutas son `#/consulta`, `#/registro`, `#/fichas`, `#/mapa`, `#/reclasificar`, `#/historial`, `#/indices`, `#/usuarios` y `#/entrar`.
- Una página interna sin sesión lleva a iniciar sesión y, al entrar, vuelve a ella si el rol la puede ver.
- Si Identidad rechaza el token (401), la sesión se borra y se vuelve a iniciar sesión con un aviso.
- El menú según el rol es solo comodidad: lo que protege los datos es el PDP, que cada servicio consulta con el token.

## Cómo hacer tu pantalla

1. Tu página ya existe como espacio reservado en `src/paginas/<parte>/`: reemplaza su contenido.
2. Para llamar al backend usa `pedir('/api/v1/<servicio>/...')`, o agrega una función en `src/api.js`.
3. Si necesitas el usuario o su rol: `const { usuario } = useSesion()`.
4. No hace falta tocar `App.jsx`, `Plantilla.jsx` ni el menú. Para una página nueva, súmala en `src/paginas.js`.

| Página | Archivo | Responsable |
|---|---|---|
| Consulta pública (HU-05/06) | `paginas/consulta/ConsultaPublica.jsx` | Luna |
| Ver en el mapa (HU-07) | `paginas/mapa/UbicacionHallazgo.jsx` | Luna |
| Iniciar sesión (HU-01) | `paginas/entrar/Entrar.jsx` | Matheus |
| Usuarios y roles (HU-02, HU-18) | `paginas/usuarios/GestionUsuarios.jsx` | Matheus |
| Registrar hallazgo (HU-03) | `paginas/registro/RegistrarHallazgo.jsx` | Peña |
| Definir fichas (HU-04) | `paginas/fichas/DefinirFicha.jsx` | Peña |
| Reclasificar (HU-08) | `paginas/reclasificar/Reclasificar.jsx` | Guarnizo |
| Historial y versiones (HU-12) | `paginas/historial/Historial.jsx` | Guarnizo |
| Índices de presión (HU-15) | `paginas/indices/IndicesPresion.jsx` | Guarnizo |

Usuarios de prueba: `investigador@`, `cientifico@`, `altorango@`, `auditor@`, `admin@` y `sinrol@biohub.local`, todos con `BioHub2026!`.

## Comandos

- `npm run dev`: abre el portal en http://localhost:5173 (también lo levanta `docker compose up`).
- `npm test`: pruebas de la estructura común (Vitest).
- `npm run lint` y `npm run build`: lo mismo que revisa el CI.
- Consulta con datos ficticios: `VITE_MODO_DEMO=true npm run dev` (muestra un aviso de que no son registros reales).
