import { test, expect } from '@playwright/test'
import { entrar, salir } from './ayudas.js'

test('Sin sesión, el registro pide entrar y conserva el destino', async ({ page }) => {
  await page.goto('/#/registro')
  await expect(page).toHaveURL(/#\/entrar\?volver=\/registro$/)
  await expect(page.getByRole('button', { name: 'Entrar', exact: true })).toBeVisible()
})

test('Una contraseña incorrecta muestra el error genérico y no inicia sesión', async ({ page }) => {
  await page.goto('/#/entrar')
  await page.locator('input[name="correo"]').fill('investigador@biohub.local')
  await page.locator('input[name="contrasena"]').fill('Incorrecta2026!')
  await page.getByRole('button', { name: 'Entrar', exact: true }).click()
  await expect(page.getByRole('alert')).toHaveText('Correo o contraseña incorrectos. Si el problema sigue, pide al administrador que revise tu cuenta.')
  await expect(page).toHaveURL(/#\/entrar$/)
  await expect(page.getByText('SESIÓN INICIADA', { exact: true })).toHaveCount(0)
})

const menus = {
  investigador: ['Registrar hallazgo', 'Ver en el mapa'],
  cientifico: ['Definir fichas', 'Ver en el mapa', 'Reclasificar hallazgo'],
  altorango: ['Ver en el mapa', 'Índices de presión'],
  auditor: ['Ver en el mapa', 'Historial y versiones'],
  admin: ['Ver en el mapa', 'Usuarios y roles'],
  sinrol: [],
}

for (const [usuario, enlaces] of Object.entries(menus)) {
  test(`${usuario} ve exactamente los enlaces de su rol y la consulta pública`, async ({ page }) => {
    await entrar(page, usuario)
    const menu = page.getByRole('navigation', { name: 'Menú principal' })
    await expect(menu.getByRole('link')).toHaveCount(enlaces.length + 1)
    for (const nombre of ['Consulta pública', ...enlaces]) {
      await expect(menu.getByRole('link', { name: nombre, exact: true })).toBeVisible()
    }
  })
}

test('El investigador no puede abrir Usuarios y roles', async ({ page }) => {
  await entrar(page, 'investigador')
  await page.goto('/#/usuarios')
  await expect(page.getByRole('alert')).toContainText('No tienes permiso para esta pantalla')
})

test('Cerrar sesión vuelve a la consulta pública y quita los enlaces internos', async ({ page }) => {
  await entrar(page, 'investigador')
  await page.goto('/#/registro')
  await salir(page)
  const menu = page.getByRole('navigation', { name: 'Menú principal' })
  await expect(menu.getByRole('link')).toHaveCount(1)
  await expect(menu.getByRole('link', { name: 'Consulta pública', exact: true })).toBeVisible()
  await expect(page.getByText('SESIÓN INICIADA', { exact: true })).toHaveCount(0)
})
