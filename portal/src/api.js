// Toda llamada a los servicios pasa por Kong (la única puerta de entrada).
// Ejemplo: pedir('/api/v1/consulta/salud')
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function pedir(ruta, opciones = {}) {
  const respuesta = await fetch(`${API_URL}${ruta}`, {
    headers: { 'Content-Type': 'application/json', ...(opciones.headers || {}) },
    ...opciones,
  })
  if (!respuesta.ok) throw new Error(`HTTP ${respuesta.status}`)
  return respuesta.json()
}
