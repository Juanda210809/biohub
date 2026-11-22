// HU-12 · Historial y versiones. Responsable: Guarnizo.
// Reemplaza el contenido de este archivo por la pantalla real. Para llamar al backend usa
// pedir() de src/api.js: ya manda el token y maneja 401 y 403.
import Pendiente from '../../componentes/Pendiente.jsx'

export default function Historial() {
  return (
    <Pendiente
      historia="HU-12"
      titulo="Historial y versiones"
      responsable="Guarnizo"
      archivo="portal/src/paginas/historial/Historial.jsx"
      endpoints={[
        'GET /api/v1/consulta/hallazgos (para escoger el hallazgo)',
        'GET /api/v1/gobernanza/hallazgos/{id}/historial',
      ]}
    />
  )
}
