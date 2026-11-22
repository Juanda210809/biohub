// HU-03 · Registrar hallazgo. Responsable: Peña.
// El investigador escoge la especie y la expedición, indica fecha y ubicación, y llena los
// atributos de la ficha de esa especie (que llegan del servidor: agregar un atributo no cambia
// este código). La lógica de validación y del cuerpo está en formulario.js.
import { useCallback, useEffect, useMemo, useState } from 'react'
import { pedir } from '../../api.js'
import {
  construirCuerpo, erroresDelServidor, formularioInicial, TIPOS_SOPORTADOS, validarFormulario,
} from './formulario.js'
import './registro.css'

function Campo({ etiqueta, error, obligatorio = false, ayuda, children }) {
  return (
    <label className={`reg-campo${error ? ' reg-campo-error' : ''}`}>
      <span className="reg-etiqueta">
        {etiqueta}
        {obligatorio && <b aria-hidden="true"> *</b>}
      </span>
      {children}
      {ayuda && !error && <small className="reg-ayuda">{ayuda}</small>}
      {error && <small className="reg-mensaje" role="alert">{error}</small>}
    </label>
  )
}

function CampoAtributo({ atributo, valor, error, alCambiar }) {
  const reglas = atributo.reglas || {}
  // Si la etiqueta ya trae la unidad (por ejemplo "Altitud (msnm)"), no se repite.
  const llevaUnidad = reglas.unidad && !atributo.etiqueta.includes(`(${reglas.unidad})`)
  const etiqueta = llevaUnidad ? `${atributo.etiqueta} (${reglas.unidad})` : atributo.etiqueta

  if (!TIPOS_SOPORTADOS.includes(atributo.tipo)) {
    return (
      <div className="reg-campo reg-campo-apagado">
        <span className="reg-etiqueta">{atributo.etiqueta}</span>
        <small className="reg-ayuda">Este tipo de dato ({atributo.tipo}) aún no está disponible en el formulario.</small>
      </div>
    )
  }

  let entrada
  if (atributo.tipo === 'SELECCION') {
    entrada = (
      <select value={valor ?? ''} onChange={(evento) => alCambiar(evento.target.value)}>
        <option value="">Escoge una opción</option>
        {(reglas.opciones || []).map((opcion) => (
          <option key={String(opcion)} value={String(opcion)}>{String(opcion)}</option>
        ))}
      </select>
    )
  } else if (atributo.tipo === 'NUMERO') {
    entrada = (
      <input
        type="number"
        step="any"
        min={reglas.minimo ?? undefined}
        max={reglas.maximo ?? undefined}
        value={valor ?? ''}
        onChange={(evento) => alCambiar(evento.target.value)}
      />
    )
  } else if (atributo.tipo === 'FECHA') {
    entrada = (
      <input
        type="date"
        min={reglas.fechaMinima || undefined}
        max={reglas.fechaMaxima || undefined}
        value={valor ?? ''}
        onChange={(evento) => alCambiar(evento.target.value)}
      />
    )
  } else {
    entrada = (
      <input
        type="text"
        maxLength={reglas.longitudMaxima ?? undefined}
        value={valor ?? ''}
        onChange={(evento) => alCambiar(evento.target.value)}
      />
    )
  }

  const ayuda = [
    reglas.minimo != null && reglas.maximo != null ? `Entre ${reglas.minimo} y ${reglas.maximo}` : null,
    atributo.publicable ? null : 'Solo lo ve el personal interno',
  ].filter(Boolean).join(' · ')

  return (
    <Campo etiqueta={etiqueta} obligatorio={atributo.obligatorio} error={error} ayuda={ayuda}>
      {entrada}
    </Campo>
  )
}

