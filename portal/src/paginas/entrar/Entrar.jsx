// HU-01 · Iniciar sesión (base de la estructura común). Matheus completa el diseño final aquí.
import { useState } from 'react'
import { ir } from '../../navegacion.js'
import { destinoTrasEntrar } from '../../paginas.js'
import { useSesion } from '../../SesionContexto.jsx'

const USUARIOS_DEMO = ['investigador', 'cientifico', 'altorango', 'auditor', 'admin', 'sinrol']

export default function Entrar({ volver, aviso }) {
  const { entrar } = useSesion()
  const [correo, setCorreo] = useState('')
  const [contrasena, setContrasena] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState('')

  async function enviar(evento) {
    evento.preventDefault()
    setEnviando(true)
    setError('')
    try {
      const usuario = await entrar(correo.trim(), contrasena)
      ir(destinoTrasEntrar(volver, usuario))
    } catch (fallo) {
      if (fallo.status === 401) setError('Correo o contraseña incorrectos, o la cuenta está desactivada.')
      else if (fallo.status === 422) setError('Escribe el correo y la contraseña.')
      else setError('No pudimos conectar con BioHub. Verifica que los servicios estén activos.')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <section className="entrar">
      <span className="etiqueta-superior">PERSONAL DEL INSTITUTO</span>
      <h2>Iniciar sesión</h2>
      <p className="texto-suave">Entra con tu cuenta interna. La consulta pública no necesita sesión.</p>
      {aviso && <p className="aviso-sesion" role="status">{aviso}</p>}

      <form className="formulario-entrar" onSubmit={enviar} noValidate>
        <label>
          <span>Correo</span>
          <input
            type="email"
            autoComplete="username"
            value={correo}
            onChange={(evento) => setCorreo(evento.target.value)}
            required
          />
        </label>
        <label>
          <span>Contraseña</span>
          <input
            type="password"
            autoComplete="current-password"
            value={contrasena}
            onChange={(evento) => setContrasena(evento.target.value)}
            required
          />
        </label>
        {error && <p className="aviso-error" role="alert">{error}</p>}
        <button type="submit" className="boton boton-primario" disabled={enviando || !correo || !contrasena}>
          {enviando ? 'Entrando…' : 'Entrar'}
        </button>
      </form>

      {import.meta.env.DEV && (
        <p className="ayuda-demo">
          Usuarios de prueba: {USUARIOS_DEMO.map((nombre) => <code key={nombre}>{nombre}@biohub.local</code>)}
          {' '}con la contraseña <code>BioHub2026!</code>
        </p>
      )}
    </section>
  )
}
