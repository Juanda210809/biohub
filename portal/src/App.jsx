// Página de inicio provisional: comprueba que los 5 servicios responden a través de Kong.
// Luna la reemplaza por las pantallas reales (login, registro, ficha pública, mapa...).
import { useEffect, useState } from 'react'
import { API_URL, pedir } from './api.js'

const SERVICIOS = [
  { id: 'registro', nombre: 'Registro y Gestión de Campo' },
  { id: 'gobernanza', nombre: 'Gobernanza Científica' },
  { id: 'consulta', nombre: 'Consulta Pública' },
  { id: 'identidad', nombre: 'Identidad y Autorización' },
  { id: 'reportes', nombre: 'Reportes y Analítica' },
]

function TarjetaServicio({ servicio }) {
  const [estado, setEstado] = useState({ cargando: true })

  useEffect(() => {
    pedir(`/api/v1/${servicio.id}/salud`)
      .then((datos) => setEstado({ datos }))
      .catch((error) => setEstado({ error: error.message }))
  }, [servicio.id])

  const ok = estado.datos?.estado === 'ok' && estado.datos?.bd === 'ok'
  const clase = estado.cargando ? 'tarjeta' : ok ? 'tarjeta verde' : 'tarjeta roja'

  return (
    <div className={clase}>
      <h3>{servicio.nombre}</h3>
      {estado.cargando && <p>Consultando…</p>}
      {estado.error && <p>Sin respuesta ({estado.error})</p>}
      {estado.datos && (
        <ul>
          <li>Servicio: {estado.datos.estado}</li>
          <li>Base de datos: {estado.datos.bd}</li>
          {estado.datos.cache && <li>Caché Redis: {estado.datos.cache}</li>}
          {estado.datos.filas_hallazgo_publico !== undefined && (
            <li>Filas replicadas: {String(estado.datos.filas_hallazgo_publico)}</li>
          )}
        </ul>
      )}
      <a href={`${API_URL}/api/v1/${servicio.id}/docs`} target="_blank" rel="noreferrer">
        Ver documentación de rutas
      </a>
    </div>
  )
}

export default function App() {
  return (
    <main>
      <h1>BioHub · estado del sistema</h1>
      <p>Si las 5 tarjetas están en verde, todo el sistema está conectado.</p>
      <section className="grilla">
        {SERVICIOS.map((s) => (
          <TarjetaServicio key={s.id} servicio={s} />
        ))}
      </section>
    </main>
  )
}