export default function RegistrarHallazgo() {
  const [especies, setEspecies] = useState([])
  const [expediciones, setExpediciones] = useState([])
  const [estadoCatalogo, setEstadoCatalogo] = useState('cargando') // cargando | listo | error
  const [errorCatalogo, setErrorCatalogo] = useState('')

  const [formulario, setFormulario] = useState(() => formularioInicial())
  const [ficha, setFicha] = useState(null)
  const [estadoFicha, setEstadoFicha] = useState('vacia') // vacia | cargando | lista | error
  const [errorFicha, setErrorFicha] = useState('')

  const [errores, setErrores] = useState({})
  const [mensajeGeneral, setMensajeGeneral] = useState([])
  const [enviando, setEnviando] = useState(false)
  const [registrado, setRegistrado] = useState(null)

  const cargarCatalogo = useCallback(() => {
    let vigente = true
    setEstadoCatalogo('cargando')
    Promise.all([pedir('/api/v1/registro/especies'), pedir('/api/v1/registro/expediciones')])
      .then(([listaEspecies, listaExpediciones]) => {
        if (!vigente) return
        setEspecies(listaEspecies)
        setExpediciones(listaExpediciones)
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

  const tipoEspecieId = useMemo(
    () => especies.find((especie) => especie.id === formulario.especieId)?.tipoEspecieId ?? '',
    [especies, formulario.especieId],
  )

  // Al escoger una especie se pide la ficha de su tipo y de ahí salen los campos del formulario.
  useEffect(() => {
    if (!tipoEspecieId) {
      setFicha(null)
      setEstadoFicha('vacia')
      return undefined
    }
    let vigente = true
    setEstadoFicha('cargando')
    setErrorFicha('')
    pedir(`/api/v1/registro/tipos-especie/${encodeURIComponent(tipoEspecieId)}/ficha`)
      .then((datos) => {
        if (!vigente) return
        setFicha(datos)
        setEstadoFicha('lista')
      })
      .catch((fallo) => {
        if (!vigente) return
        setFicha(null)
        setErrorFicha(fallo.message)
        setEstadoFicha('error')
      })
    return () => {
      vigente = false
    }
  }, [tipoEspecieId])

  function cambiar(campo, valor) {
    setFormulario((actual) => ({ ...actual, [campo]: valor }))
    setErrores((actuales) => (actuales[campo] ? { ...actuales, [campo]: undefined } : actuales))
  }

  function cambiarEspecie(valor) {
    // Los atributos pertenecen a la ficha de la especie anterior: se limpian al cambiarla.
    setFormulario((actual) => ({ ...actual, especieId: valor, atributos: {} }))
    setErrores({})
    setMensajeGeneral([])
  }

  function cambiarAtributo(clave, valor) {
    setFormulario((actual) => ({ ...actual, atributos: { ...actual.atributos, [clave]: valor } }))
    const llave = `atributos.${clave}`
    setErrores((actuales) => (actuales[llave] ? { ...actuales, [llave]: undefined } : actuales))
  }

  async function enviar(evento) {
    evento.preventDefault()
    setMensajeGeneral([])
    if (estadoFicha !== 'lista') {
      setMensajeGeneral(['Escoge una especie y espera a que cargue su ficha.'])
      return
    }
    const encontrados = validarFormulario(formulario, ficha)
    setErrores(encontrados)
    if (Object.keys(encontrados).length > 0) {
      setMensajeGeneral(['Revisa los campos marcados.'])
      return
    }

    setEnviando(true)
    try {
      const respuesta = await pedir('/api/v1/registro/hallazgos', {
        method: 'POST',
        body: construirCuerpo(formulario, ficha),
      })
      setRegistrado(respuesta)
    } catch (fallo) {
      if (fallo.status === 422) {
        const { campos, general } = erroresDelServidor(fallo, ficha)
        setErrores(campos)
        setMensajeGeneral(general.length > 0 ? general : ['Revisa los campos marcados.'])
      } else if (fallo.status === 404) {
        setMensajeGeneral([fallo.message])
      } else if (fallo.status === 403) {
        setMensajeGeneral(['Tu cuenta no tiene permiso para registrar hallazgos.'])
      } else if (fallo.status === 401) {
        // api.js ya cerró la sesión y el portal vuelve al inicio de sesión.
        setMensajeGeneral(['Tu sesión terminó. Inicia sesión de nuevo.'])
      } else {
        setMensajeGeneral([fallo.message || 'No se pudo guardar el hallazgo. Intenta de nuevo.'])
      }
    } finally {
      setEnviando(false)
    }
  }

  function registrarOtro() {
    // Se conservan la expedición y la fecha: normalmente se registran varios en la misma salida.
    setFormulario((actual) => ({
      ...formularioInicial(),
      expedicionId: actual.expedicionId,
      fechaHallazgo: actual.fechaHallazgo,
    }))
    setErrores({})
    setMensajeGeneral([])
    setRegistrado(null)
  }

  if (registrado) {
    return (
      <section className="reg">
        <div className="reg-exito" role="status">
          <span className="reg-icono" aria-hidden="true">✓</span>
          <h2>Hallazgo registrado</h2>
          <p className="texto-suave">
            Quedó guardado como versión {registrado.version} de su historial.
            Código: <code>{registrado.hallazgoId}</code>
          </p>
          <button type="button" className="boton boton-primario" onClick={registrarOtro}>
            Registrar otro hallazgo
          </button>
        </div>
      </section>
    )
  }

  if (estadoCatalogo === 'cargando') {
    return (
      <section className="reg">
        <p className="cargando-linea" role="status">Cargando especies y expediciones…</p>
      </section>
    )
  }

  if (estadoCatalogo === 'error') {
    return (
      <section className="reg">
        <div className="aviso-error" role="alert">
          <span>No pudimos cargar las listas del formulario: {errorCatalogo}</span>
          <button type="button" className="boton boton-secundario" onClick={cargarCatalogo}>
            Intentar de nuevo
          </button>
        </div>
      </section>
    )
  }

  return (
    <section className="reg">
      <span className="etiqueta-superior">HU-03 · REGISTRO EN CAMPO</span>
      <h2>Registrar hallazgo</h2>
      <p className="texto-suave">
        Los campos con * son obligatorios. La ubicación exacta solo la ve el personal de alto
        rango; el público solo ve la región y el departamento.
      </p>

      {mensajeGeneral.length > 0 && (
        <div className="aviso-error" role="alert">
          <span>{mensajeGeneral.join(' ')}</span>
        </div>
      )}

      <form className="reg-formulario" onSubmit={enviar} noValidate>
        <fieldset className="reg-grupo">
          <legend>¿Qué encontraste?</legend>
          <Campo etiqueta="Especie" obligatorio error={errores.especieId}>
            <select value={formulario.especieId} onChange={(evento) => cambiarEspecie(evento.target.value)}>
              <option value="">Escoge una especie</option>
              {especies.map((especie) => (
                <option key={especie.id} value={especie.id}>
                  {especie.nombreCientifico}{especie.nombreComun ? ` · ${especie.nombreComun}` : ''}
                </option>
              ))}
            </select>
          </Campo>
          <Campo etiqueta="Expedición" obligatorio error={errores.expedicionId}>
            <select value={formulario.expedicionId} onChange={(evento) => cambiar('expedicionId', evento.target.value)}>
              <option value="">Escoge una expedición</option>
              {expediciones.map((expedicion) => (
                <option key={expedicion.id} value={expedicion.id}>{expedicion.nombre}</option>
              ))}
            </select>
          </Campo>
          <Campo etiqueta="Fecha del hallazgo" obligatorio error={errores.fechaHallazgo}>
            <input
              type="date"
              value={formulario.fechaHallazgo}
              onChange={(evento) => cambiar('fechaHallazgo', evento.target.value)}
            />
          </Campo>
        </fieldset>

        <fieldset className="reg-grupo">
          <legend>¿Dónde?</legend>
          <Campo etiqueta="Latitud" obligatorio error={errores.latitud} ayuda="Entre -90 y 90">
            <input
              type="number"
              step="any"
              value={formulario.latitud}
              onChange={(evento) => cambiar('latitud', evento.target.value)}
            />
          </Campo>
          <Campo etiqueta="Longitud" obligatorio error={errores.longitud} ayuda="Entre -180 y 180">
            <input
              type="number"
              step="any"
              value={formulario.longitud}
              onChange={(evento) => cambiar('longitud', evento.target.value)}
            />
          </Campo>
          <Campo etiqueta="Precisión (metros)" error={errores.precisionM}>
            <input
              type="number"
              step="any"
              min="0"
              value={formulario.precisionM}
              onChange={(evento) => cambiar('precisionM', evento.target.value)}
            />
          </Campo>
          <Campo etiqueta="Región" error={errores.region} ayuda="Indica al menos la región o el departamento">
            <input value={formulario.region} onChange={(evento) => cambiar('region', evento.target.value)} />
          </Campo>
          <Campo etiqueta="Departamento" error={errores.departamento}>
            <input value={formulario.departamento} onChange={(evento) => cambiar('departamento', evento.target.value)} />
          </Campo>
          <Campo etiqueta="Ecosistema" error={errores.ecosistema}>
            <input value={formulario.ecosistema} onChange={(evento) => cambiar('ecosistema', evento.target.value)} />
          </Campo>
        </fieldset>

        <fieldset className="reg-grupo">
          <legend>{ficha ? `Ficha de la especie · ${ficha.nombre}` : 'Ficha de la especie'}</legend>
          {estadoFicha === 'vacia' && (
            <p className="texto-suave reg-ancho">Escoge una especie para ver los datos que pide su ficha.</p>
          )}
          {estadoFicha === 'cargando' && <p className="cargando-linea reg-ancho" role="status">Cargando la ficha…</p>}
          {estadoFicha === 'error' && (
            <div className="aviso-error reg-ancho" role="alert">
              <span>No pudimos cargar la ficha: {errorFicha}</span>
            </div>
          )}
          {estadoFicha === 'lista' && ficha.atributos.length === 0 && (
            <p className="texto-suave reg-ancho">Esta ficha no pide datos adicionales.</p>
          )}
          {estadoFicha === 'lista' && ficha.atributos.map((atributo) => (
            <CampoAtributo
              key={atributo.clave}
              atributo={atributo}
              valor={formulario.atributos[atributo.clave]}
              error={errores[`atributos.${atributo.clave}`]}
              alCambiar={(valor) => cambiarAtributo(atributo.clave, valor)}
            />
          ))}
        </fieldset>

        <div className="reg-acciones">
          <button type="submit" className="boton boton-primario" disabled={enviando}>
            {enviando ? 'Guardando…' : 'Registrar hallazgo'}
          </button>
        </div>
      </form>
    </section>
  )
}
