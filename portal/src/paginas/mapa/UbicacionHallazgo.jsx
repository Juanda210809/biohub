// HU-07 · Ubicación en el mapa. Responsable: Luna.
// Reemplaza el contenido de este archivo por la pantalla real. Para llamar al backend usa
// pedir() de src/api.js: ya manda el token y maneja 401 y 403.
import Pendiente from '../../componentes/Pendiente.jsx'

export default function UbicacionHallazgo() {
  return (
    <Pendiente
      historia="HU-07"
      titulo="Ubicación en el mapa"
      responsable="Luna"
      archivo="portal/src/paginas/mapa/UbicacionHallazgo.jsx"
      endpoints={[
        'GET /api/v1/consulta/hallazgos (para escoger el hallazgo)',
        'GET /api/v1/registro/hallazgos/{id}/ubicacion',
      ]}
    />
  )
}
