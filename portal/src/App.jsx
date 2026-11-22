// Estructura común del portal: elige la página según el hash (#/registro), pide iniciar sesión
// cuando hace falta y muestra "sin permiso" si el rol no corresponde.
import { useEffect, useState } from 'react'
import { EVENTO_SESION_VENCIDA } from './api.js'
import Plantilla from './componentes/Plantilla.jsx'
import { ir, leerRuta, useHash } from './navegacion.js'
import Entrar from './paginas/entrar/Entrar.jsx'
import { buscarPagina, destinoTrasEntrar, esPublica, puedeVer, RUTA_ENTRAR, RUTA_INICIO } from './paginas.js'
import { ProveedorSesion, useSesion } from './SesionContexto.jsx'

function Redirigir({ a }) {
  useEffect(() => {
    ir(a)
  }, [a])
  return null
}

function SinPermiso() {
  return (
    <section className="estado-vacio estado-error" role="alert">
      <span className="estado-icono">🔒</span>
      <h3>No tienes permiso para esta pantalla</h3>
      <p>Tu rol no incluye esta función. Si crees que es un error, pídele al administrador que revise tu rol.</p>
      <a className="boton boton-secundario" href={`#${RUTA_INICIO}`}>Ir a la consulta pública</a>
    </section>
  )
}

function Paginas() {
  const hash = useHash()
  const { camino, parametros } = leerRuta(hash)
  const { usuario, verificando } = useSesion()
  const [aviso, setAviso] = useState('')

  // Si Identidad deja de aceptar el token, se vuelve a iniciar sesión en la misma página.
  useEffect(() => {
    const alVencer = () => {
      const { camino: actual } = leerRuta()
      setAviso('Tu sesión terminó. Vuelve a iniciar sesión para continuar.')
      if (actual !== RUTA_ENTRAR) ir(`${RUTA_ENTRAR}?volver=${actual}`)
    }
    window.addEventListener(EVENTO_SESION_VENCIDA, alVencer)
    return () => window.removeEventListener(EVENTO_SESION_VENCIDA, alVencer)
  }, [])

  useEffect(() => {
    if (usuario) setAviso('')
  }, [usuario])

  if (camino === '/') return <Redirigir a={RUTA_INICIO} />

  if (camino === RUTA_ENTRAR) {
    const volver = parametros.get('volver')
    if (usuario) return <Redirigir a={destinoTrasEntrar(volver, usuario)} />
    return (
      <Plantilla titulo="Iniciar sesión" caminoActual={camino}>
        <Entrar volver={volver} aviso={aviso} />
      </Plantilla>
    )
  }

  const pagina = buscarPagina(camino)
  if (!pagina) return <Redirigir a={RUTA_INICIO} />

  if (!esPublica(pagina)) {
    if (verificando) {
      return <Plantilla titulo={pagina.titulo} caminoActual={camino}><p className="cargando-linea">Verificando la sesión…</p></Plantilla>
    }
    if (!usuario) return <Redirigir a={`${RUTA_ENTRAR}?volver=${pagina.ruta}`} />
  }

  const Componente = pagina.componente
  return (
    <Plantilla titulo={pagina.titulo} caminoActual={camino}>
      {puedeVer(pagina, usuario) ? <Componente /> : <SinPermiso />}
    </Plantilla>
  )
}

export default function App() {
  return (
    <ProveedorSesion>
      <Paginas />
    </ProveedorSesion>
  )
}
