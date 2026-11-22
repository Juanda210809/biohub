// HU-03 · Registrar hallazgo. Responsable: Peña.
// Reemplaza el contenido de este archivo por la pantalla real. Para llamar al backend usa
// pedir() de src/api.js: ya manda el token y maneja 401 y 403.
import Pendiente from '../../componentes/Pendiente.jsx'

export default function RegistrarHallazgo() {
  return (
    <Pendiente
      historia="HU-03"
      titulo="Registrar hallazgo"
      responsable="Peña"
      archivo="portal/src/paginas/registro/RegistrarHallazgo.jsx"
      endpoints={[
        'GET /api/v1/registro/especies',
        'GET /api/v1/registro/expediciones',
        'GET /api/v1/registro/tipos-especie/{tipoEspecieId}/ficha',
        'POST /api/v1/registro/hallazgos',
      ]}
    />
  )
}
