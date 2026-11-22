// HU-08 · Reclasificar hallazgo. Responsable: Guarnizo.
// Reemplaza el contenido de este archivo por la pantalla real. Para llamar al backend usa
// pedir() de src/api.js: ya manda el token y maneja 401 y 403.
import Pendiente from '../../componentes/Pendiente.jsx'

export default function Reclasificar() {
  return (
    <Pendiente
      historia="HU-08"
      titulo="Reclasificar hallazgo"
      responsable="Guarnizo"
      archivo="portal/src/paginas/reclasificar/Reclasificar.jsx"
      endpoints={[
        'GET /api/v1/consulta/hallazgos (para escoger el hallazgo)',
        'GET /api/v1/registro/especies',
        'POST /api/v1/gobernanza/hallazgos/{id}/reclasificaciones',
      ]}
    />
  )
}
