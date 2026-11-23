import { test, expect } from '@playwright/test'
import { entrar } from './ayudas.js'

test('Octubre de 2026 muestra presión alta en bosque, normal en páramo y baja en manglar', async ({ page }) => {
  await entrar(page, 'altorango')
  await page.goto('/#/indices')
  await page.getByLabel('Mes', { exact: true }).fill('2026-10')
  const tabla = page.getByRole('table', { name: 'Índices de presión por ecosistema, octubre de 2026' })
  await expect(tabla).toBeVisible()
  for (const [ecosistema, nivel] of [['Bosque húmedo', 'Alta'], ['Páramo', 'Normal'], ['Manglar', 'Baja']]) {
    const fila = tabla.getByRole('row').filter({ has: page.getByRole('rowheader', { name: ecosistema, exact: true }) })
    await expect(fila.getByRole('cell', { name: nivel, exact: true })).toBeVisible()
  }
})

test('El manglar del 14 de agosto era reinita en septiembre y ahora es azulejo', async ({ page }) => {
  await entrar(page, 'auditor')
  await page.goto('/#/historial')
  await page.getByRole('searchbox', { name: 'Buscar hallazgo' }).fill('Manglar')
  const hallazgo = page.getByRole('list', { name: 'Hallazgos', exact: true }).getByRole('button')
    .filter({ hasText: 'Manglar' }).filter({ hasText: /14 de ago\.? de 2026 · versión 2/ })
  await expect(hallazgo).toHaveCount(1)
  await hallazgo.click()
  await page.getByLabel('Fecha', { exact: true }).fill('2026-09-01')
  await page.getByRole('button', { name: 'Reconstruir', exact: true }).click()
  await expect(page.getByRole('article').filter({ hasText: /EL .* · VERSIÓN 1/ })).toContainText('Setophaga cerulea')
  await expect(page.getByRole('article').filter({ hasText: 'HOY · VERSIÓN 2' })).toContainText('Thraupis episcopus')
  const cambio = page.getByRole('row').filter({ has: page.getByRole('rowheader', { name: 'Especie', exact: true }) })
  await expect(cambio.getByRole('cell')).toHaveText(['Setophaga cerulea', 'Thraupis episcopus'])
})
