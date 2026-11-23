# Pruebas de punta a punta del portal

Recorren el portal en un navegador real (Playwright + Chromium), como lo haría cada rol, contra el sistema completo levantado con `docker compose`. Las corre el CI en cada PR ("Pruebas de punta a punta del portal").

| Archivo | Qué prueba |
|---|---|
| `pruebas/sesion.spec.js` | Iniciar sesión, contraseña incorrecta, menú exacto de cada rol, "sin permiso" y cerrar sesión |
| `pruebas/flujo-mvp.spec.js` | El flujo completo, en orden: el investigador registra un hallazgo con coordenadas → el visitante lo ve sin coordenadas → el científico lo reclasifica → el auditor ve el historial → alto rango genera los índices del mes |
| `pruebas/usuarios.spec.js` | El administrador crea una cuenta, le cambia el rol (cambia su menú), la desactiva (ya no entra) y no puede cambiarse su propio rol |
| `pruebas/datos-demo.spec.js` | Con los datos de `db/demo/`: índices de octubre con niveles alto, normal y bajo, e historial con el antes y el después |
| `pruebas/mapa.spec.js` | HU-07: alto rango ve el marcador en el punto exacto; investigador, científico, auditor y admin ven solo región y departamento, sin marcador ni coordenadas; sin rol no tiene acceso y sin sesión pide entrar |

## Cómo correrlas

Desde la raíz del repo:

```bash
docker compose down -v && docker compose up --build -d --wait
cd pruebas/e2e
npm ci
npx playwright install chromium
npm test
```

Si algo falla, `npm run reporte` abre el reporte con capturas y el paso a paso. Se guarda en `salida/`, que no se sube.

## Ojo antes de la demo

Cada corrida **deja hallazgos de prueba** en la base (con ecosistema "Prueba …"), que aparecen en la consulta y en los índices. Antes de presentar, vuelve a crear las bases con `docker compose down -v` y `docker compose up --build`.
