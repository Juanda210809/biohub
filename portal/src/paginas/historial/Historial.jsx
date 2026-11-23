// HU-12 · Reconstrucción histórica de un hallazgo. Responsable: Guarnizo.
// El auditor escoge un hallazgo y una fecha, y ve qué se creía ese día comparado con hoy.
import { useId, useState } from 'react'
import { pedir } from '../../api.js'
import SelectorHallazgo from '../reclasificar/SelectorHallazgo.jsx'
import {
  autorCorto, etiquetaCampo, fechaConHora, fechaCorta, hoyIso, mensajeError, valorLegible,
} from '../reclasificar/utilidades.js'
import '../reclasificar/pantallas.css'

function TarjetaVersion({ titulo, version, hoy = false }) {
  return (
    <article className={`gob-version${hoy ? ' hoy' : ''}`}>
      <span className="etiqueta-superior">{titulo} · VERSIÓN {version.numero}</span>
      <em>{version.especie}</em>
      <p className="gob-meta">
        {autorCorto(version.autorId)} · vigente desde {fechaConHora(version.vigenteDesde)}
      </p>
      {version.justificacion && <p className="gob-meta">«{version.justificacion}»</p>}
    </article>
  )
}

export default function Historial() {
  const id = useId()
  const [hallazgo, setHallazgo] = useState(null)
  const [fecha, setFecha] = useState(hoyIso())
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState(null)
  const [datos, setDatos] = useState(null)

  function escoger(h) {
    setHallazgo(h)
    setDatos(null)
    setError(null)
  }

  async function reconstruir(evento) {
    evento.preventDefault()
    if (!hallazgo || !fecha) return
    setCargando(true)
    setError(null)
    setDatos(null)
    try {
      const parametros = new URLSearchParams({ fecha })
      setDatos(await pedir(
        `/api/v1/gobernanza/hallazgos/${encodeURIComponent(hallazgo.hallazgo_id)}/historial?${parametros}`,
      ))
    } catch (e) {
      setError(e)
    } finally {
      setCargando(false)
    }
  }

  const pista = Array.isArray(error?.detalles) ? error.detalles.map((d) => d?.mensaje).filter(Boolean).join(' ') : ''

  return (
    <div className="gob-pagina">
      <header className="gob-encabezado">
        <span className="etiqueta-superior">AUDITORÍA · HU-12</span>
        <h1>¿Qué se creía en esa fecha?</h1>
        <p>Escoge un hallazgo y un día. Verás la versión que estaba vigente entonces, la de hoy y qué cambió entre las dos.</p>
      </header>

      <div className="gob-columnas">
        <SelectorHallazgo seleccionado={hallazgo} onSeleccionar={escoger} />

        <div className="gob-pagina">
          <section className="gob-panel">
            <div className="seccion-titulo">
              <div>
                <span className="etiqueta-superior">PASO 2</span>
                <h2>{hallazgo ? <em>{hallazgo.especie}</em> : 'Escoge la fecha'}</h2>
              </div>
            </div>
            <form className="gob-filtro-fecha" onSubmit={reconstruir}>
              <label className="gob-campo">
                Fecha
                <input type="date" value={fecha} max={hoyIso()} onChange={(e) => setFecha(e.target.value)} required />
              </label>
              <button type="submit" className="boton boton-primario" disabled={!hallazgo || !fecha || cargando}>
                {cargando ? 'Reconstruyendo…' : 'Reconstruir'}
              </button>
              {!hallazgo && <span className="texto-suave">Primero escoge un hallazgo de la lista.</span>}
            </form>
          </section>

          {error && (
            <div className="aviso-error" role="alert">
              <span>{mensajeError(error)}{pista ? ` ${pista}` : ''}</span>
            </div>
          )}

          {!datos && !error && (
            <div className="estado-vacio">
              <span className="estado-icono" aria-hidden="true">🕰️</span>
              <h3>La comparación aparecerá aquí</h3>
              <p>Cada reclasificación crea una versión nueva, así que siempre se puede saber qué se sabía en un día dado.</p>
            </div>
          )}

          {datos && (
            <>
              <div className="gob-comparacion">
                <TarjetaVersion titulo={`EL ${fechaCorta(datos.fecha).toUpperCase()}`} version={datos.enFecha} />
                <span className="gob-flecha" aria-hidden="true">→</span>
                <TarjetaVersion titulo="HOY" version={datos.actual} hoy />
              </div>

              <section className="gob-panel">
                <div className="seccion-titulo">
                  <h2>
                    {datos.versionesPosteriores === 0
                      ? 'Esa sigue siendo la versión vigente'
                      : `Qué cambió · ${datos.versionesPosteriores} ${datos.versionesPosteriores === 1 ? 'versión' : 'versiones'} después`}
                  </h2>
                </div>
                {datos.cambios?.length ? (
                  <div className="gob-tabla-envoltura" tabIndex={0} role="region" aria-labelledby={`${id}-cambios`}>
                    <table className="gob-tabla">
                      <caption id={`${id}-cambios`} className="visually-hidden">
                        Cambios del hallazgo entre el {fechaCorta(datos.fecha)} y hoy
                      </caption>
                      <thead>
                        <tr><th scope="col">Dato</th><th scope="col">Antes</th><th scope="col">Ahora</th></tr>
                      </thead>
                      <tbody>
                        {datos.cambios.map((c) => (
                          <tr key={c.campo}>
                            <th scope="row">{etiquetaCampo(c.campo)}</th>
                            <td className="antes">{valorLegible(c.antes)}</td>
                            <td className="ahora">{valorLegible(c.ahora)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="texto-suave">No hay diferencias entre esa fecha y hoy.</p>
                )}
              </section>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
