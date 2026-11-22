// Comparte la sesión con todo el portal: useSesion() devuelve el usuario, entrar() y salir().
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { cerrarSesionEnServidor, iniciarSesion, sesionActual } from './api.js'
import { actualizarUsuario, borrarSesion, EVENTO_SESION, guardarSesion, leerSesion } from './sesion.js'

const Contexto = createContext(null)

export function ProveedorSesion({ children }) {
  const [usuario, setUsuario] = useState(() => leerSesion()?.usuario ?? null)
  // Si al abrir había una sesión guardada, se confirma con Identidad antes de confiar en ella.
  const [verificando, setVerificando] = useState(() => leerSesion() !== null)

  useEffect(() => {
    const sincronizar = () => setUsuario(leerSesion()?.usuario ?? null)
    window.addEventListener(EVENTO_SESION, sincronizar)
    return () => window.removeEventListener(EVENTO_SESION, sincronizar)
  }, [])

  useEffect(() => {
    if (!verificando) return undefined
    let vigente = true
    sesionActual()
      .then((datos) => {
        // El rol pudo cambiar desde el último inicio de sesión (HU-02): se usa el actual.
        if (vigente) actualizarUsuario(datos)
      })
      .catch(() => {
        // 401 ya borra la sesión en api.js; cualquier otro fallo se deja para el siguiente intento.
      })
      .finally(() => {
        if (vigente) setVerificando(false)
      })
    return () => {
      vigente = false
    }
  }, [verificando])

  const entrar = useCallback(async (correo, contrasena) => {
    const respuesta = await iniciarSesion(correo, contrasena)
    guardarSesion(respuesta)
    return respuesta.usuario
  }, [])

  const salir = useCallback(async () => {
    try {
      await cerrarSesionEnServidor()
    } catch {
      // Aunque Identidad no responda, la sesión se cierra en el navegador.
    } finally {
      borrarSesion()
    }
  }, [])

  const valor = useMemo(() => ({ usuario, verificando, entrar, salir }), [usuario, verificando, entrar, salir])
  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>
}

export function useSesion() {
  const valor = useContext(Contexto)
  if (!valor) throw new Error('useSesion debe usarse dentro de <ProveedorSesion>')
  return valor
}
