import { describe, expect, it } from 'vitest'
import { buscarPagina, destinoTrasEntrar, esPublica, PAGINAS, paginasDelMenu, puedeVer } from './paginas.js'
import { ROLES } from './roles.js'

describe('páginas del portal', () => {
  it('la consulta es pública y visible para cualquier usuario', () => {
    const consulta = buscarPagina('/consulta')
    expect(consulta).not.toBeNull()
    expect(esPublica(consulta)).toBe(true)
    for (const usuario of [undefined, null, {}, { rol: 'DESCONOCIDO' }, ...Object.values(ROLES).map((rol) => ({ rol }))]) {
      expect(puedeVer(consulta, usuario)).toBe(true)
    }
  })

  it.each([undefined, null, {}, { rol: null }, { rol: 'DESCONOCIDO' }])(
    'solo muestra la consulta a un usuario sin rol válido: %j', (usuario) => {
      expect(PAGINAS.filter((pagina) => puedeVer(pagina, usuario)).map((pagina) => pagina.ruta)).toEqual(['/consulta'])
      expect(paginasDelMenu(usuario).map((pagina) => pagina.ruta)).toEqual(['/consulta'])
    },
  )

  it.each([
    [ROLES.INVESTIGADOR, ['/registro', '/mapa']],
    [ROLES.CIENTIFICO_AUTORIZADO, ['/fichas', '/mapa', '/reclasificar']],
    [ROLES.ALTO_RANGO, ['/mapa', '/indices']],
    [ROLES.AUDITOR, ['/mapa', '/historial']],
    [ROLES.ADMINISTRADOR, ['/mapa', '/usuarios']],
  ])('el rol %s ve exactamente sus páginas internas', (rol, rutasInternas) => {
    const usuario = { rol }
    for (const pagina of PAGINAS) {
      expect(puedeVer(pagina, usuario)).toBe(pagina.ruta === '/consulta' || rutasInternas.includes(pagina.ruta))
      expect(esPublica(pagina)).toBe(pagina.ruta === '/consulta')
    }
    expect(paginasDelMenu(usuario).map((pagina) => pagina.ruta).sort()).toEqual(
      ['/consulta', ...rutasInternas].sort(),
    )
  })

  it('devuelve null para una ruta inexistente', () => {
    expect(buscarPagina('/no-existe')).toBeNull()
  })

  it('encuentra cada página por su ruta', () => {
    for (const pagina of PAGINAS) expect(buscarPagina(pagina.ruta)).toBe(pagina)
  })

  it('todas las rutas son únicas', () => {
    const rutas = PAGINAS.map((pagina) => pagina.ruta)
    expect(new Set(rutas).size).toBe(rutas.length)
  })
})

describe('destino después de iniciar sesión', () => {
  it('vuelve a la página pedida si el rol la puede ver', () => {
    expect(destinoTrasEntrar('/registro', { rol: ROLES.INVESTIGADOR })).toBe('/registro')
  })

  it('va a la consulta si el rol no puede ver la página pedida', () => {
    expect(destinoTrasEntrar('/registro', { rol: ROLES.ADMINISTRADOR })).toBe('/consulta')
  })

  it.each([null, '', '/no-existe', 'https://x.com', '//x.com'])('va a la consulta con volver=%j', (volver) => {
    expect(destinoTrasEntrar(volver, { rol: ROLES.INVESTIGADOR })).toBe('/consulta')
  })
})
