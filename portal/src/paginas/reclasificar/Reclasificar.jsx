// HU-08 · Reclasificar hallazgo. Responsable: Guarnizo.
// El científico autorizado escoge un hallazgo, la especie correcta y escribe por qué.
// Gobernanza guarda el cambio como una versión nueva; la anterior no se borra.
import { useEffect, useId, useMemo, useRef, useState } from 'react'
import { pedir } from '../../api.js'
import { useSesion } from '../../SesionContexto.jsx'
import SelectorHallazgo from './SelectorHallazgo.jsx'
import {
  erroresPorCampo, especiesDestino, fechaConHora, fechaCorta, mensajeError, nombreLugar,
} from './utilidades.js'
import './pantallas.css'

const MAXIMO_JUSTIFICACION = 1000

// Mensaje de cada campo cuando el navegador lo marca como inválido (vacío).
const FALTA = {
  especieId: { etiqueta: 'Especie correcta', mensaje: 'Escoge la especie correcta.' },
  justificacion: { etiqueta: 'Justificación', mensaje: 'La justificación es obligatoria.' },
}

// ¿El usuario ya tocó el campo y quedó mal? Igual que :user-invalid en CSS, para que el lector
// de pantalla diga "inválido" al mismo tiempo que se ve en rojo, y no antes de que escriba.
function marcadoPorUsuario(campo) {
  try {
    return campo.matches(':user-invalid')
  } catch {
    return !campo.validity.valid // navegadores viejos sin :user-invalid
  }
}

