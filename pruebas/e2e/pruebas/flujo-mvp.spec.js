import { test, expect } from '@playwright/test'
import { entrar, marcaUnica } from './ayudas.js'

test.describe.serial('Flujo completo de un hallazgo', () => {
  let marca
  let fecha
  let justificacion

  test('El investigador registra una rana dorada con su ficha obligatoria', async ({ page }) => {
    marca = marcaUnica()
    justificacion = `Revisión de las grabaciones de campo para ${marca}.`
    await entrar(page, 'investigador')
    await page.goto('/#/registro')
    const especie = page.getByLabel(/^Especie/)
    await especie.selectOption(await especie.getByRole('option', { name: /Phyllobates terribilis/ }).getAttribute('value'))
    await page.getByLabel(/^Expedición/).selectOption({ label: 'Expedición Pacífico Cauca 2026' })
    fecha = await page.getByLabel(/^Fecha del hallazgo/).inputValue()
    await page.getByLabel(/^Latitud/).fill('2.512345')
    await page.getByLabel(/^Longitud(?! del)/).fill('-77.123456')
    await page.getByLabel(/^Región/).fill('Pacífico')
    await page.getByLabel('Departamento', { exact: true }).fill('Cauca')
    await page.getByLabel('Ecosistema', { exact: true }).fill(marca)
    await page.getByLabel(/^Temperatura del agua/).fill('22')
    await page.getByRole('button', { name: 'Registrar hallazgo', exact: true }).click()
    await expect(page.getByRole('status')).toContainText('Hallazgo registrado')
  })

  test('El visitante encuentra la ficha sin coordenadas exactas en toda la página', async ({ page }) => {
    test.setTimeout(180_000)
    const tarjeta = page.locator('.tarjeta-hallazgo').filter({ hasText: marca })
    // La búsqueda es local a cada página; la réplica puede tardar en aparecer.
    await expect(async () => {
      await page.goto('/#/consulta')
      await page.reload()
      await page.getByLabel('Buscar registros de biodiversidad').fill(marca)
      await expect(page.locator('.skeleton')).toHaveCount(0)
      while (!(await tarjeta.count())) {
        const siguiente = page.getByRole('button', { name: 'Siguiente →', exact: true })
        if (!(await siguiente.isVisible()) || !(await siguiente.isEnabled())) break
        const respuesta = page.waitForResponse((r) => r.url().includes('/api/v1/consulta/hallazgos?') && r.request().method() === 'GET')
        await siguiente.click()
        await respuesta
        await expect(page.locator('.skeleton')).toHaveCount(0)
      }
      await expect(tarjeta).toBeVisible()
    }).toPass({ timeout: 120_000, intervals: [1000, 2000, 5000] })
    await expect(page.getByRole('link', { name: 'Iniciar sesión', exact: true })).toBeVisible()
    const ficha = page.waitForResponse((r) => /\/api\/v1\/consulta\/hallazgos\/[^/?]+$/.test(r.url()) && r.request().method() === 'GET')
    await tarjeta.click()
    expect((await ficha).ok()).toBeTruthy()
    await expect(page.getByText('Cargando ficha pública…', { exact: true })).toHaveCount(0)
    await expect(page.getByText('No fue posible cargar el detalle.', { exact: true })).toHaveCount(0)
    await expect(page.getByRole('heading', { name: 'Phyllobates terribilis', exact: true })).toBeVisible()
    await expect(page.getByText('Cauca', { exact: true })).toBeVisible()
    await expect(page.getByText('Pacífico', { exact: true })).toBeVisible()
    await expect(page.locator('body')).not.toContainText('2.512345')
    await expect(page.locator('body')).not.toContainText('77.123456')
    await expect(page.locator('body')).not.toContainText(/\blatitud\b/i)
  })

  test('El científico reclasifica el hallazgo y crea la versión dos', async ({ page }) => {
    await entrar(page, 'cientifico')
    await page.goto('/#/reclasificar')
    await page.getByRole('searchbox', { name: 'Buscar hallazgo' }).fill(marca)
    await page.getByRole('list', { name: 'Hallazgos', exact: true }).getByRole('button').filter({ hasText: marca }).click()
    const especie = page.getByLabel('Especie correcta')
    await expect(especie).toBeEnabled()
    await especie.selectOption(await especie.getByRole('option', { name: /Setophaga cerulea/ }).getAttribute('value'))
    await page.getByLabel('Justificación').fill(justificacion)
    await page.getByRole('button', { name: 'Reclasificar', exact: true }).click()
    await expect(page.getByRole('status')).toContainText('Reclasificación guardada como versión 2')
  })

  test('El auditor reconstruye hoy y ve la especie vigente con su justificación', async ({ page }) => {
    await entrar(page, 'auditor')
    await page.goto('/#/historial')
    await page.getByRole('searchbox', { name: 'Buscar hallazgo' }).fill(marca)
    await page.getByRole('list', { name: 'Hallazgos', exact: true }).getByRole('button').filter({ hasText: marca }).click()
    const hoy = await page.getByLabel('Fecha', { exact: true }).getAttribute('max')
    await page.getByLabel('Fecha', { exact: true }).fill(hoy)
    await page.getByRole('button', { name: 'Reconstruir', exact: true }).click()
    const vigente = page.getByRole('article').filter({ hasText: 'HOY · VERSIÓN 2' })
    await expect(vigente).toContainText('Setophaga cerulea')
    await expect(vigente).toContainText(justificacion)
    await expect(page.getByRole('heading', { name: 'Esa sigue siendo la versión vigente' })).toBeVisible()
  })

  test('Alto rango genera o recalcula el mes actual y encuentra el ecosistema', async ({ page }) => {
    test.setTimeout(180_000)
    await entrar(page, 'altorango')
    await page.goto('/#/indices')
    await page.getByLabel('Mes', { exact: true }).fill(fecha.slice(0, 7))
    await expect(page.getByText(/^Cargando índices de/)).toHaveCount(0)
    // Recalcular permite incorporar la réplica en Reportes cuando ya había un informe.
    await expect(async () => {
      const generar = page.getByRole('button', { name: /^(Generar índices|Recalcular)$/ })
      await expect(generar).toBeEnabled()
      await generar.click()
      await expect(page.getByRole('button', { name: 'Recalcular', exact: true })).toBeEnabled()
      await expect(page.getByRole('row').filter({ has: page.getByRole('rowheader', { name: marca, exact: true }) })).toBeVisible()
    }).toPass({ timeout: 120_000, intervals: [1000, 2000, 5000] })
  })
})
