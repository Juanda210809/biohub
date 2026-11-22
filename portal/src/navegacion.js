// Navegación por hash (#/registro, #/entrar?volver=/mapa): no necesita servidor ni librerías.
import { useSyncExternalStore } from 'react'

export function leerRuta(hash = window.location.hash) {
  const sinNumeral = hash.replace(/^#/, '')
  const [camino, consulta = ''] = sinNumeral.split('?')
  return {
    camino: camino.startsWith('/') && camino.length > 1 ? camino.replace(/\/+$/, '') : '/',
    parametros: new URLSearchParams(consulta),
  }
}

export function ir(ruta) {
  window.location.hash = ruta
}

function suscribir(aviso) {
  window.addEventListener('hashchange', aviso)
  return () => window.removeEventListener('hashchange', aviso)
}

export function useHash() {
  return useSyncExternalStore(suscribir, () => window.location.hash)
}

// Solo acepta rutas internas del portal ("/algo"): evita volver a una dirección externa.
export function rutaSegura(valor, porDefecto = '/consulta') {
  return typeof valor === 'string' && /^\/[A-Za-z0-9/_-]*$/.test(valor) && !valor.startsWith('//')
    ? valor
    : porDefecto
}
