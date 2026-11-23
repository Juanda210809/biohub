import { describe, expect, it } from 'vitest'
import {
  anchoBarra, autorCorto, erroresPorCampo, especiesDestino, etiquetaCampo, filtrarHallazgos,
  hoyIso, indiceLegible, mensajeError, mesActual, mesAnterior, nombreMes, resumenIndices, valorLegible,
} from './utilidades.js'

const hallazgos = [
  { hallazgo_id: '1', especie: 'Setophaga cerulea', region: 'Pacífico', departamento: 'Cauca', ecosistema: 'Bosque húmedo' },
  { hallazgo_id: '2', especie: 'Phyllobates terribilis', region: 'Andina', departamento: 'Antioquia', ecosistema: 'Páramo' },
]

describe('filtrarHallazgos', () => {
  it('sin búsqueda devuelve todos', () => {
    expect(filtrarHallazgos(hallazgos, '  ')).toHaveLength(2)
  })
  it('busca sin importar tildes ni mayúsculas', () => {
    expect(filtrarHallazgos(hallazgos, 'PACIFICO').map((h) => h.hallazgo_id)).toEqual(['1'])
    expect(filtrarHallazgos(hallazgos, 'paramo').map((h) => h.hallazgo_id)).toEqual(['2'])
  })
  it('busca también por especie', () => {
    expect(filtrarHallazgos(hallazgos, 'terribilis')).toHaveLength(1)
  })
})

describe('especiesDestino', () => {
  it('quita la especie que el hallazgo ya tiene', () => {
    const especies = [{ id: 'a', nombreCientifico: 'Setophaga cerulea' }, { id: 'b', nombreCientifico: 'Thraupis episcopus' }]
    expect(especiesDestino(especies, 'Setophaga cerulea').map((e) => e.id)).toEqual(['b'])
  })
})

describe('errores del backend', () => {
  it('agrupa los detalles por campo y se queda con el primero', () => {
    const error = { detalles: [{ campo: 'justificacion', mensaje: 'Obligatoria' }, { campo: 'justificacion', mensaje: 'Otra' }] }
    expect(erroresPorCampo(error)).toEqual({ justificacion: 'Obligatoria' })
    expect(erroresPorCampo(null)).toEqual({})
  })
  it('traduce los códigos conocidos', () => {
    expect(mensajeError({ status: 409, codigo: 'misma_especie' })).toMatch(/ya está clasificado/)
    expect(mensajeError({ status: 403 })).toMatch(/permiso/)
    expect(mensajeError({ message: 'Failed to fetch' })).toMatch(/conectar/)
    expect(mensajeError({ status: 500, message: 'Falla rara' })).toBe('Falla rara')
  })
})

describe('fechas y meses', () => {
  it('hoy en formato AAAA-MM-DD', () => {
    expect(hoyIso(new Date(2026, 10, 5))).toBe('2026-11-05')
  })
  it('el mes anterior cruza de año', () => {
    expect(mesAnterior(new Date(2026, 10, 18))).toBe('2026-10')
    expect(mesAnterior(new Date(2027, 0, 3))).toBe('2026-12')
    expect(mesActual(new Date(2026, 10, 18))).toBe('2026-11')
  })
  it('nombre del mes en español', () => {
    expect(nombreMes('2026-10')).toBe('octubre de 2026')
    expect(nombreMes('2026-13')).toBe('2026-13')
  })
})

describe('textos de la tabla de cambios', () => {
  it('etiqueta legible para cada campo', () => {
    expect(etiquetaCampo('especie')).toBe('Especie')
    expect(etiquetaCampo('atributos.altitudMsnm')).toBe('Altitud msnm')
    expect(etiquetaCampo('temperatura_agua')).toBe('Temperatura agua')
  })
  it('valores vacíos se muestran con raya', () => {
    expect(valorLegible(null)).toBe('—')
    expect(valorLegible('quebrada')).toBe('quebrada')
  })
  it('el autor se muestra corto', () => {
    expect(autorCorto('3f2a9c1e-0000-4000-8000-00000000ab12')).toBe('Usuario …00ab12')
    expect(autorCorto(null)).toBe('Autor desconocido')
  })
})

describe('índices', () => {
  const ecosistemas = [
    { ecosistema: 'Páramo', hallazgos: 5, indice: 2.5, nivel: 'ALTA' },
    { ecosistema: 'Manglar', hallazgos: 2, indice: 1, nivel: 'NORMAL' },
    { ecosistema: 'Selva', hallazgos: 1, indice: null, nivel: 'SIN_HISTORIA' },
  ]
  it('resume el mes', () => {
    expect(resumenIndices(ecosistemas)).toEqual({ ecosistemas: 3, hallazgos: 8, alta: 1, maximo: 2.5 })
    expect(resumenIndices()).toEqual({ ecosistemas: 0, hallazgos: 0, alta: 0, maximo: 0 })
  })
  it('la barra es proporcional al índice más alto', () => {
    expect(anchoBarra(2.5, 2.5)).toBe(100)
    expect(anchoBarra(1, 2.5)).toBe(40)
    expect(anchoBarra(null, 2.5)).toBe(0)
    expect(anchoBarra(0.001, 2.5)).toBe(2)
  })
  it('el índice se muestra con dos decimales', () => {
    expect(indiceLegible(null)).toBe('—')
    expect(indiceLegible(1.333)).toMatch(/^1[,.]33$/)
  })
})
