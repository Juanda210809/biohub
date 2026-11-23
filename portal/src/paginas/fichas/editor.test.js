import { describe, expect, it } from 'vitest'
import {
  construirCuerpo, erroresDelServidor, filaDesdeAtributo, filaNueva, firma, hayErrores, tiposDeEspecie,
  validarFilas,
} from './editor.js'

const ATRIBUTOS = [
  { clave: 'temperaturaAgua', etiqueta: 'Temperatura del agua', tipo: 'NUMERO', obligatorio: true, publicable: false, reglas: { minimo: 0, maximo: 40, unidad: '°C' } },
  { clave: 'habitat', etiqueta: 'Hábitat', tipo: 'SELECCION', obligatorio: false, publicable: true, reglas: { opciones: ['quebrada', 'charca'] } },
]

function filasDeEjemplo() {
  return ATRIBUTOS.map(filaDesdeAtributo)
}

function nueva(cambios = {}, reglas = {}) {
  const fila = filaNueva()
  return { ...fila, clave: 'nuevo', etiqueta: 'Nuevo', ...cambios, reglas: { ...fila.reglas, ...reglas } }
}

describe('editor de fichas', () => {
  it('lo que se carga y se vuelve a enviar sin tocar queda igual que el original', () => {
    const cuerpo = construirCuerpo(3, filasDeEjemplo())
    expect(cuerpo).toEqual({ revisionBase: 3, atributos: ATRIBUTOS })
  })

  it('los atributos existentes no se pueden renombrar ni cambiar de tipo, los nuevos sí', () => {
    expect(filasDeEjemplo().every((fila) => fila.existente)).toBe(true)
    expect(filaNueva().existente).toBe(false)
  })

  it('detecta si hay cambios sin publicar', () => {
    const filas = filasDeEjemplo()
    const original = firma(filas)
    expect(firma(filas)).toBe(original)
    filas[0].etiqueta = 'Otra etiqueta'
    expect(firma(filas)).not.toBe(original)
    expect(firma([...filasDeEjemplo(), filaNueva()])).not.toBe(original)
  })

  it('una ficha válida no tiene errores', () => {
    expect(hayErrores(validarFilas([...filasDeEjemplo(), nueva()]))).toBe(false)
  })

  it('no deja publicar una ficha sin atributos', () => {
    expect(validarFilas([]).general).toEqual(['La ficha debe tener al menos un atributo.'])
  })

  it.each(['', 'Temperatura', '1abc', 'con espacio', 'ñandú', 'a'.repeat(61)])('rechaza la clave "%s"', (clave) => {
    expect(validarFilas([nueva({ clave })]).porFila[0].clave).toBeDefined()
  })

  it('rechaza una clave repetida', () => {
    const errores = validarFilas([nueva(), nueva()])
    expect(errores.porFila[1].clave).toMatch(/otro atributo/)
    expect(errores.porFila[0]).toBeUndefined()
  })

  it('pide una etiqueta de hasta 100 caracteres', () => {
    expect(validarFilas([nueva({ etiqueta: '  ' })]).porFila[0].etiqueta).toBeDefined()
    expect(validarFilas([nueva({ etiqueta: 'a'.repeat(101) })]).porFila[0].etiqueta).toMatch(/100/)
  })

  it('valida las reglas de un número', () => {
    expect(validarFilas([nueva({ tipo: 'NUMERO' }, { minimo: '10', maximo: '5' })]).porFila[0].reglas).toMatch(/mínimo no puede ser mayor/)
    expect(validarFilas([nueva({ tipo: 'NUMERO' }, { minimo: 'abc' })]).porFila[0].reglas).toMatch(/mínimo debe ser un número/)
    expect(validarFilas([nueva({ tipo: 'NUMERO' }, { minimo: '0', maximo: '5' })]).porFila).toEqual({})
  })

  it('valida las reglas de un texto', () => {
    expect(validarFilas([nueva({ tipo: 'TEXTO' }, { longitudMaxima: '0' })]).porFila[0].reglas).toMatch(/mayor o igual a 1/)
    expect(validarFilas([nueva({ tipo: 'TEXTO' }, { longitudMaxima: '2.5' })]).porFila[0].reglas).toBeDefined()
    expect(validarFilas([nueva({ tipo: 'TEXTO' }, { longitudMaxima: '50' })]).porFila).toEqual({})
  })

  it('valida las reglas de una fecha', () => {
    expect(validarFilas([nueva({ tipo: 'FECHA' }, { fechaMinima: '2026-12-01', fechaMaxima: '2026-01-01' })]).porFila[0].reglas)
      .toMatch(/fecha mínima/)
  })

  it('una selección necesita opciones y sin repetir', () => {
    expect(validarFilas([nueva({ tipo: 'SELECCION' }, { opciones: ' \n ' })]).porFila[0].reglas).toMatch(/al menos una opción/)
    expect(validarFilas([nueva({ tipo: 'SELECCION' }, { opciones: 'a\nb\na' })]).porFila[0].reglas).toMatch(/repetirse/)
    expect(validarFilas([nueva({ tipo: 'SELECCION' }, { opciones: 'a\n\n b ' })]).porFila).toEqual({})
  })

  it('arma solo las reglas del tipo elegido, con números reales', () => {
    const cuerpo = construirCuerpo(1, [
      nueva({ clave: 'peso', tipo: 'NUMERO' }, { minimo: '0', maximo: '12.5', unidad: ' kg ', patron: 'sobra', opciones: 'sobra' }),
      nueva({ clave: 'nota', tipo: 'TEXTO' }, { longitudMaxima: '80', minimo: '99' }),
      nueva({ clave: 'color', tipo: 'SELECCION' }, { opciones: 'rojo\nazul' }),
    ])
    expect(cuerpo.atributos.map((a) => a.reglas)).toEqual([
      { minimo: 0, maximo: 12.5, unidad: 'kg' },
      { longitudMaxima: 80 },
      { opciones: ['rojo', 'azul'] },
    ])
  })

  it('reparte los errores del servidor entre las filas y el mensaje general', () => {
    const error = {
      detalles: [
        { campo: 'atributos[1].clave', mensaje: 'está repetida en la ficha' },
        { campo: 'atributos[1].reglas', mensaje: 'minimo no puede ser mayor que maximo' },
        { campo: 'atributos.2.tipo', mensaje: 'Input should be a valid enumeration member' },
        { campo: 'atributos[0].obligatorio', mensaje: 'raro' },
        { campo: 'atributos', mensaje: 'debe incluir al menos un atributo' },
        { campo: 'revisionBase', mensaje: 'la revisión vigente es la 4' },
      ],
    }
    expect(erroresDelServidor(error)).toEqual({
      porFila: {
        1: { clave: 'está repetida en la ficha', reglas: 'minimo no puede ser mayor que maximo' },
        2: { tipo: 'Input should be a valid enumeration member' },
        0: { otro: 'raro' },
      },
      general: ['atributos: debe incluir al menos un atributo', 'revisionBase: la revisión vigente es la 4'],
    })
  })

  it('no falla si el error no trae detalles', () => {
    expect(erroresDelServidor(new Error('x'))).toEqual({ porFila: {}, general: [] })
  })

  it('saca los tipos de especie del catálogo, sin repetir y por nombre', () => {
    const especies = [
      { id: '1', tipoEspecieId: 'b', tipoEspecie: 'Ave' },
      { id: '2', tipoEspecieId: 'a', tipoEspecie: 'Anfibio' },
      { id: '3', tipoEspecieId: 'b', tipoEspecie: 'Ave' },
    ]
    expect(tiposDeEspecie(especies)).toEqual([{ id: 'a', nombre: 'Anfibio' }, { id: 'b', nombre: 'Ave' }])
  })
})
