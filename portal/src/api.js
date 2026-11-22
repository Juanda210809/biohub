// Todas las llamadas del portal pasan por Kong, la única puerta de entrada.
// Si hay sesión, cada petición lleva "Authorization: Bearer <token>"; el PDP decide qué se puede.
import { borrarSesion, tokenActual } from './sesion.js'

export const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')

// Se dispara cuando Identidad ya no acepta el token (vencido, cerrado o cuenta desactivada).
export const EVENTO_SESION_VENCIDA = 'biohub:sesion-vencida'

function mensajeDe(datos, estado) {
  const detalle = datos?.mensaje || datos?.detail
  if (typeof detalle === 'string' && detalle) return detalle
  if (estado === 403) return 'No tiene permiso para hacer esto.'
  return `Error HTTP ${estado}`
}

export async function pedir(ruta, opciones = {}) {
  const token = tokenActual()
  const cabeceras = { Accept: 'application/json', ...(opciones.headers || {}) }
  if (token && !cabeceras.Authorization) cabeceras.Authorization = `Bearer ${token}`
  if (opciones.body !== undefined && typeof opciones.body !== 'string') {
    cabeceras['Content-Type'] = 'application/json'
  }

  const respuesta = await fetch(`${API_URL}${ruta}`, {
    ...opciones,
    headers: cabeceras,
    body: opciones.body !== undefined && typeof opciones.body !== 'string'
      ? JSON.stringify(opciones.body)
      : opciones.body,
  })

  const texto = await respuesta.text()
  let datos = null
  if (texto) {
    try {
      datos = JSON.parse(texto)
    } catch {
      datos = { detail: texto }
    }
  }

  if (!respuesta.ok) {
    // 401 con token: la sesión ya no sirve. Se borra y el portal vuelve al inicio de sesión.
    if (respuesta.status === 401 && cabeceras.Authorization) {
      borrarSesion()
      window.dispatchEvent(new Event(EVENTO_SESION_VENCIDA))
    }
    const error = new Error(mensajeDe(datos, respuesta.status))
    error.status = respuesta.status
    error.codigo = datos?.codigo
    error.detalles = datos?.detalles
    throw error
  }

  return datos
}

// ---------------------------------------------------------------- Identidad (sesión)

export function iniciarSesion(correo, contrasena) {
  return pedir('/api/v1/identidad/sesiones', { method: 'POST', body: { correo, contrasena } })
}

export function sesionActual() {
  return pedir('/api/v1/identidad/sesiones/actual')
}

export function cerrarSesionEnServidor() {
  return pedir('/api/v1/identidad/sesiones/actual', { method: 'DELETE' })
}

// ---------------------------------------------------------------- Consulta pública (HU-05/06)

export function listarHallazgos({ limite = 12, desplazamiento = 0, signal } = {}) {
  const parametros = new URLSearchParams({
    limite: String(limite),
    desplazamiento: String(desplazamiento),
  })

  return pedir(`/api/v1/consulta/hallazgos?${parametros.toString()}`, { signal })
}

export function obtenerFicha(hallazgoId, { signal } = {}) {
  return pedir(`/api/v1/consulta/hallazgos/${encodeURIComponent(hallazgoId)}`, { signal })
}
