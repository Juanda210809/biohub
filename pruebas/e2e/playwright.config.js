// Pruebas de punta a punta del portal (SCRUM-47). Corren contra el sistema levantado:
//   docker compose down -v && docker compose up --build -d --wait   (desde la raíz del repo)
//   cd pruebas/e2e && npm ci && npx playwright install chromium && npm test
// Usan los usuarios demo y los datos de demostración (db/demo/).
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './pruebas',
  // Un solo navegador a la vez: las pruebas comparten la misma base de datos.
  workers: 1,
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  timeout: 60_000,
  expect: { timeout: 10_000 },
  outputDir: 'salida/resultados',
  reporter: [['list'], ['html', { outputFolder: 'salida/reporte', open: 'never' }]],
  use: {
    // Siempre localhost: Kong solo acepta ese origen por CORS.
    baseURL: process.env.PORTAL_URL || 'http://localhost:5173',
    locale: 'es-CO',
    timezoneId: 'America/Bogota',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
})
