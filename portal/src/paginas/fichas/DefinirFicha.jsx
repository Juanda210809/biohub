// HU-04 · Definir atributos de la ficha. Responsable: Peña.
// El personal científico escoge un tipo de especie, ve los atributos de su ficha vigente, los
// agrega, modifica o quita, y publica una revisión nueva (sin tocar código ni detener el sistema).
// Los hallazgos ya registrados no cambian. La lógica de validación y del cuerpo está en editor.js.
import { useCallback, useEffect, useMemo, useState } from 'react'
import { pedir } from '../../api.js'
import {
  construirCuerpo, erroresDelServidor, filaDesdeAtributo, filaNueva, firma, hayErrores, TIPOS, tiposDeEspecie,
  validarFilas,
} from './editor.js'
import './fichas.css'

const SIN_ERRORES = { porFila: {}, general: [] }

function Campo({ etiqueta, error, ayuda, children }) {
  return (
    <label className={`fic-campo${error ? ' fic-campo-error' : ''}`}>
      <span className="fic-etiqueta">{etiqueta}</span>
      {children}
      {ayuda && !error && <small className="fic-ayuda">{ayuda}</small>}
      {error && <small className="fic-mensaje" role="alert">{error}</small>}
    </label>
  )
}

function ReglasDelTipo({ fila, alCambiar }) {
  const reglas = fila.reglas
  const cambiar = (nombre) => (evento) => alCambiar({ reglas: { ...reglas, [nombre]: evento.target.value } })

  if (fila.tipo === 'NUMERO') {
    return (
      <>
        <Campo etiqueta="Mínimo (opcional)">
          <input type="number" step="any" value={reglas.minimo} onChange={cambiar('minimo')} />
        </Campo>
        <Campo etiqueta="Máximo (opcional)">
          <input type="number" step="any" value={reglas.maximo} onChange={cambiar('maximo')} />
        </Campo>
        <Campo etiqueta="Unidad (opcional)" ayuda="Por ejemplo: °C, mm, msnm">
          <input value={reglas.unidad} onChange={cambiar('unidad')} />
        </Campo>
      </>
    )
  }
  if (fila.tipo === 'TEXTO') {
    return (
      <>
        <Campo etiqueta="Longitud máxima (opcional)" ayuda="Cantidad máxima de caracteres">
          <input type="number" step="1" min="1" value={reglas.longitudMaxima} onChange={cambiar('longitudMaxima')} />
        </Campo>
        <Campo etiqueta="Patrón (opcional)" ayuda="Expresión regular que debe cubrir todo el texto">
          <input value={reglas.patron} onChange={cambiar('patron')} />
        </Campo>
      </>
    )
  }
  if (fila.tipo === 'FECHA') {
    return (
      <>
        <Campo etiqueta="Fecha mínima (opcional)">
          <input type="date" value={reglas.fechaMinima} onChange={cambiar('fechaMinima')} />
        </Campo>
        <Campo etiqueta="Fecha máxima (opcional)">
          <input type="date" value={reglas.fechaMaxima} onChange={cambiar('fechaMaxima')} />
        </Campo>
      </>
    )
  }
  return (
    <div className="fic-ancho">
      <Campo etiqueta="Opciones" ayuda="Una opción por línea. No pueden repetirse.">
        <textarea rows={4} value={reglas.opciones} onChange={cambiar('opciones')} />
      </Campo>
    </div>
  )
}

function FilaAtributo({ fila, posicion, errores, alCambiar, alQuitar }) {
  const hayError = Object.keys(errores).length > 0
  return (
    <li className={`fic-atributo${hayError ? ' fic-atributo-error' : ''}`}>
      <div className="fic-atributo-cabecera">
        <strong>{fila.etiqueta.trim() || `Atributo ${posicion + 1}`}</strong>
        <span className={`fic-marca${fila.existente ? '' : ' fic-marca-nueva'}`}>
          {fila.existente ? 'En la ficha' : 'Nuevo'}
        </span>
        <button type="button" className="boton boton-secundario" onClick={alQuitar}>Quitar</button>
      </div>

      <div className="fic-rejilla">
        <Campo
          etiqueta="Clave"
          error={errores.clave}
          ayuda={fila.existente ? 'No se puede cambiar: es la identidad del atributo' : 'Nombre interno, en camelCase. Ejemplo: temperaturaAgua'}
        >
          <input value={fila.clave} disabled={fila.existente} onChange={(evento) => alCambiar({ clave: evento.target.value })} />
        </Campo>
        <Campo etiqueta="Etiqueta" error={errores.etiqueta} ayuda="Lo que ve el investigador en el formulario">
          <input value={fila.etiqueta} onChange={(evento) => alCambiar({ etiqueta: evento.target.value })} />
        </Campo>
        <Campo
          etiqueta="Tipo de dato"
          error={errores.tipo}
          ayuda={fila.existente ? 'No se puede cambiar el tipo de un atributo existente; crea otro con otra clave' : undefined}
        >
          <select value={fila.tipo} disabled={fila.existente} onChange={(evento) => alCambiar({ tipo: evento.target.value })}>
            {TIPOS.map((tipo) => <option key={tipo.valor} value={tipo.valor}>{tipo.nombre}</option>)}
          </select>
        </Campo>
        <div className="fic-marcas">
          <label className="fic-casilla">
            <input type="checkbox" checked={fila.obligatorio} onChange={(evento) => alCambiar({ obligatorio: evento.target.checked })} />
            <span>Obligatorio</span>
          </label>
          <label className="fic-casilla">
            <input type="checkbox" checked={fila.publicable} onChange={(evento) => alCambiar({ publicable: evento.target.checked })} />
            <span>Visible al público</span>
          </label>
        </div>
        <ReglasDelTipo fila={fila} alCambiar={alCambiar} />
      </div>

      {errores.reglas && <p className="fic-mensaje" role="alert">{errores.reglas}</p>}
      {errores.otro && <p className="fic-mensaje" role="alert">{errores.otro}</p>}
    </li>
  )
}

