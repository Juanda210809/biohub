import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  actualizarUsuario, borrarSesion, EVENTO_SESION, guardarSesion, leerSesion, tokenActual,
} from './sesion.js'

const CLAVE = 'biohub.sesion'
const sesion = { token: 'token-prueba', usuario: { id: 'usuario-1' } }

beforeEach(() => sessionStorage.clear())
afterEach(() => {
  sessionStorage.clear()
  vi.restoreAllMocks()
})

describe('sesión del portal', () => {
  it('guarda y lee la sesión', () => {
    guardarSesion(sesion)
    expect(JSON.parse(sessionStorage.getItem(CLAVE))).toEqual(sesion)
    expect(leerSesion()).toEqual(sesion)
  })

  it('devuelve null y borra una sesión vencida', () => {
    guardarSesion({ ...sesion, expiraEn: '2020-01-01T00:00:00.000Z' })
    expect(leerSesion(Date.parse('2020-01-02T00:00:00.000Z'))).toBeNull()
    expect(sessionStorage.getItem(CLAVE)).toBeNull()
  })

  it.each([
    ['JSON dañado', '{incorrecto'],
    ['sin token', JSON.stringify({ usuario: sesion.usuario })],
    ['sin usuario', JSON.stringify({ token: sesion.token })],
  ])('descarta una sesión con %s', (_caso, contenido) => {
    sessionStorage.setItem(CLAVE, contenido)
    expect(leerSesion()).toBeNull()
    expect(sessionStorage.getItem(CLAVE)).toBeNull()
  })

  it('actualiza el usuario y conserva el token y el vencimiento', () => {
    const expiraEn = new Date(Date.now() + 60_000).toISOString()
    guardarSesion({ ...sesion, expiraEn })
    const usuario = { id: 'usuario-1', rol: 'INVESTIGADOR' }
    actualizarUsuario(usuario)
    expect(leerSesion()).toEqual({ token: sesion.token, expiraEn, usuario })
  })

  it('no crea una sesión al actualizar el usuario sin sesión', () => {
    actualizarUsuario({ id: 'usuario-1' })
    expect(leerSesion()).toBeNull()
  })

  it('borra la sesión guardada', () => {
    guardarSesion(sesion)
    borrarSesion()
    expect(sessionStorage.getItem(CLAVE)).toBeNull()
    expect(leerSesion()).toBeNull()
  })

  it('obtiene el token actual o null cuando no hay sesión', () => {
    expect(tokenActual()).toBeNull()
    guardarSesion(sesion)
    expect(tokenActual()).toBe(sesion.token)
    borrarSesion()
    expect(tokenActual()).toBeNull()
  })

  it('dispara el evento de sesión al guardar y al borrar', () => {
    const avisar = vi.spyOn(window, 'dispatchEvent')
    guardarSesion(sesion)
    expect(avisar).toHaveBeenCalledTimes(1)
    expect(avisar.mock.calls[0][0]).toBeInstanceOf(Event)
    expect(avisar.mock.calls[0][0].type).toBe(EVENTO_SESION)
    avisar.mockClear()
    borrarSesion()
    expect(avisar).toHaveBeenCalledTimes(1)
    expect(avisar.mock.calls[0][0].type).toBe(EVENTO_SESION)
  })
})
