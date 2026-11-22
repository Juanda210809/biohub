// HU-04 · Definir atributos de la ficha. Responsable: Peña.
// Reemplaza el contenido de este archivo por la pantalla real. Para llamar al backend usa
// pedir() de src/api.js: ya manda el token y maneja 401 y 403.
import Pendiente from '../../componentes/Pendiente.jsx'

export default function DefinirFicha() {
  return (
    <Pendiente
      historia="HU-04"
      titulo="Definir atributos de la ficha"
      responsable="Peña"
      archivo="portal/src/paginas/fichas/DefinirFicha.jsx"
      endpoints={[
        'GET /api/v1/registro/especies (tipos de especie)',
        'GET /api/v1/registro/tipos-especie/{id}/ficha',
        'PUT /api/v1/registro/tipos-especie/{id}/ficha',
      ]}
    />
  )
}
