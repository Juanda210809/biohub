// La sesión del portal: token y usuario que devuelve Identidad al iniciar sesión.
// Vive en sessionStorage: se borra al cerrar la pestaña y no se comparte entre pestañas.
const CLAVE = 'biohub.sesion'
export const EVENTO_SESION = 'biohub:sesion'

function almacen() {
  try {
    return window.sessionStorage
  } catch {
    return null
  }
}

function avisar() {
  window.dispatchEvent(new Event(EVENTO_SESION))
}

export function leerSesion(ahora = Date.now()) {
  const guardada = almacen()?.getItem(CLAVE)
  if (!guardada) return null
  try {
    const sesion = JSON.parse(guardada)
    if (!sesion?.token || !sesion?.usuario) throw new Error('sesión incompleta')
    if (sesion.expiraEn && Date.parse(sesion.expiraEn) <= ahora) throw new Error('sesión vencida')
    return sesion
  } catch {
    almacen()?.removeItem(CLAVE)
    return null
  }
}

export function guardarSesion({ token, expiraEn, usuario }) {
  almacen()?.setItem(CLAVE, JSON.stringify({ token, expiraEn, usuario }))
  avisar()
}

export function actualizarUsuario(usuario) {
  const sesion = leerSesion()
  if (sesion) guardarSesion({ ...sesion, usuario })
}

export function borrarSesion() {
  almacen()?.removeItem(CLAVE)
  avisar()
}

export function tokenActual() {
  return leerSesion()?.token ?? null
}
