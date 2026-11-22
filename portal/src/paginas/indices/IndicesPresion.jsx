// HU-15 · Índices de presión. Responsable: Guarnizo.
// Reemplaza el contenido de este archivo por la pantalla real. Para llamar al backend usa
// pedir() de src/api.js: ya manda el token y maneja 401 y 403.
import Pendiente from '../../componentes/Pendiente.jsx'

export default function IndicesPresion() {
  return (
    <Pendiente
      historia="HU-15"
      titulo="Índices de presión"
      responsable="Guarnizo"
      archivo="portal/src/paginas/indices/IndicesPresion.jsx"
      endpoints={[
        'GET /api/v1/reportes/indices/{AAAA-MM}',
        'POST /api/v1/reportes/indices/{AAAA-MM}',
      ]}
    />
  )
}
