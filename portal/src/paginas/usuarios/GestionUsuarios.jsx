// HU-02 · HU-18 · Usuarios y roles. Responsable: Matheus.
// Reemplaza el contenido de este archivo por la pantalla real. Para llamar al backend usa
// pedir() de src/api.js: ya manda el token y maneja 401 y 403.
import Pendiente from '../../componentes/Pendiente.jsx'

export default function GestionUsuarios() {
  return (
    <Pendiente
      historia="HU-02 · HU-18"
      titulo="Usuarios y roles"
      responsable="Matheus"
      archivo="portal/src/paginas/usuarios/GestionUsuarios.jsx"
      endpoints={[
        'GET /api/v1/identidad/usuarios',
        'POST /api/v1/identidad/usuarios',
        'PATCH /api/v1/identidad/usuarios/{id}',
        'POST /api/v1/identidad/usuarios/{id}/desactivar · /activar',
        'PUT /api/v1/identidad/usuarios/{id}/rol',
      ]}
    />
  )
}
