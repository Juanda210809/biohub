import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  API_URL, cerrarSesionEnServidor, EVENTO_SESION_VENCIDA, iniciarSesion,
  listarHallazgos, pedir,
} from './api.js'
import { guardarSesion, leerSesion } from './sesion.js'

let fetchSimulado

function responder(status = 200, datos = {}) {
  fetchSimulado.mockResolvedValueOnce({
    ok: status >= 200 && status < 300,
    status,
    text: vi.fn().mockResolvedValue(datos === null ? '' : JSON.stringify(datos)),
  })
}

function crearSesion() {
  guardarSesion({ token: 'token-prueba', usuario: { id: 'usuario-1' } })
}

beforeEach(() => {
  sessionStorage.clear()
  fetchSimulado = vi.fn()
  vi.stubGlobal('fetch', fetchSimulado)
})

afterEach(() => {
  sessionStorage.clear()
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})

describe('peticiones del portal', () => {
  it('no envía Authorization cuando no hay sesión y devuelve el JSON', async () => {
    responder(200, { resultado: 'correcto' })
    await expect(pedir('/prueba')).resolves.toEqual({ resultado: 'correcto' })
    expect(fetchSimulado).toHaveBeenCalledTimes(1)
    expect(fetchSimulado.mock.calls[0][1].headers).not.toHaveProperty('Authorization')
  })

  it('envía el token de la sesión como Bearer', async () => {
    crearSesion()
    responder()
    await pedir('/prueba')
    expect(fetchSimulado.mock.calls[0][1].headers.Authorization).toBe('Bearer token-prueba')
  })

  it('convierte un cuerpo objeto a JSON y declara su tipo de contenido', async () => {
    responder()
    const body = { nombre: 'Hallazgo', cantidad: 2 }
    await pedir('/prueba', { method: 'POST', body })
    expect(fetchSimulado).toHaveBeenCalledWith(`${API_URL}/prueba`, expect.objectContaining({
      method: 'POST',
      body: JSON.stringify(body),
      headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
    }))
  })

  it('borra la sesión y dispara el evento de vencimiento ante un 401 con token', async () => {
    crearSesion()
    const avisar = vi.spyOn(window, 'dispatchEvent')
    responder(401, { mensaje: 'Sesión vencida' })
    await expect(pedir('/prueba')).rejects.toMatchObject({ status: 401 })
    expect(fetchSimulado.mock.calls[0][1].headers.Authorization).toBe('Bearer token-prueba')
    expect(leerSesion()).toBeNull()
    expect(sessionStorage.getItem('biohub.sesion')).toBeNull()
    const eventos = avisar.mock.calls.map(([evento]) => evento.type)
    expect(eventos.filter((tipo) => tipo === EVENTO_SESION_VENCIDA)).toHaveLength(1)
  })

  it('no dispara el evento de vencimiento ante un 401 sin token', async () => {
    const avisar = vi.spyOn(window, 'dispatchEvent')
    responder(401, { detail: 'Credenciales incorrectas' })
    await expect(pedir('/prueba')).rejects.toMatchObject({ status: 401 })
    expect(fetchSimulado.mock.calls[0][1].headers).not.toHaveProperty('Authorization')
    expect(avisar.mock.calls.map(([evento]) => evento.type)).not.toContain(EVENTO_SESION_VENCIDA)
  })

  it('lanza un error con estado 403 y conserva la sesión', async () => {
    crearSesion()
    responder(403)
    await expect(pedir('/prueba')).rejects.toMatchObject({
      status: 403, message: 'No tiene permiso para hacer esto.',
    })
    expect(leerSesion().token).toBe('token-prueba')
  })

  it('copia el código, el mensaje y los detalles al Error', async () => {
    const detalles = { campo: 'correo' }
    responder(422, { codigo: 'DATO_INVALIDO', mensaje: 'Correo inválido', detalles })
    const resultado = pedir('/prueba')
    await expect(resultado).rejects.toBeInstanceOf(Error)
    await expect(resultado).rejects.toMatchObject({
      status: 422, codigo: 'DATO_INVALIDO', message: 'Correo inválido', detalles,
    })
  })

  it('usa detail como mensaje cuando no hay mensaje', async () => {
    responder(400, { detail: 'Solicitud incorrecta' })
    await expect(pedir('/prueba')).rejects.toThrow('Solicitud incorrecta')
  })

  it('prefiere mensaje sobre detail', async () => {
    responder(400, { mensaje: 'Mensaje principal', detail: 'Mensaje alternativo' })
    await expect(pedir('/prueba')).rejects.toThrow('Mensaje principal')
  })

  it('devuelve null para una respuesta 204 vacía', async () => {
    responder(204, null)
    await expect(pedir('/prueba')).resolves.toBeNull()
  })
})

describe('operaciones de la API', () => {
  it('inicia sesión con POST y las credenciales indicadas', async () => {
    responder()
    await iniciarSesion('persona@example.com', 'clave-prueba')
    expect(fetchSimulado).toHaveBeenCalledWith(`${API_URL}/api/v1/identidad/sesiones`, expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({ correo: 'persona@example.com', contrasena: 'clave-prueba' }),
    }))
  })

  it('cierra la sesión en el servidor con DELETE', async () => {
    responder(204, null)
    await cerrarSesionEnServidor()
    expect(fetchSimulado).toHaveBeenCalledWith(`${API_URL}/api/v1/identidad/sesiones/actual`, expect.objectContaining({
      method: 'DELETE',
    }))
  })

  it.each([
    [undefined, '12', '0'],
    [{ limite: 25, desplazamiento: 50 }, '25', '50'],
  ])('arma la consulta de hallazgos con opciones %j', async (opciones, limite, desplazamiento) => {
    responder()
    await listarHallazgos(opciones)
    const url = new URL(fetchSimulado.mock.calls[0][0], window.location.origin)
    expect(url.pathname).toBe(new URL(`${API_URL}/api/v1/consulta/hallazgos`, window.location.origin).pathname)
    expect([...url.searchParams.entries()]).toEqual([
      ['limite', limite], ['desplazamiento', desplazamiento],
    ])
  })
})
