import { test, expect } from '@playwright/test'
import { entrar } from './ayudas.js'

// Escoge el primer hallazgo de Cauca de la lista (todos tienen coordenadas en los datos demo)
// y devuelve lo que respondió el servicio de ubicación para ese hallazgo.
async function seleccionarHallazgoDeCauca(page) {
  await page.goto('/#/mapa')
  const boton = page.locator('.mapa-detalle-lista').getByRole('button').filter({ hasText: 'Cauca' }).first()
  await expect(boton).toBeVisible()
  const ubicacion = page.waitForResponse((respuesta) =>
    /\/api\/v1\/registro\/hallazgos\/[^/]+\/ubicacion$/.test(new URL(respuesta.url()).pathname)
    && respuesta.request().method() === 'GET'
  )
  await boton.click()
  const respuesta = await ubicacion
  expect(respuesta.ok()).toBeTruthy()
  return await respuesta.json()
}

test('Alto rango ve la ubicación exacta y un único marcador de un hallazgo de Cauca', async ({ page }) => {
  await entrar(page, 'altorango')
  const ubicacion = await seleccionarHallazgoDeCauca(page)
  expect(ubicacion.nivelUbicacion).toBe('EXACTA')
  await expect(page.locator('.mapa-especies').getByText('Ubicación exacta autorizada', { exact: true })).toBeVisible()
  await expect(page.locator('.leaflet-marker-icon')).toHaveCount(1)
})

test.describe('La ubicación general protege las coordenadas exactas', () => {
  for (const usuario of ['investigador', 'cientifico', 'auditor', 'admin']) {
    test(`${usuario} ve región y departamento sin marcadores ni coordenadas exactas`, async ({ page }) => {
      await entrar(page, usuario)
      const ubicacion = await seleccionarHallazgoDeCauca(page)
      expect(ubicacion.nivelUbicacion).toBe('REGION')
      expect(ubicacion).not.toHaveProperty('latitud')
      expect(ubicacion).not.toHaveProperty('longitud')
      const panel = page.locator('.mapa-especies')
      await expect(panel.getByText('Ubicación general autorizada', { exact: true })).toBeVisible()
      await expect(panel.getByText('Región: Pacífico', { exact: true })).toBeVisible()
      await expect(panel.getByText('Departamento: Cauca', { exact: true })).toBeVisible()
      await expect(panel.getByText('No se muestran coordenadas exactas para este nivel de autorización.', { exact: true })).toBeVisible()
      await expect(page.locator('.leaflet-marker-icon')).toHaveCount(0)
      await expect(page.locator('body')).not.toContainText(/-?\b\d{1,3}[.,]\d{4,}\b/)
    })
  }
})

test('Sin rol no aparece el mapa en el menú y se rechaza el acceso directo', async ({ page }) => {
  await entrar(page, 'sinrol')
  const menu = page.getByRole('navigation', { name: 'Menú principal' })
  await expect(menu.getByRole('link', { name: 'Ver en el mapa', exact: true })).toHaveCount(0)
  await page.goto('/#/mapa')
  await expect(page.getByRole('alert')).toContainText('No tienes permiso para esta pantalla')
})

test('Sin sesión, el mapa pide entrar y conserva el destino', async ({ page }) => {
  await page.goto('/#/mapa')
  await expect(page).toHaveURL(/#\/entrar\?volver=\/mapa$/)
  await expect(page.getByRole('button', { name: 'Entrar', exact: true })).toBeVisible()
})
