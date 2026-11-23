// Lista de hallazgos para escoger uno. La usan Reclasificar (HU-08) e Historial (HU-12).
// Los datos vienen de Consulta (GET /api/v1/consulta/hallazgos), que solo trae datos públicos.
import { useEffect, useMemo, useState } from 'react'
import { listarHallazgos } from '../../api.js'
import { fechaCorta, filtrarHallazgos, mensajeError, nombreLugar } from './utilidades.js'

const LIMITE = 100

export default function SelectorHallazgo({ seleccionado, onSeleccionar, recarga = 0 }) {
  const [hallazgos, setHallazgos] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)
  const [busqueda, setBusqueda] = useState('')
  const [intento, setIntento] = useState(0)

  useEffect(() => {
    const control = new AbortController()
    setCargando(true)
    setError(null)
    listarHallazgos({ limite: LIMITE, desplazamiento: 0, signal: control.signal })
      .then((datos) => setHallazgos(Array.isArray(datos?.hallazgos) ? datos.hallazgos : []))
      .catch((e) => { if (e.name !== 'AbortError') setError(e) })
      .finally(() => { if (!control.signal.aborted) setCargando(false) })
    return () => control.abort()
  }, [recarga, intento])

  const visibles = useMemo(() => filtrarHallazgos(hallazgos, busqueda), [hallazgos, busqueda])

  return (
    <section className="gob-panel gob-selector">
      <div className="seccion-titulo">
        <div>
          <span className="etiqueta-superior">PASO 1</span>
          <h2>Escoge el hallazgo</h2>
        </div>
        {!cargando && !error && <span className="texto-suave">{hallazgos.length} hallazgos</span>}
      </div>

      <label className="buscador gob-buscador">
        <span className="icono" aria-hidden="true">⌕</span>
        <input
          type="search"
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          placeholder="Buscar por especie, región o ecosistema"
          aria-label="Buscar hallazgo"
        />
      </label>

      {error && (
        <div className="aviso-error" role="alert">
          <span>{mensajeError(error)}</span>
          <button type="button" className="boton boton-secundario" onClick={() => setIntento((n) => n + 1)}>Reintentar</button>
        </div>
      )}

      {cargando && <p className="cargando-linea">Cargando hallazgos…</p>}

      {!cargando && !error && visibles.length === 0 && (
        <p className="texto-suave gob-vacio-corto">
          {hallazgos.length === 0 ? 'Todavía no hay hallazgos registrados.' : 'Ningún hallazgo coincide con la búsqueda.'}
        </p>
      )}

      {/* role="list": Safari quita la semántica de lista cuando se le quitan las viñetas. */}
      <ul className="gob-lista" role="list" aria-label="Hallazgos">
        {visibles.map((h) => {
          const activo = seleccionado?.hallazgo_id === h.hallazgo_id
          return (
            <li key={h.hallazgo_id}>
              <button
                type="button"
                aria-pressed={activo}
                className={`gob-opcion${activo ? ' activo' : ''}`}
                onClick={() => onSeleccionar(h)}
              >
                <em>{h.especie}</em>
                <span>{nombreLugar(h)}{h.ecosistema ? ` · ${h.ecosistema}` : ''}</span>
                <small>{fechaCorta(h.fecha_hallazgo)} · versión {h.version ?? 1}</small>
              </button>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
