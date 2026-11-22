// HU-01 · Iniciar sesión. Responsable: Matheus.
// Criterios: con credenciales válidas entra; con inválidas se rechaza sin decir qué dato falló;
// puede cerrar sesión (botón de la barra lateral); la consulta pública no pide sesión.
import { useState } from 'react'
import { ir } from '../../navegacion.js'
import { destinoTrasEntrar, RUTA_INICIO } from '../../paginas.js'
import { useSesion } from '../../SesionContexto.jsx'
import { mensajeErrorEntrar, validarCredenciales } from './entrar.js'
import './entrar.css'

const USUARIOS_DEMO = ['investigador', 'cientifico', 'altorango', 'auditor', 'admin', 'sinrol']

export default function Entrar({ volver, aviso }) {
  const { entrar } = useSesion()
  const [correo, setCorreo] = useState('')
  const [contrasena, setContrasena] = useState('')
  const [verContrasena, setVerContrasena] = useState(false)
  const [mayusculas, setMayusculas] = useState(false)
  const [enviando, setEnviando] = useState(false)
  const [errores, setErrores] = useState({})
  const [error, setError] = useState('')

  async function enviar(evento) {
    evento.preventDefault()
    const encontrados = validarCredenciales(correo, contrasena)
    setErrores(encontrados)
    setError('')
    if (Object.keys(encontrados).length > 0) return

    setEnviando(true)
    try {
      const usuario = await entrar(correo.trim(), contrasena)
      ir(destinoTrasEntrar(volver, usuario))
    } catch (fallo) {
      setError(mensajeErrorEntrar(fallo))
      setContrasena('')
    } finally {
      setEnviando(false)
    }
  }

  function revisarMayusculas(evento) {
    setMayusculas(Boolean(evento.getModifierState?.('CapsLock')))
  }

  function usarDemo(nombre) {
    setCorreo(`${nombre}@biohub.local`)
    setErrores({})
    setError('')
  }

  return (
    <section className="entrar-tarjeta">
      <aside className="entrar-presentacion" aria-hidden="true">
        <span className="entrar-hoja">❧</span>
        <h2>Bienvenido de nuevo al inventario nacional</h2>
        <p>Registra hallazgos, revisa su historia y protege la ubicación de las especies en peligro.</p>
        <ul>
          <li>Cada rol ve solo las funciones que le corresponden.</li>
          <li>Las coordenadas exactas solo las ve el personal de alto rango.</li>
          <li>Tu sesión se cierra al cerrar la pestaña.</li>
        </ul>
      </aside>

      <div className="entrar-formulario">
        <span className="etiqueta-superior">PERSONAL DEL INSTITUTO</span>
        <h2>Iniciar sesión</h2>
        <p className="texto-suave">Entra con tu cuenta interna de BioHub.</p>
        {aviso && <p className="aviso-sesion" role="status">{aviso}</p>}

        <form className="formulario-entrar" onSubmit={enviar} noValidate>
          <label>
            <span>Correo</span>
            <input
              type="email"
              name="correo"
              autoComplete="username"
              placeholder="nombre@biohub.local"
              value={correo}
              onChange={(evento) => setCorreo(evento.target.value)}
              aria-invalid={Boolean(errores.correo)}
              aria-describedby={errores.correo ? 'error-correo' : undefined}
              autoFocus
            />
            {errores.correo && <small id="error-correo" className="entrar-error-campo">{errores.correo}</small>}
          </label>

          <label>
            <span>Contraseña</span>
            <div className="entrar-campo-clave">
              <input
                type={verContrasena ? 'text' : 'password'}
                name="contrasena"
                autoComplete="current-password"
                value={contrasena}
                onChange={(evento) => setContrasena(evento.target.value)}
                onKeyUp={revisarMayusculas}
                onKeyDown={revisarMayusculas}
                aria-invalid={Boolean(errores.contrasena)}
                aria-describedby={errores.contrasena ? 'error-contrasena' : undefined}
              />
              <button
                type="button"
                className="entrar-ver-clave"
                onClick={() => setVerContrasena((valor) => !valor)}
                aria-pressed={verContrasena}
              >
                {verContrasena ? 'Ocultar' : 'Mostrar'}
              </button>
            </div>
            {errores.contrasena && <small id="error-contrasena" className="entrar-error-campo">{errores.contrasena}</small>}
            {mayusculas && <small className="entrar-aviso-mayus">Las mayúsculas están activadas.</small>}
          </label>

          {error && <p className="aviso-error" role="alert">{error}</p>}

          <button type="submit" className="boton boton-primario" disabled={enviando}>
            {enviando ? 'Entrando…' : 'Entrar'}
          </button>
        </form>

        <a className="entrar-volver" href={`#${RUTA_INICIO}`}>← Ir a la consulta pública (no necesita sesión)</a>

        {import.meta.env.DEV && (
          <div className="ayuda-demo">
            <span>Usuarios de prueba (contraseña <code>BioHub2026!</code>):</span>
            <div className="entrar-demo">
              {USUARIOS_DEMO.map((nombre) => (
                <button key={nombre} type="button" onClick={() => usarDemo(nombre)}>{nombre}@</button>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  )
}
