import { describe, expect, it } from 'vitest'
import { mensajeErrorEntrar, validarCredenciales } from './entrar.js'

describe('validarCredenciales', () => {
  it('acepta un correo y una contraseña escritos', () => {
    expect(validarCredenciales('admin@biohub.local', 'BioHub2026!')).toEqual({})
  })

  it('ignora los espacios alrededor del correo', () => {
    expect(validarCredenciales('  admin@biohub.local  ', 'x')).toEqual({})
  })

  it('pide los dos datos cuando faltan', () => {
    const errores = validarCredenciales('', '')
    expect(errores.correo).toMatch(/correo/i)
    expect(errores.contrasena).toMatch(/contraseña/i)
  })

  it('rechaza un correo sin formato válido', () => {
    expect(validarCredenciales('admin', 'x').correo).toMatch(/válido/)
    expect(validarCredenciales('admin@biohub', 'x').correo).toMatch(/válido/)
  })
})

describe('mensajeErrorEntrar', () => {
  it('con 401 no dice cuál dato falló (HU-01)', () => {
    const mensaje = mensajeErrorEntrar({ status: 401 })
    expect(mensaje).toMatch(/correo o contraseña incorrectos/i)
    expect(mensaje).not.toMatch(/no existe|no está registrado|contraseña es incorrecta/i)
  })

  it('distingue cuando el servicio no está disponible', () => {
    expect(mensajeErrorEntrar({ status: 503 })).toMatch(/no está disponible/)
  })

  it('sin respuesta del servidor habla de conexión', () => {
    expect(mensajeErrorEntrar(new TypeError('Failed to fetch'))).toMatch(/conectar/)
  })
})
