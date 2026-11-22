import { useEffect, useMemo, useState } from 'react'
import { listarHallazgos, obtenerFicha } from './api.js'
import { HALLAZGOS_DEMO } from './datos-demo.js'

const MODO_DEMO = true

const POR_PAGINA = 12

function fechaBonita(valor) {
  if (!valor) return 'Fecha no disponible'
  const fecha = new Date(`${String(valor).slice(0, 10)}T12:00:00`)
  if (Number.isNaN(fecha.getTime())) return String(valor)
  return new Intl.DateTimeFormat('es-CO', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(fecha)
}

function nombreLugar(hallazgo) {
  return [hallazgo.departamento, hallazgo.region].filter(Boolean).join(', ') || 'Ubicación general no disponible'
}

function atributosSeguros(atributos) {
  if (!atributos || typeof atributos !== 'object' || Array.isArray(atributos)) return []
  return Object.entries(atributos).filter(([clave, valor]) => {
    const nombre = clave.toLowerCase()
    return valor !== null && valor !== '' && !/(coord|latitud|longitud|longitude|latitude)/i.test(nombre)
  })
}

function Icono({ tipo }) {
  const iconos = {
    inicio: '⌂', catalogo: '◫', mapa: '⌖', ayuda: '?', hoja: '❧', buscar: '⌕',
  }
  return <span className="icono" aria-hidden="true">{iconos[tipo] || '•'}</span>
}

function MensajeError({ error, onRetry }) {
  const sinPermiso = error?.status === 403
  return (
    <div className="estado-vacio estado-error" role="alert">
      <span className="estado-icono">{sinPermiso ? '🔒' : '⚠️'}</span>
      <h3>{sinPermiso ? 'Consulta temporalmente restringida' : 'No pudimos conectar con BioHub'}</h3>
      <p>
        {sinPermiso
          ? 'El servicio de Identidad todavía no autorizó esta consulta. No mostramos datos de ejemplo para evitar confundirlos con registros reales.'
          : 'Verifica que los servicios estén activos y que Kong esté disponible. Puedes intentar nuevamente.'}
      </p>
      <button type="button" className="boton boton-primario" onClick={onRetry}>Intentar de nuevo</button>
    </div>
  )
}

function obtenerCategoria(hallazgo) {
  const categoria = hallazgo.categoria || hallazgo.atributos_publicos?.categoria
  if (String(categoria || '').toLowerCase() === 'flora') return 'Flora'
  if (String(categoria || '').toLowerCase() === 'fauna') return 'Fauna'

  const tipo = String(hallazgo.atributos_publicos?.tipo || '').toLowerCase()
  const tiposFlora = ['planta', 'palma', 'orquídea', 'orquidea', 'árbol', 'arbol', 'flor', 'frailejón', 'frailejon', 'helecho', 'arbusto']
  return tiposFlora.some((palabra) => tipo.includes(palabra)) ? 'Flora' : 'Fauna'
}

function obtenerVisualEspecie(hallazgo) {
  const nombre = String(hallazgo.especie || '').toLocaleLowerCase('es-CO')
  const categoria = obtenerCategoria(hallazgo)

  if (nombre.includes('colibrí')) return { clase: 'visual-colibri', icono: '🐦', etiqueta: 'Ave', categoria }
  if (nombre.includes('oso')) return { clase: 'visual-oso', icono: '🐻', etiqueta: 'Mamífero', categoria }
  if (nombre.includes('delfín') || nombre.includes('delfin')) return { clase: 'visual-delfin', icono: '🐬', etiqueta: 'Mamífero acuático', categoria }
  if (nombre.includes('palma')) return { clase: 'visual-palma', icono: '🌴', etiqueta: 'Palma', categoria }
  if (nombre.includes('orquídea') || nombre.includes('orquidea') || nombre.includes('cattleya')) return { clase: 'visual-orquidea', icono: '🌸', etiqueta: 'Orquídea', categoria }
  if (nombre.includes('frailejón') || nombre.includes('frailejon')) return { clase: 'visual-frailejon', icono: '🌱', etiqueta: 'Planta de páramo', categoria }
  if (nombre.includes('mariposa')) return { clase: 'visual-mariposa', icono: '🦋', etiqueta: 'Insecto', categoria }
  if (nombre.includes('rana')) return { clase: 'visual-rana', icono: '🐸', etiqueta: 'Anfibio', categoria }
  if (nombre.includes('tucán') || nombre.includes('tucan')) return { clase: 'visual-tucan', icono: '🦜', etiqueta: 'Ave', categoria }
  return { clase: categoria === 'Flora' ? 'visual-flora' : 'visual-fauna', icono: categoria === 'Flora' ? '🌿' : '🦋', etiqueta: categoria, categoria }
}


function obtenerImagenEspecie(hallazgo) {
  const nombre = String(hallazgo.especie || '').toLocaleLowerCase('es-CO')

  if (nombre.includes('colibrí') || nombre.includes('colibri')) return '/imagenes/ColibriEsmeralda.jpg'
  if (nombre.includes('oso')) return '/imagenes/OsoDeAnteojos.jpg'
  if (nombre.includes('delfín') || nombre.includes('delfin')) return '/imagenes/DelfinRosado.jpg'
  if (nombre.includes('palma')) return '/imagenes/PalmaDeCera.jpg'
  if (nombre.includes('orquídea') || nombre.includes('orquidea') || nombre.includes('cattleya')) return '/imagenes/Orquidea.jpg'
  if (nombre.includes('frailejón') || nombre.includes('frailejon')) return '/imagenes/Frailejon.jpg'

  return null
}

function TarjetaHallazgo({ hallazgo, onOpen }) {
  const especie = hallazgo.especie || 'Especie sin identificar'
  const visual = obtenerVisualEspecie(hallazgo)
  const imagen = obtenerImagenEspecie(hallazgo)

  return (
    <button
      type="button"
      className="tarjeta-hallazgo"
      onClick={() => onOpen(hallazgo)}
      aria-label={`Abrir ficha pública de ${especie}`}
    >
      <div className={`tarjeta-ilustracion ${visual.clase}`}>
        {imagen ? (
          <img
            src={imagen}
            alt={`${especie}, ${visual.etiqueta}`}
            className="tarjeta-imagen"
            loading="lazy"
          />
        ) : (
          <>
            <span className="ilustracion-icono" aria-hidden="true">{visual.icono}</span>
            <span className="ilustracion-brillo" aria-hidden="true" />
          </>
        )}
        <span className="ilustracion-etiqueta">{visual.etiqueta}</span>
      </div>
      <div className="tarjeta-contenido">
        <div className={`tarjeta-meta categoria-meta categoria-${visual.categoria.toLowerCase()}`}>
          <span className="punto-verde" /> {visual.categoria.toUpperCase()} · {visual.etiqueta.toUpperCase()}
        </div>
        <h3>{especie}</h3>
        <p className="tarjeta-lugar"><span>⌖</span> {nombreLugar(hallazgo)}</p>
        <div className="tarjeta-pie">
          <span>{hallazgo.ecosistema || 'Ecosistema no especificado'}</span>
          <time dateTime={hallazgo.fecha_hallazgo || undefined}>{fechaBonita(hallazgo.fecha_hallazgo)}</time>
        </div>
      </div>
      <span className="flecha-tarjeta" aria-hidden="true">↗</span>
    </button>
  )
}

function DetalleHallazgo({ hallazgo, ficha, cargando, error, onBack, onRetry }) {
  const datos = ficha || hallazgo
  const atributos = atributosSeguros(datos.atributos_publicos)
  const categoria = obtenerCategoria(datos)
  const imagen = obtenerImagenEspecie(datos)

  return (
    <section className="panel-detalle">
      <button type="button" className="boton-volver" onClick={onBack}>← Volver al listado</button>
      {cargando && <div className="cargando-linea">Cargando ficha pública…</div>}
      {error && <div className="aviso-error"><strong>No fue posible cargar el detalle.</strong><span>{error.message}</span><button type="button" className="boton boton-secundario" onClick={onRetry}>Reintentar</button></div>}
      <div className="detalle-hero">
        <div className={`detalle-emblema categoria-emblema-${categoria.toLowerCase()}`}>
          {imagen ? (
            <img
              src={imagen}
              alt={`Fotografía de ${datos.especie || 'la especie'}`}
              className="detalle-imagen"
              loading="lazy"
            />
          ) : (
            <span aria-hidden="true">
              {categoria === 'Flora' ? '🌿' : '🦋'}
            </span>
          )}
        </div>
        <div>
          <span className="etiqueta-superior">FICHA PÚBLICA · {categoria.toUpperCase()}</span>
          <h2>{datos.especie || 'Especie sin identificar'}</h2>
          <p>{datos.ecosistema || 'Ecosistema no especificado'}</p>
        </div>
      </div>
      <div className="detalle-grid">
        <article className="dato-detalle"><span>Departamento</span><strong>{datos.departamento || 'No disponible'}</strong></article>
        <article className="dato-detalle"><span>Región</span><strong>{datos.region || 'No disponible'}</strong></article>
        <article className="dato-detalle"><span>Fecha del hallazgo</span><strong>{fechaBonita(datos.fecha_hallazgo)}</strong></article>
        <article className="dato-detalle"><span>Última actualización</span><strong>{fechaBonita(datos.actualizado_en)}</strong></article>
      </div>
      <section className="atributos-panel">
        <div className="seccion-titulo"><div><span className="etiqueta-superior">INFORMACIÓN DISPONIBLE</span><h3>Detalles del registro</h3></div></div>
        {atributos.length > 0 ? (
          <dl className="atributos-lista">
            {atributos.map(([clave, valor]) => (
              <div className="atributo-fila" key={clave}><dt>{clave.replaceAll('_', ' ')}</dt><dd>{typeof valor === 'object' ? JSON.stringify(valor) : String(valor)}</dd></div>
            ))}
          </dl>
        ) : <p className="texto-suave">Este registro no tiene atributos públicos adicionales.</p>}
      </section>
      <p className="nota-privacidad">La ficha muestra únicamente información pública. La ubicación exacta y las coordenadas no forman parte de esta consulta.</p>
      {datos.hallazgo_id && <p className="id-registro">Identificador: <code>{datos.hallazgo_id}</code>{datos.version ? ` · Versión ${datos.version}` : ''}</p>}
    </section>
  )
}

export default function App() {
  const [hallazgos, setHallazgos] = useState([])
  const [cantidad, setCantidad] = useState(0)
  const [desplazamiento, setDesplazamiento] = useState(0)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)
  const [busqueda, setBusqueda] = useState('')
  const [regionActiva, setRegionActiva] = useState('Todas')
  const [categoriaActiva, setCategoriaActiva] = useState('Todas')
  const [seleccionado, setSeleccionado] = useState(null)
  const [ficha, setFicha] = useState(null)
  const [cargandoFicha, setCargandoFicha] = useState(false)
  const [errorFicha, setErrorFicha] = useState(null)
  const [recarga, setRecarga] = useState(0)

  useEffect(() => {
    if (MODO_DEMO) {
      setCargando(true)
      setError(null)
      const pagina = HALLAZGOS_DEMO.slice(desplazamiento, desplazamiento + POR_PAGINA)
      setHallazgos(pagina)
      setCantidad(HALLAZGOS_DEMO.length)
      setCargando(false)
      return undefined
    }

    const controlador = new AbortController()
    setCargando(true)
    setError(null)
    listarHallazgos({ limite: POR_PAGINA, desplazamiento, signal: controlador.signal })
      .then((respuesta) => {
        setHallazgos(Array.isArray(respuesta?.hallazgos) ? respuesta.hallazgos : [])
        setCantidad(Number(respuesta?.cantidad) || 0)
      })
      .catch((fallo) => {
        if (fallo.name !== 'AbortError') setError(fallo)
      })
      .finally(() => {
        if (!controlador.signal.aborted) setCargando(false)
      })
    return () => controlador.abort()
  }, [desplazamiento, recarga])

  useEffect(() => {
    if (!seleccionado?.hallazgo_id) return undefined

    if (MODO_DEMO) {
      setCargandoFicha(false)
      setErrorFicha(null)
      setFicha(seleccionado)
      return undefined
    }

    const controlador = new AbortController()
    setCargandoFicha(true)
    setErrorFicha(null)
    setFicha(null)
    obtenerFicha(seleccionado.hallazgo_id, { signal: controlador.signal })
      .then(setFicha)
      .catch((fallo) => {
        if (fallo.name !== 'AbortError') setErrorFicha(fallo)
      })
      .finally(() => {
        if (!controlador.signal.aborted) setCargandoFicha(false)
      })
    return () => controlador.abort()
  }, [seleccionado])

  const regiones = useMemo(() => ['Todas', ...new Set(hallazgos.map((item) => item.region).filter(Boolean))], [hallazgos])
  const filtrados = useMemo(() => {
    const termino = busqueda.trim().toLocaleLowerCase('es-CO')
    return hallazgos.filter((item) => {
      const coincideTexto = !termino || [item.especie, item.departamento, item.region, item.ecosistema, item.categoria, item.atributos_publicos?.tipo]
        .filter(Boolean).some((valor) => String(valor).toLocaleLowerCase('es-CO').includes(termino))
      const coincideRegion = regionActiva === 'Todas' || item.region === regionActiva
      const coincideCategoria = categoriaActiva === 'Todas' || obtenerCategoria(item) === categoriaActiva
      return coincideTexto && coincideRegion && coincideCategoria
    })
  }, [hallazgos, busqueda, regionActiva, categoriaActiva])

  function abrirFicha(hallazgo) {
    setSeleccionado(hallazgo)
    setFicha(null)
    setErrorFicha(null)
  }

  function volverListado() {
    setSeleccionado(null)
    setFicha(null)
    setErrorFicha(null)
  }

  return (
    <div className="app-shell">
      <aside className="barra-lateral">
        <a className="marca" href="#inicio" onClick={volverListado}>
          <span className="marca-icono">B</span><span><strong>BioHub</strong><small>BIODIVERSIDAD COLOMBIA</small></span>
        </a>
        <div className="nav-grupo">
          <span className="nav-etiqueta">ESPACIO DE TRABAJO</span>
          <button className={`nav-enlace ${!seleccionado ? 'activo' : ''}`} onClick={volverListado}><Icono tipo="inicio" />Explorar registros</button>
          <button className="nav-enlace" onClick={() => { setBusqueda(''); setRegionActiva('Todas'); setCategoriaActiva('Todas'); setDesplazamiento(0); volverListado() }}><Icono tipo="catalogo" />Todos los registros</button>
        </div>
        <div className="lateral-inferior">
          <div className="lateral-hoja">❧</div>
          <strong>Conocer para conservar</strong>
          <p>Información pública para descubrir y proteger nuestra biodiversidad.</p>
          <span className="lateral-version">PORTAL DE CONSULTA · MVP</span>
        </div>
      </aside>

      <main className="contenido-principal">
        <header className="barra-superior">
          <div className="migas"><span>BioHub</span><b>/</b><strong>{seleccionado ? 'Ficha pública' : 'Consulta pública'}</strong></div>
          <div className="perfil-publico"><span className="perfil-punto" /> {MODO_DEMO ? 'Modo demostración' : 'Consulta abierta'}</div>
        </header>

        <div className="contenido-pagina">
          {!seleccionado ? (
            <>
              <section className="bienvenida">
                <div className="bienvenida-texto">
                  <span className="etiqueta-superior">SISTEMA NACIONAL DE BIODIVERSIDAD</span>
                  <h1>La biodiversidad de Colombia, <em>al alcance de todos.</em></h1>
                  <p>Explora los registros públicos de registros y descubre la riqueza natural de nuestros ecosistemas.</p>
                </div>
                <div className="bienvenida-ilustracion" aria-hidden="true"><span className="sol" /><span className="hoja hoja-uno">❧</span><span className="hoja hoja-dos">❧</span><span className="ave">⌁</span></div>
                <div className="bienvenida-pie"><span>🌿</span> Datos públicos · Consulta de biodiversidad <span className="bienvenida-separador">•</span> Colombia</div>
              </section>

              <section className="seccion-listado">
                <div className="seccion-titulo">
                  <div>
                    <span className="etiqueta-superior">INVENTARIO NACIONAL</span>
                    <h2>Registros de biodiversidad</h2>
                    <p>Explora especies de flora y fauna de los ecosistemas colombianos.</p>
                    {MODO_DEMO && <p className="aviso-demo" role="note">Datos ficticios de demostración; no corresponden a registros reales.</p>}
                  </div>
                  <div className="contador-registros"><strong>{cargando ? '—' : cantidad}</strong><span>registros disponibles</span></div>
                </div>

                <div className="herramientas-listado">
                  <label className="buscador"><Icono tipo="buscar" /><input
                        value={busqueda}
                        onChange={(evento) => { setBusqueda(evento.target.value); setDesplazamiento(0) }}
                        placeholder="Buscar especie, región o ecosistema…"
                        aria-label="Buscar registros de biodiversidad"
                      /><kbd>⌕</kbd></label>
                  <label className="filtro-region"><span>Región</span><select value={regionActiva} onChange={(evento) => { setRegionActiva(evento.target.value); setDesplazamiento(0) }}><option value="Todas">Todas las regiones</option>{regiones.filter((region) => region !== 'Todas').map((region) => <option key={region} value={region}>{region}</option>)}</select></label>
                  <label className="filtro-region"><span>Tipo</span><select value={categoriaActiva} onChange={(evento) => { setCategoriaActiva(evento.target.value); setDesplazamiento(0) }}><option value="Todas">Flora y fauna</option><option value="Flora">Flora</option><option value="Fauna">Fauna</option></select></label>
                </div>

                {cargando && <div className="rejilla-hallazgos"><div className="skeleton" /><div className="skeleton" /><div className="skeleton" /></div>}
                {!cargando && error && <MensajeError error={error} onRetry={() => setRecarga((valor) => valor + 1)} />}
                {!cargando && !error && filtrados.length === 0 && (
                  <div className="estado-vacio"><span className="estado-icono">🍃</span><h3>{hallazgos.length ? 'No encontramos coincidencias' : 'Aún no hay registros para mostrar'}</h3><p>{hallazgos.length ? 'Prueba con otra búsqueda o selecciona una región diferente.' : 'Cuando haya registros públicos disponibles, aparecerán aquí.'}</p>{(busqueda || regionActiva !== 'Todas') && <button type="button" className="boton boton-secundario" onClick={() => { setBusqueda(''); setRegionActiva('Todas'); setCategoriaActiva('Todas'); setDesplazamiento(0) }}>Limpiar filtros</button>}</div>
                )}
                {!cargando && !error && filtrados.length > 0 && <div className="rejilla-hallazgos">{filtrados.map((hallazgo) => <TarjetaHallazgo key={hallazgo.hallazgo_id} hallazgo={hallazgo} onOpen={abrirFicha} />)}</div>}

                {!cargando && !error && hallazgos.length > 0 && (
                  <div className="paginacion"><span>Mostrando {desplazamiento + 1}–{desplazamiento + hallazgos.length} registros de esta consulta</span><div><button className="boton-pagina" disabled={desplazamiento === 0} onClick={() => setDesplazamiento((valor) => Math.max(0, valor - POR_PAGINA))}>← Anterior</button><button type="button" className="boton-pagina" disabled={desplazamiento + hallazgos.length >= cantidad} onClick={() => setDesplazamiento((valor) => valor + POR_PAGINA)}>Siguiente →</button></div></div>
                )}
              </section>
            </>
          ) : (
            <DetalleHallazgo hallazgo={seleccionado} ficha={ficha} cargando={cargandoFicha} error={errorFicha} onBack={volverListado} onRetry={() => { setSeleccionado({ ...seleccionado }) }} />
          )}
          <footer className="pie-pagina"><span>© BioHub · Sistema Nacional de Registro y Vigilancia de Biodiversidad</span><span>Información pública para la conservación <b>♥</b></span></footer>
        </div>
      </main>
    </div>
  )
}
