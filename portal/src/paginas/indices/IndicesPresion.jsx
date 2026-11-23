// HU-15 · Índices de presión por ecosistema. Responsable: Guarnizo.
// El alto rango escoge un mes y ve cuánta actividad hubo en cada ecosistema comparada con
// el promedio de los 3 meses anteriores. Si el mes no se ha calculado, puede generarlo.
import { useCallback, useEffect, useId, useState } from 'react'
import { pedir } from '../../api.js'
import {
  NIVELES, anchoBarra, fechaConHora, indiceLegible, mensajeError, mesActual, mesAnterior, nombreMes,
  resumenIndices,
} from '../reclasificar/utilidades.js'
import '../reclasificar/pantallas.css'

function Insignia({ nivel }) {
  const info = NIVELES[nivel] || { texto: nivel }
  return <span className={`gob-insignia ${String(nivel).toLowerCase()}`} title={info.descripcion}>{info.texto}</span>
}

export default function IndicesPresion() {
  const id = useId()
  const [periodo, setPeriodo] = useState(mesAnterior())
  const [datos, setDatos] = useState(null)
  const [cargando, setCargando] = useState(false)
  const [generando, setGenerando] = useState(false)
  const [error, setError] = useState(null)

  const consultar = useCallback(async (mes, signal) => {
    setCargando(true)
    setError(null)
    setDatos(null)
    try {
      setDatos(await pedir(`/api/v1/reportes/indices/${encodeURIComponent(mes)}`, { signal }))
    } catch (e) {
      if (e.name !== 'AbortError') setError(e)
    } finally {
      if (!signal?.aborted) setCargando(false)
    }
  }, [])

  useEffect(() => {
    if (!periodo) return undefined
    const control = new AbortController()
    consultar(periodo, control.signal)
    return () => control.abort()
  }, [periodo, consultar])

  async function generar() {
    setGenerando(true)
    setError(null)
    try {
      setDatos(await pedir(`/api/v1/reportes/indices/${encodeURIComponent(periodo)}`, { method: 'POST' }))
    } catch (e) {
      setError(e)
    } finally {
      setGenerando(false)
    }
  }

  const faltaGenerar = error?.codigo === 'indices_no_generados'
  const resumen = resumenIndices(datos?.ecosistemas)

  return (
    <div className="gob-pagina">
      <header className="gob-encabezado seccion-titulo">
        <div>
          <span className="etiqueta-superior">REPORTES · HU-15</span>
          <h1>Índices de presión por ecosistema</h1>
          <p>
            Hallazgos del mes comparados con el promedio de los 3 meses anteriores. Un índice de 1 es lo habitual;
            por encima de 1,25 la presión es alta y por debajo de 0,75 es baja.
          </p>
        </div>
        <label className="gob-campo">
          Mes
          <input type="month" required value={periodo} max={mesActual()} onChange={(e) => setPeriodo(e.target.value)} />
        </label>
      </header>

      {cargando && <p className="cargando-linea">Cargando índices de {nombreMes(periodo)}…</p>}

      {faltaGenerar && (
        <div className="estado-vacio">
          <span className="estado-icono" aria-hidden="true">📊</span>
          <h3>{nombreMes(periodo)} todavía no tiene índices</h3>
          <p>
            Se calculan solos al empezar cada mes. Si los necesitas ya, puedes generarlos ahora;
            quedará registrado que los pediste tú.
          </p>
          <button type="button" className="boton boton-primario" onClick={generar} disabled={generando}>
            {generando ? 'Generando…' : 'Generar índices'}
          </button>
        </div>
      )}

      {error && !faltaGenerar && (
        <div className="aviso-error" role="alert">
          <span>{mensajeError(error)}</span>
          <button type="button" className="boton boton-secundario" onClick={() => consultar(periodo)}>Reintentar</button>
        </div>
      )}

      {datos && (
        <>
          <div className="gob-resumen">
            <div className="dato-detalle"><span>Mes</span><strong>{nombreMes(datos.periodo)}</strong></div>
            <div className="dato-detalle"><span>Ecosistemas</span><strong>{resumen.ecosistemas}</strong></div>
            <div className="dato-detalle"><span>Hallazgos del mes</span><strong>{resumen.hallazgos.toLocaleString('es-CO')}</strong></div>
            <div className="dato-detalle"><span>Con presión alta</span><strong>{resumen.alta}</strong></div>
          </div>

          <section className="gob-panel">
            <div className="seccion-titulo">
              <div>
                <h2 id={`${id}-detalle`}>Detalle por ecosistema</h2>
                <p>
                  Generado {datos.origen === 'AUTOMATICO' ? 'automáticamente' : 'a solicitud'} el {fechaConHora(datos.generadoEn)}
                </p>
              </div>
              <button type="button" className="boton boton-secundario" onClick={generar} disabled={generando}>
                {generando ? 'Recalculando…' : 'Recalcular'}
              </button>
            </div>

            {datos.ecosistemas?.length ? (
              // Con poco espacio la tabla se vuelve una tarjeta por ecosistema (ver pantallas.css).
              <div className="gob-tabla-envoltura gob-apilable" tabIndex={0} role="region" aria-labelledby={`${id}-caption`}>
                <table className="gob-tabla">
                  <caption id={`${id}-caption`} className="visually-hidden">
                    Índices de presión por ecosistema, {nombreMes(datos.periodo)}
                  </caption>
                  <thead>
                    <tr>
                      <th scope="col">Ecosistema</th>
                      <th scope="col" className="numero">Hallazgos</th>
                      <th scope="col" className="numero">Especies</th>
                      <th scope="col" className="numero">Promedio previo</th>
                      <th scope="col" className="numero">Índice</th>
                      <th scope="col">Comparación</th>
                      <th scope="col">Nivel</th>
                    </tr>
                  </thead>
                  <tbody>
                    {datos.ecosistemas.map((e) => (
                      <tr key={e.ecosistema}>
                        <th scope="row">{e.ecosistema}</th>
                        <td className="numero" data-etiqueta="Hallazgos">{e.hallazgos}</td>
                        <td className="numero" data-etiqueta="Especies">{e.especiesDistintas}</td>
                        <td className="numero" data-etiqueta="Promedio previo">{indiceLegible(e.promedioPrevio)}</td>
                        <td className="numero" data-etiqueta="Índice"><strong>{indiceLegible(e.indice)}</strong></td>
                        <td className="celda-barra" data-etiqueta="Comparación">
                          <div className="gob-barra" aria-hidden="true">
                            <span className={String(e.nivel).toLowerCase()} style={{ width: `${anchoBarra(e.indice, resumen.maximo)}%` }} />
                          </div>
                        </td>
                        <td data-etiqueta="Nivel"><Insignia nivel={e.nivel} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="texto-suave">No hubo hallazgos en ningún ecosistema durante {nombreMes(datos.periodo)}.</p>
            )}

            <ul className="gob-leyenda">
              {Object.entries(NIVELES).map(([clave, info]) => (
                <li key={clave}><Insignia nivel={clave} /> {info.descripcion}</li>
              ))}
            </ul>
          </section>
        </>
      )}
    </div>
  )
}
