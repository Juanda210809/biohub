// Todas las llamadas del portal pasan por Kong, la única puerta de entrada.
export const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')

export async function pedir(ruta, opciones = {}) {
  const respuesta = await fetch(`${API_URL}${ruta}`, {
    ...opciones,
    headers: {
      Accept: 'application/json',
      ...(opciones.headers || {}),
    },
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
    const detalle = datos?.detail || datos?.mensaje || `Error HTTP ${respuesta.status}`
    const error = new Error(typeof detalle === 'string' ? detalle : `Error HTTP ${respuesta.status}`)
    error.status = respuesta.status
    throw error
  }

  return datos
}

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
