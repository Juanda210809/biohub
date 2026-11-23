import { test, expect } from '@playwright/test'
import { entrar, salir, marcaUnica } from './ayudas.js'

test('El administrador crea un investigador, lo cambia a auditor y desactiva la cuenta', async ({ page }) => {
  const nombre = marcaUnica()
  const correo = `${nombre.toLowerCase().replace(/\s/g, '')}@biohub.local`
  await entrar(page, 'admin')
  await page.goto('/#/usuarios')

  await test.step('Crear la cuenta con rol Investigador', async () => {
    await page.getByRole('button', { name: '+ Nueva cuenta', exact: true }).click()
    await page.getByLabel('Nombre completo', { exact: true }).fill(nombre)
    await page.getByLabel('Correo', { exact: true }).fill(correo)
    await page.getByLabel(/^Contraseña inicial/).fill('BioHub2026!')
    await page.getByLabel('Confirmar contraseña', { exact: true }).fill('BioHub2026!')
    await page.getByLabel('Rol de la cuenta nueva', { exact: true }).selectOption({ label: 'Investigador' })
    await page.getByRole('button', { name: 'Crear cuenta', exact: true }).click()
    await expect(page.getByRole('status')).toContainText(`Cuenta de ${nombre} creada con el rol Investigador.`)
    const fila = page.getByRole('row').filter({ has: page.getByRole('cell', { name: correo, exact: true }) })
    await expect(fila).toBeVisible()
    await expect(fila.getByRole('combobox')).toHaveValue('INVESTIGADOR')
  })

  await test.step('Cambiar a Auditor y comprobar su menú al entrar', async () => {
    const fila = page.getByRole('row').filter({ has: page.getByRole('cell', { name: correo, exact: true }) })
    await fila.getByRole('combobox').selectOption({ label: 'Auditor' })
    await expect(page.getByRole('status')).toContainText(`${nombre} ahora es Auditor.`)
    await expect(fila.getByRole('combobox')).toHaveValue('AUDITOR')
    await salir(page)
    await entrar(page, correo)
    const menu = page.getByRole('navigation', { name: 'Menú principal' })
    await expect(menu.getByRole('link', { name: 'Historial y versiones', exact: true })).toBeVisible()
    await expect(menu.getByRole('link', { name: 'Registrar hallazgo', exact: true })).toHaveCount(0)
    await salir(page)
  })

  await test.step('Desactivar la cuenta y rechazar su inicio de sesión', async () => {
    await entrar(page, 'admin')
    await page.goto('/#/usuarios')
    const fila = page.getByRole('row').filter({ has: page.getByRole('cell', { name: correo, exact: true }) })
    page.once('dialog', (d) => d.accept())
    await fila.getByRole('button', { name: 'Desactivar', exact: true }).click()
    await expect(fila.getByText('Desactivada', { exact: true })).toBeVisible()
    await salir(page)
    await page.goto('/#/entrar')
    await page.locator('input[name="correo"]').fill(correo)
    await page.locator('input[name="contrasena"]').fill('BioHub2026!')
    await page.getByRole('button', { name: 'Entrar', exact: true }).click()
    await expect(page.getByRole('alert')).toHaveText('Correo o contraseña incorrectos. Si el problema sigue, pide al administrador que revise tu cuenta.')
    await expect(page).toHaveURL(/#\/entrar$/)
    await expect(page.getByText('SESIÓN INICIADA', { exact: true })).toHaveCount(0)
  })
})

test('El administrador tiene deshabilitado el selector de su propio rol', async ({ page }) => {
  await entrar(page, 'admin')
  await page.goto('/#/usuarios')
  const fila = page.getByRole('row').filter({ has: page.getByRole('cell', { name: 'admin@biohub.local', exact: true }) })
  await expect(fila).toBeVisible()
  await expect(fila.getByRole('combobox')).toBeDisabled()
})
