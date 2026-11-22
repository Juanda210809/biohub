import { afterEach, describe, expect, it, vi } from 'vitest'
import { guardarSesion, borrarSesion } from '../../sesion.js'
import {
  asignarRol,
  cambiosCuenta,
  crearCuenta,
  desactivarCuenta,
  erroresDelServidor,
  filtrarUsuarios,
  mensajeGeneral,
  reemplazarUsuario,
  resumenCuentas,
  SIN_ROL,
  validarCuenta,
} from './usuarios.js'

const ANA = { id: '1', nombre: 'Ana Pérez', correo: 'ana@biohub.local', rol: 'INVESTIGADOR', activo: true }
const LUIS = { id: '2', nombre: 'Luis Gómez', correo: 'luis@biohub.local', rol: null, activo: true }
const EVA = { id: '3', nombre: 'Eva Ruiz', correo: 'eva@biohub.local', rol: 'AUDITOR', activo: false }
const TODOS = [ANA, LUIS, EVA]

function respuesta(estado, cuerpo) {
  return { ok: estado < 400, status: estado, text: async () => (cuerpo ? JSON.stringify(cuerpo) : '') }
}

describe('llamadas a Identidad', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    borrarSesion()
  })

  it('asignar rol manda PUT con el rol y el token', async () => {
    guardarSesion({ token: 'tok', expiraEn: null, usuario: { id: 'admin', rol: 'ADMINISTRADOR' } })
    const fetchFalso = vi.fn().mockResolvedValue(respuesta(200, { ...LUIS, rol: 'AUDITOR' }))
    vi.stubGlobal('fetch', fetchFalso)

    await asignarRol('2', 'AUDITOR')

    const [url, opciones] = fetchFalso.mock.calls[0]
    expect(url).toMatch(/\/api\/v1\/identidad\/usuarios\/2\/rol$/)
    expect(opciones.method).toBe('PUT')
    expect(JSON.parse(opciones.body)).toEqual({ rol: 'AUDITOR' })
    expect(opciones.headers.Authorization).toBe('Bearer tok')
  })

  it('quitar el rol manda null (HU-02: usuario sin rol)', async () => {
    const fetchFalso = vi.fn().mockResolvedValue(respuesta(200, LUIS))
    vi.stubGlobal('fetch', fetchFalso)
    await asignarRol('2', SIN_ROL)
    expect(JSON.parse(fetchFalso.mock.calls[0][1].body)).toEqual({ rol: null })
  })

  it('crear cuenta manda POST con nombre, correo y contraseña', async () => {
    const fetchFalso = vi.fn().mockResolvedValue(respuesta(201, LUIS))
    vi.stubGlobal('fetch', fetchFalso)
    await crearCuenta({ nombre: 'Luis', correo: 'luis@biohub.local', contrasena: 'segura123' })
    const [url, opciones] = fetchFalso.mock.calls[0]
    expect(url).toMatch(/\/api\/v1\/identidad\/usuarios$/)
    expect(opciones.method).toBe('POST')
    expect(JSON.parse(opciones.body)).toEqual({ nombre: 'Luis', correo: 'luis@biohub.local', contrasena: 'segura123' })
  })

  it('desactivar propaga el código 409 de Identidad', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      respuesta(409, { codigo: 'no_puede_desactivarse', mensaje: 'No puede desactivar su propia cuenta', detalles: [] }),
    ))
    await expect(desactivarCuenta('1')).rejects.toMatchObject({ status: 409, codigo: 'no_puede_desactivarse' })
  })
})

