// Espacio reservado para una pantalla que todavía no está hecha.
// Quien la haga reemplaza el archivo de su página; no hace falta tocar este componente.
export default function Pendiente({ historia, titulo, responsable, archivo, endpoints = [] }) {
  return (
    <section className="pendiente">
      <span className="etiqueta-superior">{historia} · EN CONSTRUCCIÓN</span>
      <h2>{titulo}</h2>
      <p>
        Esta pantalla la arma <strong>{responsable}</strong> en <code>{archivo}</code>.
        La sesión, el menú y el token ya vienen de la estructura común.
      </p>
      {endpoints.length > 0 && (
        <>
          <h3>Endpoints que usa (por Kong)</h3>
          <ul>
            {endpoints.map((endpoint) => <li key={endpoint}><code>{endpoint}</code></li>)}
          </ul>
        </>
      )}
    </section>
  )
}
