
import { useEffect, useMemo, useRef, useState } from 'react'
import L from 'leaflet'
import { listarHallazgos, obtenerUbicacion } from '../../api.js'
import './mapa.css'

const POR_PAGINA = 100
const MAX_REGISTROS = 5000

export default function UbicacionHallazgo() {
  const contenedorMapa = useRef(null)
  const mapa = useRef(null)
  const capaMarcadores = useRef(null)

  const [hallazgos, setHallazgos] = useState([])
  const [seleccionado, setSeleccionado] = useState('')
  const [ubicacion, setUbicacion] = useState(null)
  const [cargando, setCargando] = useState(true)
  const [cargandoUbicacion, setCargandoUbicacion] = useState(false)
  const [error, setError] = useState('')
  const [errorUbicacion, setErrorUbicacion] = useState('')

  // Cargar los hallazgos públicos.
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

  const departamentos = useMemo(
    () => new Set(
      hallazgos.map((hallazgo) => hallazgo.departamento).filter(Boolean)
    ).size,
    [hallazgos]
  )

  const especiesUnicas = useMemo(
    () => new Set(
      hallazgos.map((hallazgo) => hallazgo.especie).filter(Boolean)
    ).size,
    [hallazgos]
  )

  const hallazgoActivo = hallazgos.find(
    (hallazgo) => hallazgo.hallazgo_id === seleccionado
  )

  // Consultar la ubicación autorizada para el hallazgo seleccionado.
  useEffect(() => {
    if (!seleccionado) {
      setUbicacion(null)
      setErrorUbicacion('')
      setCargandoUbicacion(false)
      return
    }

    const controlador = new AbortController()

    async function consultarUbicacion() {
      setUbicacion(null)
      setErrorUbicacion('')
      setCargandoUbicacion(true)

      try {
        const respuesta = await obtenerUbicacion(seleccionado, {
          signal: controlador.signal,
        })

        if (!controlador.signal.aborted) {
          setUbicacion(respuesta)
        }
      } catch (err) {
        if (!controlador.signal.aborted) {
          setErrorUbicacion(
            err.message || 'No fue posible consultar la ubicación.'
          )
        }
      } finally {
        if (!controlador.signal.aborted) {
          setCargandoUbicacion(false)
        }
      }
    }

    consultarUbicacion()
    return () => controlador.abort()
  }, [seleccionado])

  // Inicializar el mapa.
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

  // Mostrar un marcador únicamente cuando el PDP autoriza ubicación exacta.
  useEffect(() => {
    if (!mapa.current || !capaMarcadores.current) return

    capaMarcadores.current.clearLayers()

    if (!ubicacion || ubicacion.nivelUbicacion !== 'EXACTA') return

    const tieneCoordenadas =
      ubicacion.latitud !== null &&
      ubicacion.latitud !== undefined &&
      ubicacion.latitud !== '' &&
      ubicacion.longitud !== null &&
      ubicacion.longitud !== undefined &&
      ubicacion.longitud !== ''

    if (!tieneCoordenadas) return

    const latitud = Number(ubicacion.latitud)
    const longitud = Number(ubicacion.longitud)

    if (
      !Number.isFinite(latitud) ||
      !Number.isFinite(longitud) ||
      latitud < -90 ||
      latitud > 90 ||
      longitud < -180 ||
      longitud > 180
    ) return

    const marcador = L.marker([latitud, longitud])
      .bindPopup(
        `<strong>${hallazgoActivo?.especie || 'Hallazgo seleccionado'}</strong>`
      )

    marcador.addTo(capaMarcadores.current)
    marcador.openPopup()

    mapa.current.flyTo([latitud, longitud], 12, { duration: 0.8 })
  }, [ubicacion, hallazgoActivo])

  function seleccionarHallazgo(hallazgo) {
    setSeleccionado(hallazgo.hallazgo_id)
  }

  return (
    <main className="mapa-pagina">
      <header className="mapa-encabezado">
        <span className="etiqueta-superior">
          BIOHUB · EXPLORACIÓN GEOGRÁFICA
        </span>
        <h1>Biodiversidad en Colombia</h1>
        <p>
          Explora los registros públicos de flora y fauna.
          Selecciona un hallazgo para consultar su ubicación
          según los permisos establecidos por el sistema.
        </p>
      </header>

      <section className="mapa-resumen">
        <article className="mapa-indicador">
          <span>Hallazgos públicos</span>
          <strong>{cargando ? '—' : hallazgos.length}</strong>
        </article>

        <article className="mapa-indicador">
          <span>Departamentos registrados</span>
          <strong>{cargando ? '—' : departamentos}</strong>
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
            <p>
              El marcador aparece únicamente cuando se autoriza
              la ubicación exacta.
            </p>
          </header>

          <div
            ref={contenedorMapa}
            className="mapa-lienzo"
            aria-label="Mapa interactivo de Colombia"
          />
        </article>

        <aside className="mapa-detalle">
          <header className="mapa-detalle-titulo">
            <h2>Hallazgos</h2>
            <p>Selecciona un registro para consultar su ubicación.</p>
          </header>

          {cargando && (
            <div className="mapa-estado">
              Cargando registros públicos...
            </div>
          )}

          {!cargando && !error && hallazgos.length === 0 && (
            <div className="mapa-estado">
              Todavía no hay hallazgos públicos disponibles.
            </div>
          )}

          {!cargando && (
            <div className="mapa-detalle-lista">
              {hallazgos.map((hallazgo) => (
                <button
                  key={hallazgo.hallazgo_id}
                  type="button"
                  className={`mapa-departamento ${
                    seleccionado === hallazgo.hallazgo_id ? 'activo' : ''
                  }`}
                  onClick={() => seleccionarHallazgo(hallazgo)}
                >
                  <span>
                    <strong>
                      {hallazgo.especie || 'Especie sin identificar'}
                    </strong>
                    <small>
                      {hallazgo.departamento || hallazgo.region || 'Ubicación general no especificada'}
                    </small>
                  </span>
                  <span className="mapa-cantidad">›</span>
                </button>
              ))}
            </div>
          )}

          {hallazgoActivo && (
            <section className="mapa-especies">
              <h3>Ubicación del hallazgo</h3>

              <article className="mapa-especie">
                <strong>
                  {hallazgoActivo.especie || 'Especie sin identificar'}
                </strong>
                <span>
                  {hallazgoActivo.ecosistema || 'Ecosistema no especificado'}
                </span>
              </article>

              {cargandoUbicacion && (
                <div className="mapa-estado">
                  Consultando permisos y ubicación...
                </div>
              )}

              {errorUbicacion && (
                <div className="mapa-estado" role="alert">
                  {errorUbicacion}
                </div>
              )}

              {ubicacion?.nivelUbicacion === 'REGION' && (
                <div className="mapa-estado">
                  <strong>Ubicación general autorizada</strong>
                  <p>Región: {ubicacion.region || 'No especificada'}</p>
                  <p>
                    Departamento:{' '}
                    {ubicacion.departamento || 'No especificado'}
                  </p>
                  <p>
                    No se muestran coordenadas exactas para este nivel
                    de autorización.
                  </p>
                </div>
              )}

              {ubicacion?.nivelUbicacion === 'EXACTA' && (
                <div className="mapa-estado">
                  <strong>Ubicación exacta autorizada</strong>
                  <p>
                    {ubicacion.departamento || ubicacion.region || 'Ubicación disponible'}
                  </p>
                  {ubicacion.precisionM != null && (
                    <p>Precisión: {ubicacion.precisionM} m</p>
                  )}
                </div>
              )}
            </section>
          )}
        </aside>
      </section>

      <p className="mapa-nota">
        Privacidad de los registros: cada consulta de ubicación
        es validada por el sistema de autorización PDP.
        Las coordenadas exactas solo se muestran cuando el
        nivel de autorización recibido es EXACTA. En los demás
        casos se presenta únicamente la información geográfica
        general permitida.
      </p>
    </main>
  )
}