describe('validarCuenta', () => {
  const valida = { nombre: 'Ana', correo: 'ana@biohub.local', contrasena: 'segura123', confirmacion: 'segura123' }

  it('acepta una cuenta nueva completa', () => {
    expect(validarCuenta(valida, { nueva: true })).toEqual({})
  })

  it('en una cuenta nueva exige contraseña', () => {
    expect(validarCuenta({ ...valida, contrasena: '', confirmacion: '' }, { nueva: true }).contrasena).toBeTruthy()
  })

  it('al editar, la contraseña vacía significa no cambiarla', () => {
    expect(validarCuenta({ ...valida, contrasena: '', confirmacion: '' }, { nueva: false })).toEqual({})
  })

  it('aplica los límites de Identidad', () => {
    expect(validarCuenta({ ...valida, contrasena: 'corta', confirmacion: 'corta' }, { nueva: true }).contrasena).toMatch(/8/)
    const larga = 'x'.repeat(73)
    expect(validarCuenta({ ...valida, contrasena: larga, confirmacion: larga }, { nueva: true }).contrasena).toMatch(/72/)
    expect(validarCuenta({ ...valida, nombre: '   ' }, { nueva: true }).nombre).toBeTruthy()
    expect(validarCuenta({ ...valida, correo: 'ana' }, { nueva: true }).correo).toBeTruthy()
  })

  it('pide que la confirmación coincida', () => {
    expect(validarCuenta({ ...valida, confirmacion: 'otra' }, { nueva: true }).confirmacion).toBeTruthy()
  })
})

describe('cambiosCuenta', () => {
  it('solo manda lo que cambió', () => {
    expect(cambiosCuenta(ANA, { nombre: 'Ana Pérez', correo: 'ana@biohub.local', contrasena: '' })).toEqual({})
    expect(cambiosCuenta(ANA, { nombre: ' Ana María ', correo: 'ANA@biohub.local', contrasena: '' })).toEqual({ nombre: 'Ana María' })
    expect(cambiosCuenta(ANA, { nombre: 'Ana Pérez', correo: 'nueva@biohub.local', contrasena: 'segura123' }))
      .toEqual({ correo: 'nueva@biohub.local', contrasena: 'segura123' })
  })
})

describe('erroresDelServidor', () => {
  it('el correo repetido se marca en el campo correo', () => {
    expect(erroresDelServidor({ status: 409, codigo: 'correo_ya_registrado' }).campos.correo).toMatch(/Ya existe/)
  })

  it('los detalles de un 422 se marcan por campo', () => {
    const fallo = { status: 422, codigo: 'peticion_invalida', detalles: [{ campo: 'contrasena', mensaje: 'muy corta' }] }
    expect(erroresDelServidor(fallo)).toEqual({ campos: { contrasena: 'muy corta' }, general: '' })
  })

  it('lo demás queda como mensaje general', () => {
    const { campos, general } = erroresDelServidor({ status: 409, codigo: 'no_puede_quitarse_administrador' })
    expect(campos).toEqual({})
    expect(general).toMatch(/administrador/)
  })
})

describe('mensajeGeneral', () => {
  it('explica el 403 y la falta de conexión', () => {
    expect(mensajeGeneral({ status: 403 })).toMatch(/rol/)
    expect(mensajeGeneral(new TypeError('Failed to fetch'))).toMatch(/conectar/)
  })
})

describe('filtrarUsuarios y resumenCuentas', () => {
  it('busca por nombre o correo sin importar mayúsculas', () => {
    expect(filtrarUsuarios(TODOS, { texto: 'pérez' })).toEqual([ANA])
    expect(filtrarUsuarios(TODOS, { texto: 'LUIS@' })).toEqual([LUIS])
  })

  it('filtra por estado y por rol, incluido "sin rol"', () => {
    expect(filtrarUsuarios(TODOS, { estado: 'DESACTIVADAS' })).toEqual([EVA])
    expect(filtrarUsuarios(TODOS, { estado: 'ACTIVAS' })).toEqual([ANA, LUIS])
    expect(filtrarUsuarios(TODOS, { rol: SIN_ROL })).toEqual([LUIS])
    expect(filtrarUsuarios(TODOS, { rol: 'AUDITOR' })).toEqual([EVA])
  })

  it('cuenta activas, desactivadas y sin rol', () => {
    expect(resumenCuentas(TODOS)).toEqual({ total: 3, activas: 2, desactivadas: 1, sinRol: 1 })
  })

  it('reemplaza solo la cuenta actualizada', () => {
    const lista = reemplazarUsuario(TODOS, { ...LUIS, rol: 'AUDITOR' })
    expect(lista[1].rol).toBe('AUDITOR')
    expect(lista[0]).toBe(ANA)
  })
})
