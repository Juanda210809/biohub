// HU-02 · HU-18 · Llamadas a Identidad y reglas de la pantalla de usuarios.
// Todo pasa por Kong con pedir(): el token va solo y el PDP exige rol ADMINISTRADOR.
import { pedir } from '../../api.js'

const BASE = '/api/v1/identidad/usuarios'
const PATRON_CORREO = /^[^@\s]+@[^@\s]+\.[^@\s]+$/

export const CLAVE_MINIMA = 8
export const CLAVE_MAXIMA = 72
// En los <select> "sin rol" se representa con texto vacío; a la API se le manda null.
export const SIN_ROL = ''

// ---------------------------------------------------------------- API de Identidad

export function listarUsuarios({ signal } = {}) {
  return pedir(BASE, { signal })
}

export function crearCuenta({ nombre, correo, contrasena }) {
  return pedir(BASE, { method: 'POST', body: { nombre, correo, contrasena } })
}

export function modificarCuenta(id, cambios) {
  return pedir(`${BASE}/${encodeURIComponent(id)}`, { method: 'PATCH', body: cambios })
}

export function desactivarCuenta(id) {
  return pedir(`${BASE}/${encodeURIComponent(id)}/desactivar`, { method: 'POST' })
}

export function activarCuenta(id) {
  return pedir(`${BASE}/${encodeURIComponent(id)}/activar`, { method: 'POST' })
}

export function asignarRol(id, rol) {
  return pedir(`${BASE}/${encodeURIComponent(id)}/rol`, { method: 'PUT', body: { rol: rol || null } })
}

// ---------------------------------------------------------------- Reglas de la pantalla

// Valida el formulario de cuenta. En una cuenta nueva la contraseña es obligatoria;
// al editar, vacía significa "no cambiarla".
export function validarCuenta({ nombre, correo, contrasena, confirmacion }, { nueva }) {
  const errores = {}
  const nombreLimpio = String(nombre ?? '').trim()
  const correoLimpio = String(correo ?? '').trim()
  const clave = contrasena ?? ''

  if (!nombreLimpio) errores.nombre = 'Escribe el nombre.'
  else if (nombreLimpio.length > 120) errores.nombre = 'El nombre admite máximo 120 caracteres.'

  if (!correoLimpio) errores.correo = 'Escribe el correo.'
  else if (!PATRON_CORREO.test(correoLimpio)) errores.correo = 'Escribe un correo válido.'

  if (nueva && !clave) errores.contrasena = 'Escribe una contraseña inicial.'
  else if (clave && clave.length < CLAVE_MINIMA) errores.contrasena = `Mínimo ${CLAVE_MINIMA} caracteres.`
  else if (clave.length > CLAVE_MAXIMA) errores.contrasena = `Máximo ${CLAVE_MAXIMA} caracteres.`

  if (clave && !errores.contrasena && clave !== (confirmacion ?? '')) {
    errores.confirmacion = 'Las contraseñas no coinciden.'
  }
  return errores
}

// Al editar, manda solo lo que cambió (la API exige al menos un dato).
export function cambiosCuenta(original, formulario) {
  const cambios = {}
  const nombre = String(formulario.nombre ?? '').trim()
  const correo = String(formulario.correo ?? '').trim().toLowerCase()
  if (nombre !== original.nombre) cambios.nombre = nombre
  if (correo !== String(original.correo).toLowerCase()) cambios.correo = correo
  if (formulario.contrasena) cambios.contrasena = formulario.contrasena
  return cambios
}

// Convierte un error de la API en mensajes por campo y un mensaje general.
export function erroresDelServidor(fallo) {
  const campos = {}
  if (fallo?.codigo === 'correo_ya_registrado') {
    campos.correo = 'Ya existe una cuenta con ese correo.'
    return { campos, general: '' }
  }
  if (Array.isArray(fallo?.detalles)) {
    for (const { campo, mensaje } of fallo.detalles) {
      if (['nombre', 'correo', 'contrasena'].includes(campo)) campos[campo] = mensaje
    }
  }
  if (Object.keys(campos).length > 0) return { campos, general: '' }
  return { campos, general: mensajeGeneral(fallo) }
}

export function mensajeGeneral(fallo) {
  switch (fallo?.codigo) {
    case 'no_puede_desactivarse':
      return 'No puedes desactivar tu propia cuenta.'
    case 'no_puede_quitarse_administrador':
      return 'No puedes quitarte tu propio rol de administrador: el sistema podría quedar sin administrador.'
    case 'usuario_no_existe':
      return 'Esa cuenta ya no existe. Recarga la lista.'
    default:
      break
  }
  if (fallo?.status === 403) return 'Tu rol ya no permite administrar cuentas.'
  if (fallo?.status) return fallo.message || `Error HTTP ${fallo.status}`
  return 'No pudimos conectar con BioHub. Verifica que los servicios estén activos.'
}

// Busca por nombre o correo y filtra por estado y rol. rol: 'TODOS', SIN_ROL o un rol.
export function filtrarUsuarios(usuarios, { texto = '', estado = 'TODOS', rol = 'TODOS' } = {}) {
  const termino = texto.trim().toLocaleLowerCase('es-CO')
  return usuarios.filter((usuario) => {
    const coincideTexto = !termino || [usuario.nombre, usuario.correo]
      .some((valor) => String(valor).toLocaleLowerCase('es-CO').includes(termino))
    const coincideEstado = estado === 'TODOS'
      || (estado === 'ACTIVAS' && usuario.activo)
      || (estado === 'DESACTIVADAS' && !usuario.activo)
    const coincideRol = rol === 'TODOS' || (usuario.rol ?? SIN_ROL) === rol
    return coincideTexto && coincideEstado && coincideRol
  })
}

export function resumenCuentas(usuarios) {
  return {
    total: usuarios.length,
    activas: usuarios.filter((usuario) => usuario.activo).length,
    desactivadas: usuarios.filter((usuario) => !usuario.activo).length,
    sinRol: usuarios.filter((usuario) => !usuario.rol).length,
  }
}

// Reemplaza en la lista la cuenta que devolvió la API, sin volver a pedir todo.
export function reemplazarUsuario(usuarios, actualizado) {
  return usuarios.map((usuario) => (usuario.id === actualizado.id ? actualizado : usuario))
}