export default function Reclasificar() {
  const { usuario } = useSesion()
  const id = useId()
  const [hallazgo, setHallazgo] = useState(null)
  const [especies, setEspecies] = useState([])
  const [errorEspecies, setErrorEspecies] = useState(null)
  const [especieId, setEspecieId] = useState('')
  const [justificacion, setJustificacion] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState(null)
  const [resultado, setResultado] = useState(null)
  const [recarga, setRecarga] = useState(0)
  const [invalidos, setInvalidos] = useState({})
  const [anuncio, setAnuncio] = useState('')
  const temporizador = useRef(null)
  const anunciados = useRef(new Set())

  useEffect(() => {
    const control = new AbortController()
    pedir('/api/v1/registro/especies', { signal: control.signal })
      .then((datos) => setEspecies(Array.isArray(datos) ? datos : []))
      .catch((e) => { if (e.name !== 'AbortError') setErrorEspecies(e) })
    return () => {
      control.abort()
      clearTimeout(temporizador.current)
    }
  }, [])

  const opciones = useMemo(() => especiesDestino(especies, hallazgo?.especie), [especies, hallazgo])
  const erroresServidor = erroresPorCampo(error)

  // Texto de error que se ve (y se lee) debajo de cada campo: primero lo que dijo el backend,
  // si no, el de campo vacío cuando el navegador ya lo marcó.
  function errorDe(nombre) {
    return erroresServidor[nombre] || (invalidos[nombre] ? FALTA[nombre].mensaje : '')
  }

  function sincronizar(campo, anunciar) {
    const nombre = campo?.name
    if (!FALTA[nombre]) return
    const invalido = marcadoPorUsuario(campo)
    setInvalidos((previo) => (previo[nombre] === invalido ? previo : { ...previo, [nombre]: invalido }))
    if (invalido && anunciar && !anunciados.current.has(nombre)) {
      anunciados.current.add(nombre)
      clearTimeout(temporizador.current)
      setAnuncio('')
      // Medio segundo después, para no hablar encima del campo al que pasó el foco.
      temporizador.current = setTimeout(() => setAnuncio(`${FALTA[nombre].etiqueta}: error, ${FALTA[nombre].mensaje}`), 500)
    }
    if (!invalido) {
      anunciados.current.delete(nombre)
      setAnuncio('')
    }
  }

  function escoger(h) {
    setHallazgo(h)
    setEspecieId('')
    setJustificacion('')
    setError(null)
    setResultado(null)
    setInvalidos({})
    anunciados.current.clear()
  }

  async function enviar(evento) {
    evento.preventDefault()
    if (!hallazgo || enviando) return
    setEnviando(true)
    setError(null)
    try {
      const respuesta = await pedir(
        `/api/v1/gobernanza/hallazgos/${encodeURIComponent(hallazgo.hallazgo_id)}/reclasificaciones`,
        { method: 'POST', body: { especieId, justificacion: justificacion.trim() } },
      )
      setResultado(respuesta)
      // Lo que se ve en pantalla queda al día sin esperar a que Consulta replique.
      setHallazgo((h) => ({ ...h, especie: respuesta.especieNueva, version: respuesta.version }))
      setEspecieId('')
      setJustificacion('')
      setInvalidos({})
      setRecarga((n) => n + 1)
    } catch (e) {
      setError(e)
      // Si el backend señaló un campo, el foco va a ese campo para que se lea su error.
      const campo = erroresPorCampo(e)
      const primero = Object.keys(campo)[0]
      if (primero) requestAnimationFrame(() => document.getElementById(`${id}-${primero}`)?.focus())
    } finally {
      setEnviando(false)
    }
  }

  function campoProps(nombre) {
    const mensaje = errorDe(nombre)
    return {
      id: `${id}-${nombre}`,
      name: nombre,
      required: true,
      'aria-invalid': mensaje ? 'true' : 'false',
      // El mensaje solo se enlaza mientras se muestra; si no, el lector lo diría desde el inicio.
      'aria-describedby': mensaje ? `${id}-${nombre}-error` : undefined,
    }
  }

  function errorCampo(nombre) {
    const mensaje = errorDe(nombre)
    if (!mensaje) return null
    return (
      <span id={`${id}-${nombre}-error`} className="gob-error-campo">
        <span role="img" aria-label="Error">⚠</span> {mensaje}
      </span>
    )
  }

  return (
    <div className="gob-pagina">
      <header className="gob-encabezado">
        <span className="etiqueta-superior">GOBERNANZA · HU-08</span>
        <h1>Reclasificar hallazgo</h1>
        <p>
          La clasificación anterior no se borra: el cambio queda como una versión nueva del hallazgo,
          con tu usuario, la fecha y tu justificación. Los datos medidos en campo se conservan.
        </p>
      </header>

      {/* Una sola región "polite" para anunciar errores de campos al salir de ellos. */}
      <p className="visually-hidden" aria-live="polite">{anuncio}</p>

      {resultado && (
        <section className="gob-exito" role="status">
          <strong>Reclasificación guardada como versión {resultado.version}</strong>
          <span className="gob-cambio">
            <em className="gob-tachado">{resultado.especieAnterior}</em>
            <span aria-hidden="true">→</span>
            <span className="visually-hidden">cambió a</span>
            <em>{resultado.especieNueva}</em>
          </span>
          <span>Vigente desde {fechaConHora(resultado.vigenteDesde)}</span>
          <span className="texto-suave">
            La ficha pública puede mostrar la especie anterior hasta por 5 minutos mientras se renueva su caché.
          </span>
        </section>
      )}

      <div className="gob-columnas">
        <SelectorHallazgo seleccionado={hallazgo} onSeleccionar={escoger} recarga={recarga} />

        <section className="gob-panel">
          <div className="seccion-titulo">
            <div>
              <span className="etiqueta-superior">PASO 2</span>
              <h2>Nueva clasificación</h2>
            </div>
          </div>

          {!hallazgo && (
            <div className="estado-vacio">
              <span className="estado-icono" aria-hidden="true">🔎</span>
              <h3>Escoge un hallazgo de la lista</h3>
              <p>Verás su clasificación actual y podrás proponer la especie correcta.</p>
            </div>
          )}

          {hallazgo && (
            <>
              <div className="gob-actual">
                <span className="etiqueta-superior">CLASIFICACIÓN ACTUAL · VERSIÓN {hallazgo.version ?? 1}</span>
                <em>{hallazgo.especie}</em>
                <dl className="gob-datos">
                  <div><dt>Lugar</dt><dd>{nombreLugar(hallazgo)}</dd></div>
                  <div><dt>Ecosistema</dt><dd>{hallazgo.ecosistema || '—'}</dd></div>
                  <div><dt>Fecha del hallazgo</dt><dd>{fechaCorta(hallazgo.fecha_hallazgo)}</dd></div>
                </dl>
              </div>

              {/* Validación nativa: al enviar con algo vacío, el navegador marca los campos y
                  lleva el foco al primero. Por eso el botón no se deshabilita. */}
              <form
                className="gob-formulario"
                onSubmit={enviar}
                onBlur={(e) => sincronizar(e.target, true)}
                onChange={(e) => sincronizar(e.target, e.target.tagName === 'SELECT')}
                onInvalidCapture={(e) => { anunciados.current.add(e.target.name); sincronizar(e.target, false) }}
              >
                <p className="texto-suave gob-nota-obligatorios">Los campos con * son obligatorios.</p>

                {errorEspecies && (
                  <div className="aviso-error" role="alert"><span>No se pudo cargar el catálogo de especies: {mensajeError(errorEspecies)}</span></div>
                )}

                <div className={`gob-campo${errorDe('especieId') ? ' con-error' : ''}`}>
                  <label htmlFor={`${id}-especieId`}>Especie correcta <span aria-hidden="true">*</span></label>
                  <select
                    {...campoProps('especieId')}
                    value={especieId}
                    onChange={(e) => { setEspecieId(e.target.value); setError(null) }}
                    disabled={enviando || !opciones.length}
                  >
                    <option value="">{opciones.length ? 'Escoge la especie…' : 'Cargando especies…'}</option>
                    {opciones.map((e) => (
                      <option key={e.id} value={e.id}>
                        {e.nombreCientifico}{e.nombreComun ? ` · ${e.nombreComun}` : ''}{e.tipoEspecie ? ` (${e.tipoEspecie})` : ''}
                      </option>
                    ))}
                  </select>
                  {errorCampo('especieId')}
                </div>

                <div className={`gob-campo${errorDe('justificacion') ? ' con-error' : ''}`}>
                  <label htmlFor={`${id}-justificacion`}>Justificación <span aria-hidden="true">*</span></label>
                  <span id={`${id}-pista`} className="gob-pista">Queda guardada en el historial. Ej.: análisis genético, muestra LG-2026-114.</span>
                  <textarea
                    {...campoProps('justificacion')}
                    aria-describedby={[`${id}-pista`, campoProps('justificacion')['aria-describedby']].filter(Boolean).join(' ')}
                    value={justificacion}
                    maxLength={MAXIMO_JUSTIFICACION}
                    onChange={(e) => { setJustificacion(e.target.value); setError(null) }}
                    disabled={enviando}
                  />
                  <span className="gob-contador" aria-hidden="true">{justificacion.length}/{MAXIMO_JUSTIFICACION}</span>
                  {errorCampo('justificacion')}
                </div>

                <p className="nota-privacidad">
                  Quedará como <strong>versión {(hallazgo.version ?? 1) + 1}</strong>, registrada por{' '}
                  <strong>{usuario?.nombre || 'tu usuario'}</strong>.
                </p>

                {error && !Object.keys(erroresServidor).length && (
                  <div className="aviso-error" role="alert"><span>{mensajeError(error)}</span></div>
                )}

                <div className="gob-acciones">
                  <button type="submit" className="boton boton-primario" disabled={enviando}>
                    {enviando ? 'Guardando…' : 'Reclasificar'}
                  </button>
                  <button type="button" className="boton boton-secundario" onClick={() => escoger(null)} disabled={enviando}>
                    Cancelar
                  </button>
                </div>
              </form>
            </>
          )}
        </section>
      </div>
    </div>
  )
}
