import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { ir, leerRuta, rutaSegura } from './navegacion.js'

let urlAnterior
beforeEach(() => { urlAnterior = window.location.href })
afterEach(() => { window.history.replaceState(null, '', urlAnterior) })

describe('lectura de rutas', () => {
  it.each([
    ['#/registro', '/registro'],
    ['', '/'],
    ['#inicio', '/'],
    ['#/registro/', '/registro'],
    ['#/registro///', '/registro'],
  ])('interpreta %j como %s', (hash, camino) => {
    const ruta = leerRuta(hash)
    expect(ruta.camino).toBe(camino)
    expect([...ruta.parametros]).toEqual([])
  })

  it('separa el camino de los parámetros de consulta', () => {
    const ruta = leerRuta('#/entrar?volver=/mapa')
    expect(ruta.camino).toBe('/entrar')
    expect(ruta.parametros).toBeInstanceOf(URLSearchParams)
    expect(ruta.parametros.get('volver')).toBe('/mapa')
  })

  it('lee el hash actual cuando no se proporciona uno', () => {
    window.history.replaceState(null, '', '#/registro')
    expect(leerRuta().camino).toBe('/registro')
  })

  it('navega cambiando el hash', () => {
    ir('/mapa')
    expect(window.location.hash).toBe('#/mapa')
  })
})

describe('rutas seguras', () => {
  it('acepta una ruta interna', () => {
    expect(rutaSegura('/mapa')).toBe('/mapa')
  })

  it.each(['https://x.com', '//x.com', 'javascript:alert(1)', null])(
    'rechaza %j y devuelve la ruta predeterminada', (valor) => {
      expect(rutaSegura(valor)).toBe('/consulta')
    },
  )

  it('permite indicar una ruta alternativa para valores rechazados', () => {
    expect(rutaSegura(null, '/entrar')).toBe('/entrar')
  })
})
