import { describe, expect, it } from 'vitest'
import {
  construirCuerpo, erroresDelServidor, formularioInicial, hoyLocal, validarFormulario,
} from './formulario.js'

const FICHA = {
  tipoEspecieId: '10000000-0000-0000-0000-000000000001',
  nombre: 'Anfibio',
  revision: 1,
  atributos: [
    { clave: 'habitat', etiqueta: 'Hábitat', tipo: 'SELECCION', obligatorio: false, reglas: { opciones: ['quebrada', 'charca'] } },
    { clave: 'observaciones', etiqueta: 'Observaciones', tipo: 'TEXTO', obligatorio: false, reglas: { longitudMaxima: 10 } },
    { clave: 'temperaturaAgua', etiqueta: 'Temperatura', tipo: 'NUMERO', obligatorio: true, reglas: { minimo: 0, maximo: 40 } },
  ],
}

function completo(cambios = {}) {
  return {
    ...formularioInicial(new Date(2026, 10, 22)),
    especieId: '20000000-0000-0000-0000-000000000001',
    expedicionId: '30000000-0000-0000-0000-000000000001',
    latitud: '2.5',
    longitud: '-77.0',
    departamento: 'Cauca',
    atributos: { temperaturaAgua: '18.5' },
    ...cambios,
  }
}

describe('formulario de registrar hallazgo', () => {
  it('usa la fecha local de hoy como valor inicial', () => {
    expect(hoyLocal(new Date(2026, 10, 5))).toBe('2026-11-05')
    expect(formularioInicial(new Date(2026, 0, 9)).fechaHallazgo).toBe('2026-01-09')
  })

  it('un formulario completo no tiene errores', () => {
    expect(validarFormulario(completo(), FICHA)).toEqual({})
  })

  it('pide lo obligatorio cuando está vacío', () => {
    const errores = validarFormulario(formularioInicial(new Date(2026, 10, 22)), FICHA)
    expect(Object.keys(errores)).toEqual(
      expect.arrayContaining(['especieId', 'expedicionId', 'latitud', 'longitud', 'region', 'atributos.temperaturaAgua']),
    )
  })

  it('acepta solo la región o solo el departamento, pero no ninguno', () => {
    expect(validarFormulario(completo({ departamento: '', region: 'Pacífico' }), FICHA)).toEqual({})
    expect(validarFormulario(completo({ departamento: '', region: '' }), FICHA).region).toBeDefined()
  })

  it.each(['X', '12', '123', 'ab', '@@@', '9 de julio'])('rechaza el lugar sin sentido "%s"', (valor) => {
    const errores = validarFormulario(completo({ region: valor, departamento: valor, ecosistema: valor }), FICHA)
    expect(errores.region).toBeDefined()
    expect(errores.departamento).toBeDefined()
    expect(errores.ecosistema).toBeDefined()
  })

  it.each(['Pacífico', 'Valle del Cauca', 'San Andrés y Providencia', 'Bosque húmedo', "N'Dorado-Sur"])(
    'acepta el nombre de lugar "%s"', (valor) => {
      expect(validarFormulario(completo({ region: valor, departamento: valor, ecosistema: valor }), FICHA)).toEqual({})
    },
  )

  it('rechaza un nombre de lugar de más de 80 caracteres', () => {
    expect(validarFormulario(completo({ departamento: 'a'.repeat(81) }), FICHA).departamento).toMatch(/80/)
  })

  it('rechaza coordenadas fuera de rango', () => {
    const errores = validarFormulario(completo({ latitud: '91', longitud: '-181' }), FICHA)
    expect(errores.latitud).toMatch(/-90 y 90/)
    expect(errores.longitud).toMatch(/-180 y 180/)
  })

  it('valida los atributos según sus reglas', () => {
    const errores = validarFormulario(
      completo({ atributos: { temperaturaAgua: '41', observaciones: 'demasiado largo', habitat: 'mar' } }),
      FICHA,
    )
    expect(errores['atributos.temperaturaAgua']).toBe('debe ser menor o igual a 40')
    expect(errores['atributos.observaciones']).toMatch(/más de 10/)
    expect(errores['atributos.habitat']).toBeDefined()
  })

  it('arma el cuerpo con números reales y sin campos vacíos', () => {
    const cuerpo = construirCuerpo(
      completo({ departamento: ' Cauca ', precisionM: '10', atributos: { temperaturaAgua: '18.5', habitat: 'quebrada', observaciones: '' } }),
      FICHA,
    )
    expect(cuerpo).toEqual({
      especieId: '20000000-0000-0000-0000-000000000001',
      expedicionId: '30000000-0000-0000-0000-000000000001',
      fechaHallazgo: '2026-11-22',
      latitud: 2.5,
      longitud: -77,
      precisionM: 10,
      departamento: 'Cauca',
      atributos: { temperaturaAgua: 18.5, habitat: 'quebrada' },
    })
  })

  it('ignora los atributos de un tipo que el formulario no sabe mostrar', () => {
    const ficha = { ...FICHA, atributos: [...FICHA.atributos, { clave: 'foto', tipo: 'ARCHIVO', obligatorio: true, reglas: {} }] }
    expect(validarFormulario(completo(), ficha)).toEqual({})
    expect(construirCuerpo(completo({ atributos: { foto: 'x', temperaturaAgua: '1' } }), ficha).atributos).toEqual({ temperaturaAgua: 1 })
  })

  it('reparte los errores del servidor entre los campos y el mensaje general', () => {
    const error = {
      detalles: [
        { campo: 'temperaturaAgua', mensaje: 'es obligatorio' },
        { campo: 'latitud', mensaje: 'debe ser menor o igual a 90' },
        { campo: 'cuerpo', mensaje: 'Debe indicar al menos la region o el departamento' },
      ],
    }
    expect(erroresDelServidor(error, FICHA)).toEqual({
      campos: { 'atributos.temperaturaAgua': 'es obligatorio', latitud: 'debe ser menor o igual a 90' },
      general: ['Debe indicar al menos la region o el departamento'],
    })
  })

  it('no falla si el error no trae detalles', () => {
    expect(erroresDelServidor(new Error('x'), FICHA)).toEqual({ campos: {}, general: [] })
  })
})
