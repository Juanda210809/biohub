import { randomUUID } from 'node:crypto'
import { expect } from '@playwright/test'

export async function entrar(page, usuario) {
  const correo = usuario.includes('@') ? usuario : `${usuario}@biohub.local`
  await page.goto('/#/entrar')
  await page.locator('input[name="correo"]').fill(correo)
  await page.locator('input[name="contrasena"]').fill('BioHub2026!')
  await page.getByRole('button', { name: 'Entrar', exact: true }).click()
  await expect(page.locator('.barra-lateral').getByText('SESIÓN INICIADA', { exact: true })).toBeVisible()
}

export async function salir(page) {
  await page.getByRole('button', { name: 'Cerrar sesión', exact: true }).click()
  await expect(page).toHaveURL(/#\/consulta$/)
  await expect(page.getByRole('link', { name: 'Iniciar sesión', exact: true })).toBeVisible()
}

export function marcaUnica() {
  // El ecosistema admite letras, pero no cifras.
  const sufijo = randomUUID().replaceAll('-', '').replace(/[0-9]/g, (n) => 'ghijklmnop'[Number(n)])
  return `Prueba ${sufijo}`
}