export default function DefinirFicha() {
  const [especies, setEspecies] = useState([])
  const [estadoCatalogo, setEstadoCatalogo] = useState('cargando') // cargando | listo | error
  const [errorCatalogo, setErrorCatalogo] = useState('')

  const [tipoId, setTipoId] = useState('')
  const [ficha, setFicha] = useState(null)
  const [estadoFicha, setEstadoFicha] = useState('vacia') // vacia | cargando | lista | error
  const [errorFicha, setErrorFicha] = useState('')

  const [filas, setFilas] = useState([])
  const [firmaOriginal, setFirmaOriginal] = useState('[]')
  const [errores, setErrores] = useState(SIN_ERRORES)
  const [aviso, setAviso] = useState([])
  const [conflicto, setConflicto] = useState(false)
  const [publicada, setPublicada] = useState(null)
  const [enviando, setEnviando] = useState(false)

  const tipos = useMemo(() => tiposDeEspecie(especies), [especies])
  const hayCambios = estadoFicha === 'lista' && firma(filas) !== firmaOriginal

  const cargarCatalogo = useCallback(() => {
    let vigente = true
    setEstadoCatalogo('cargando')
    pedir('/api/v1/registro/especies')
      .then((lista) => {
        if (!vigente) return
        setEspecies(lista)
        setEstadoCatalogo('listo')
      })
      .catch((fallo) => {
        if (!vigente) return
        setErrorCatalogo(fallo.message)
        setEstadoCatalogo('error')
      })
    return () => {
      vigente = false
    }
  }, [])

  useEffect(() => cargarCatalogo(), [cargarCatalogo])

  const cargarFicha = useCallback((id) => {
    setEstadoFicha('cargando')
    setErrorFicha('')
    return pedir(`/api/v1/registro/tipos-especie/${encodeURIComponent(id)}/ficha`)
      .then((datos) => {
        const nuevas = datos.atributos.map(filaDesdeAtributo)
        setFicha(datos)
        setFilas(nuevas)
        setFirmaOriginal(firma(nuevas))
        setEstadoFicha('lista')
      })
      .catch((fallo) => {
        setFicha(null)
        setFilas([])
        setErrorFicha(fallo.message)
        setEstadoFicha('error')
      })
  }, [])

  function limpiarMensajes() {
    setErrores(SIN_ERRORES)
    setAviso([])
    setConflicto(false)
    setPublicada(null)
  }

  function escogerTipo(id) {
    if (hayCambios && !window.confirm('Tienes cambios sin publicar. ¿Descartarlos?')) return
    limpiarMensajes()
    setTipoId(id)
    if (!id) {
      setFicha(null)
      setFilas([])
      setEstadoFicha('vacia')
      return
    }
    cargarFicha(id)
  }

  function recargar() {
    limpiarMensajes()
    cargarFicha(tipoId)
  }

  function descartar() {
    limpiarMensajes()
    setFilas(ficha.atributos.map(filaDesdeAtributo))
  }

  function cambiarFila(posicion, cambios) {
    setFilas((actuales) => actuales.map((fila, i) => (i === posicion ? { ...fila, ...cambios } : fila)))
    setErrores((actuales) => (actuales.porFila[posicion] ? { ...actuales, porFila: { ...actuales.porFila, [posicion]: undefined } } : actuales))
    setPublicada(null)
  }

  function quitarFila(posicion) {
    setFilas((actuales) => actuales.filter((_, i) => i !== posicion))
    setErrores(SIN_ERRORES)
    setPublicada(null)
  }

  function agregarFila() {
    setFilas((actuales) => [...actuales, filaNueva()])
    setPublicada(null)
  }

  async function publicar() {
    setAviso([])
    setConflicto(false)
    setPublicada(null)
    const encontrados = validarFilas(filas)
    setErrores(encontrados)
    if (hayErrores(encontrados)) {
      setAviso(['Revisa los atributos marcados antes de publicar.'])
      return
    }

    setEnviando(true)
    try {
      const nueva = await pedir(`/api/v1/registro/tipos-especie/${encodeURIComponent(tipoId)}/ficha`, {
        method: 'PUT',
        body: construirCuerpo(ficha.revision, filas),
      })
      const filasNuevas = nueva.atributos.map(filaDesdeAtributo)
      setFicha(nueva)
      setFilas(filasNuevas)
      setFirmaOriginal(firma(filasNuevas))
      setPublicada(nueva.revision)
    } catch (fallo) {
      if (fallo.status === 409) {
        setConflicto(true)
        setAviso(['La ficha cambió mientras la editabas (alguien publicó otra revisión). Recárgala y repite tu cambio.'])
      } else if (fallo.status === 422) {
        const { porFila, general } = erroresDelServidor(fallo)
        setErrores({ porFila, general })
        setAviso(['El servidor no aceptó la ficha. Revisa los atributos marcados.'])
      } else if (fallo.status === 403) {
        setAviso(['Tu cuenta no tiene permiso para definir fichas.'])
      } else if (fallo.status === 404) {
        setAviso([fallo.message])
      } else if (fallo.status === 401) {
        // api.js ya cerró la sesión y el portal vuelve al inicio de sesión.
        setAviso(['Tu sesión terminó. Inicia sesión de nuevo.'])
      } else {
        setAviso([fallo.message || 'No se pudo publicar la ficha. Intenta de nuevo.'])
      }
    } finally {
      setEnviando(false)
    }
  }

  if (estadoCatalogo === 'cargando') {
    return (
      <section className="fic">
        <p className="cargando-linea" role="status">Cargando los tipos de especie…</p>
      </section>
    )
  }

  if (estadoCatalogo === 'error') {
    return (
      <section className="fic">
        <div className="aviso-error" role="alert">
          <span>No pudimos cargar los tipos de especie: {errorCatalogo}</span>
          <button type="button" className="boton boton-secundario" onClick={cargarCatalogo}>Intentar de nuevo</button>
        </div>
      </section>
    )
  }

  return (
    <section className="fic">
      <span className="etiqueta-superior">HU-04 · FICHAS TAXONÓMICAS</span>
      <h2>Definir atributos de la ficha</h2>
      <p className="texto-suave">
        Escoge un tipo de especie, agrega, modifica o quita atributos y publica una revisión nueva.
        Los hallazgos ya registrados no cambian.
      </p>

      <div className="fic-selector">
        <Campo etiqueta="Tipo de especie">
          <select value={tipoId} onChange={(evento) => escogerTipo(evento.target.value)}>
            <option value="">Escoge un tipo de especie</option>
            {tipos.map((tipo) => <option key={tipo.id} value={tipo.id}>{tipo.nombre}</option>)}
          </select>
        </Campo>
        {ficha && <span className="fic-revision">Revisión vigente: {ficha.revision}</span>}
      </div>

      {tipos.length === 0 && <p className="texto-suave">No hay tipos de especie para editar.</p>}
      {estadoFicha === 'vacia' && tipos.length > 0 && (
        <p className="texto-suave">Escoge un tipo de especie para ver su ficha.</p>
      )}
      {estadoFicha === 'cargando' && <p className="cargando-linea" role="status">Cargando la ficha…</p>}
      {estadoFicha === 'error' && (
        <div className="aviso-error" role="alert">
          <span>No pudimos cargar la ficha: {errorFicha}</span>
          <button type="button" className="boton boton-secundario" onClick={recargar}>Intentar de nuevo</button>
        </div>
      )}

      {publicada !== null && (
        <div className="fic-exito" role="status">
          Ficha publicada: ahora es la revisión {publicada}. Los hallazgos ya registrados no cambian.
        </div>
      )}

      {aviso.length > 0 && (
        <div className="aviso-error" role="alert">
          <span>{aviso.join(' ')}</span>
          {conflicto && (
            <button type="button" className="boton boton-secundario" onClick={recargar}>Recargar la ficha</button>
          )}
        </div>
      )}
      {errores.general.length > 0 && (
        <div className="aviso-error" role="alert">
          <span>{errores.general.join(' ')}</span>
        </div>
      )}

      {estadoFicha === 'lista' && (
        <>
          <ul className="fic-lista">
            {filas.map((fila, posicion) => (
              <FilaAtributo
                key={fila.id}
                fila={fila}
                posicion={posicion}
                errores={errores.porFila[posicion] ?? {}}
                alCambiar={(cambios) => cambiarFila(posicion, cambios)}
                alQuitar={() => quitarFila(posicion)}
              />
            ))}
          </ul>
          {filas.length === 0 && <p className="texto-suave">La ficha no tiene atributos. Agrega al menos uno.</p>}

          <div className="fic-acciones">
            <button type="button" className="boton boton-secundario" onClick={agregarFila}>+ Agregar atributo</button>
            <span className="fic-espacio" />
            <button type="button" className="boton boton-secundario" onClick={descartar} disabled={!hayCambios || enviando}>
              Descartar cambios
            </button>
            <button type="button" className="boton boton-primario" onClick={publicar} disabled={!hayCambios || enviando}>
              {enviando ? 'Publicando…' : `Publicar revisión ${ficha.revision + 1}`}
            </button>
          </div>
          {!hayCambios && <p className="texto-suave fic-nota">No hay cambios sin publicar.</p>}
        </>
      )}
    </section>
  )
}
