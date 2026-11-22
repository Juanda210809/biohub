// Marco común del portal: barra lateral con el menú según el rol, barra superior y pie.
// Cada página solo pone su contenido; no repite el menú ni la sesión.
import { ir } from '../navegacion.js'
import { paginasDelMenu, RUTA_ENTRAR, RUTA_INICIO } from '../paginas.js'
import { nombreRol } from '../roles.js'
import { useSesion } from '../SesionContexto.jsx'

export default function Plantilla({ titulo, caminoActual, children }) {
  const { usuario, salir } = useSesion()
  const paginas = paginasDelMenu(usuario)
  const publicas = paginas.filter((pagina) => pagina.roles === null)
  const internas = paginas.filter((pagina) => pagina.roles !== null)

  async function cerrarSesion() {
    await salir()
    ir(RUTA_INICIO)
  }

  function enlace(pagina) {
    const activo = pagina.ruta === caminoActual
    return (
      <a
        key={pagina.ruta}
        className={`nav-enlace ${activo ? 'activo' : ''}`}
        href={`#${pagina.ruta}`}
        aria-current={activo ? 'page' : undefined}
      >
        <span className="icono" aria-hidden="true">{pagina.icono}</span>
        {pagina.titulo}
      </a>
    )
  }

  return (
    <div className="app-shell">
      <aside className="barra-lateral">
        <a className="marca" href="#/consulta">
          <span className="marca-icono">B</span>
          <span><strong>BioHub</strong><small>BIODIVERSIDAD COLOMBIA</small></span>
        </a>

        <nav className="nav-grupo" aria-label="Menú principal">
          <span className="nav-etiqueta">CONSULTA</span>
          {publicas.map(enlace)}
          {internas.length > 0 && <span className="nav-etiqueta nav-etiqueta-separada">MI TRABAJO</span>}
          {internas.map(enlace)}
        </nav>

        <div className="lateral-inferior">
          {usuario ? (
            <>
              <span className="lateral-version">SESIÓN INICIADA</span>
              <strong>{usuario.nombre}</strong>
              <p>{nombreRol(usuario.rol)}</p>
              <button type="button" className="boton boton-salir" onClick={cerrarSesion}>Cerrar sesión</button>
            </>
          ) : (
            <>
              <div className="lateral-hoja">❧</div>
              <strong>Personal del Instituto</strong>
              <p>Inicia sesión para registrar, revisar o administrar hallazgos.</p>
              <a className="boton boton-entrar" href={`#${RUTA_ENTRAR}`}>Iniciar sesión</a>
            </>
          )}
        </div>
      </aside>

      <main className="contenido-principal">
        <header className="barra-superior">
          <div className="migas"><span>BioHub</span><b>/</b><strong>{titulo}</strong></div>
          <div className="perfil-publico">
            <span className="perfil-punto" />
            {usuario ? `${usuario.nombre} · ${nombreRol(usuario.rol)}` : 'Consulta abierta'}
          </div>
        </header>

        <div className="contenido-pagina">
          {children}
          <footer className="pie-pagina">
            <span>© BioHub · Sistema Nacional de Registro y Vigilancia de Biodiversidad</span>
            <span>Información pública para la conservación <b>♥</b></span>
          </footer>
        </div>
      </main>
    </div>
  )
}
