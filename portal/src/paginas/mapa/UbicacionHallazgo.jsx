import { useEffect, useMemo, useRef, useState } from 'react'
import L from 'leaflet'
import { listarHallazgos } from '../../api.js'
import './mapa.css'

// Referencias geográficas aproximadas de ciudades representativas.
// No son coordenadas de los hallazgos ni de especies individuales.
const REFERENCIAS = {
  Amazonas: [-4.2153, -69.9406],
  Boyacá: [5.5353, -73.3678],
  Cundinamarca: [5.0221, -74.0048],
  Quindío: [4.5339, -75.6811],
}

const POR_PAGINA = 12
const MAX_REGISTROS = 5000

export default function UbicacionHallazgo() {
  const contenedorMapa = useRef(null)
  const mapa = useRef(null)
  const capaMarcadores = useRef(null)

  const [hallazgos, setHallazgos] = useState([])
  const [seleccionado, setSeleccionado] = useState('')
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const controlador = new AbortController()

    async function cargarHallazgos() {
      setCargando(true)
      setError('')

      try {
        const registros = []
        let desplazamiento = 0

        while (registros.length < MAX_REGISTROS) {
          const respuesta = await listarHallazgos({
            limite: POR_PAGINA,
            desplazamiento,
            signal: controlador.signal,
          })

          const pagina = respuesta?.hallazgos || []
          registros.push(...pagina)

          if (pagina.length < POR_PAGINA) break
          desplazamiento += POR_PAGINA
        }

        if (!controlador.signal.aborted) {
          setHallazgos(registros)
        }
      } catch (err) {
        if (!controlador.signal.aborted) {
          setError(err.message || 'No fue posible cargar los hallazgos.')
        }
      } finally {
        if (!controlador.signal.aborted) setCargando(false)
      }
    }

    cargarHallazgos()
    return () => controlador.abort()
  }, [])

  const departamentos = useMemo(() => {
    const grupos = new Map()

    hallazgos.forEach((hallazgo) => {
      const nombre = hallazgo.departamento?.trim()
      if (!nombre) return

      if (!grupos.has(nombre)) grupos.set(nombre, [])
      grupos.get(nombre).push(hallazgo)
    })

    return [...grupos.entries()]
      .map(([nombre, registros]) => ({
        nombre,
        registros,
        coordenadas: REFERENCIAS[nombre] || null,
      }))
      .sort((a, b) => a.nombre.localeCompare(b.nombre, 'es'))
  }, [hallazgos])

  const departamentoActivo = departamentos.find(
    (departamento) => departamento.nombre === seleccionado
  )

  const especiesUnicas = useMemo(
    () => new Set(hallazgos.map((hallazgo) => hallazgo.especie).filter(Boolean)).size,
    [hallazgos]
  )

  useEffect(() => {
    if (!contenedorMapa.current || mapa.current) return

    const instancia = L.map(contenedorMapa.current, {
      scrollWheelZoom: true,
    }).setView([4.5, -73.5], 5)

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 18,
    }).addTo(instancia)

    mapa.current = instancia
    capaMarcadores.current = L.layerGroup().addTo(instancia)

    const ajustarTamano = () => instancia.invalidateSize()
    window.addEventListener('resize', ajustarTamano)

    return () => {
      window.removeEventListener('resize', ajustarTamano)
      instancia.remove()
      mapa.current = null
      capaMarcadores.current = null
    }
  }, [])

  useEffect(() => {
    if (!mapa.current || !capaMarcadores.current) return

    capaMarcadores.current.clearLayers()

    departamentos.forEach((departamento) => {
      if (!departamento.coordenadas) return

      const icono = L.divIcon({
        className: '',
        html: `<div class="mapa-punto">${departamento.registros.length}</div>`,
        iconSize: [34, 34],
        iconAnchor: [17, 17],
      })

      const marcador = L.marker(departamento.coordenadas, { icon: icono })

      marcador.on('click', () => setSeleccionado(departamento.nombre))
      marcador.addTo(capaMarcadores.current)
    })
  }, [departamentos])

  function seleccionarDepartamento(departamento) {
    setSeleccionado(departamento.nombre)

    if (departamento.coordenadas && mapa.current) {
      mapa.current.flyTo(departamento.coordenadas, 7, { duration: 0.8 })
    }
  }

  return (
    <main className="mapa-pagina">
      <header className="mapa-encabezado">
        <span className="etiqueta-superior">BIOHUB · EXPLORACIÓN GEOGRÁFICA</span>
        <h1>Biodiversidad en Colombia</h1>
        <p>
          Explora los registros públicos de flora y fauna por departamento.
          Selecciona un marcador para conocer las especies registradas.
        </p>
      </header>

      <section className="mapa-resumen">
        <article className="mapa-indicador">
          <span>Hallazgos públicos</span>
          <strong>{cargando ? '—' : hallazgos.length}</strong>
        </article>
        <article className="mapa-indicador">
          <span>Departamentos registrados</span>
          <strong>{cargando ? '—' : departamentos.length}</strong>
        </article>
        <article className="mapa-indicador">
          <span>Especies diferentes</span>
          <strong>{cargando ? '—' : especiesUnicas}</strong>
        </article>
      </section>

      {error && (
        <div className="aviso-error" role="alert">
          <span>{error}</span>
          <button
            className="boton boton-secundario"
            onClick={() => window.location.reload()}
          >
            Reintentar
          </button>
        </div>
      )}

      <section className="mapa-contenido">
        <article className="mapa-panel">
          <header className="mapa-panel-titulo">
            <h2>Mapa de Colombia</h2>
            <p>Los números indican los hallazgos públicos por departamento.</p>
          </header>
          <div
            ref={contenedorMapa}
            className="mapa-lienzo"
            aria-label="Mapa interactivo de Colombia"
          />
        </article>

        <aside className="mapa-detalle">
          <header className="mapa-detalle-titulo">
            <h2>Departamentos</h2>
            <p>Selecciona uno para consultar sus registros.</p>
          </header>

          {cargando && <div className="mapa-estado">Cargando registros públicos...</div>}

          {!cargando && !error && departamentos.length === 0 && (
            <div className="mapa-estado">
              Todavía no hay hallazgos públicos disponibles.
            </div>
          )}

          {!cargando && (
            <div className="mapa-detalle-lista">
              {departamentos.map((departamento) => (
                <button
                  key={departamento.nombre}
                  type="button"
                  className={`mapa-departamento ${seleccionado === departamento.nombre ? 'activo' : ''}`}
                  onClick={() => seleccionarDepartamento(departamento)}
                >
                  <span>
                    <strong>{departamento.nombre}</strong>
                    <small>
                      {departamento.coordenadas
                        ? 'Referencia geográfica disponible'
                        : 'Sin marcador geográfico disponible'}
                    </small>
                  </span>
                  <span className="mapa-cantidad">
                    {departamento.registros.length}
                  </span>
                </button>
              ))}
            </div>
          )}

          {departamentoActivo && (
            <section className="mapa-especies">
              <h3>Especies en {departamentoActivo.nombre}</h3>
              {departamentoActivo.registros.map((hallazgo) => (
                <article className="mapa-especie" key={hallazgo.hallazgo_id}>
                  <strong>{hallazgo.especie || 'Especie sin identificar'}</strong>
                  <span>
                    {hallazgo.ecosistema || 'Ecosistema no especificado'}
                  </span>
                </article>
              ))}
            </section>
          )}
        </aside>
      </section>

      <p className="mapa-nota">
        Privacidad de los registros: los marcadores representan referencias
        geográficas generales y no indican el lugar exacto de los hallazgos.
        Algunos departamentos pueden aparecer en el listado sin marcador
        mientras no tengan una referencia geográfica configurada.
      </p>
    </main>
  )
}

