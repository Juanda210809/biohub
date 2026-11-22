// Las páginas del portal: ruta, quién la ve en el menú y qué componente muestra.
// Para agregar una pantalla: crea su archivo en src/paginas/<parte>/ y súmala aquí.
//
// "roles" solo decide qué aparece en el menú y qué páginas pide iniciar sesión. Lo que de verdad
// protege los datos es el PDP: cada servicio vuelve a preguntar con el token (RNF-05).
import ConsultaPublica from './paginas/consulta/ConsultaPublica.jsx'
import DefinirFicha from './paginas/fichas/DefinirFicha.jsx'
import Historial from './paginas/historial/Historial.jsx'
import IndicesPresion from './paginas/indices/IndicesPresion.jsx'
import UbicacionHallazgo from './paginas/mapa/UbicacionHallazgo.jsx'
import Reclasificar from './paginas/reclasificar/Reclasificar.jsx'
import RegistrarHallazgo from './paginas/registro/RegistrarHallazgo.jsx'
import GestionUsuarios from './paginas/usuarios/GestionUsuarios.jsx'
import { rutaSegura } from './navegacion.js'
import { ROLES, ROLES_INTERNOS } from './roles.js'

export const RUTA_INICIO = '/consulta'
export const RUTA_ENTRAR = '/entrar'

export const PAGINAS = [
  { ruta: '/consulta', titulo: 'Consulta pública', icono: '◫', roles: null, componente: ConsultaPublica },
  { ruta: '/registro', titulo: 'Registrar hallazgo', icono: '✚', roles: [ROLES.INVESTIGADOR], componente: RegistrarHallazgo },
  { ruta: '/fichas', titulo: 'Definir fichas', icono: '☰', roles: [ROLES.CIENTIFICO_AUTORIZADO], componente: DefinirFicha },
  { ruta: '/mapa', titulo: 'Ver en el mapa', icono: '⌖', roles: ROLES_INTERNOS, componente: UbicacionHallazgo },
  { ruta: '/reclasificar', titulo: 'Reclasificar hallazgo', icono: '⇄', roles: [ROLES.CIENTIFICO_AUTORIZADO], componente: Reclasificar },
  { ruta: '/historial', titulo: 'Historial y versiones', icono: '↺', roles: [ROLES.AUDITOR], componente: Historial },
  { ruta: '/indices', titulo: 'Índices de presión', icono: '▤', roles: [ROLES.ALTO_RANGO], componente: IndicesPresion },
  { ruta: '/usuarios', titulo: 'Usuarios y roles', icono: '☺', roles: [ROLES.ADMINISTRADOR], componente: GestionUsuarios },
]

export function buscarPagina(camino) {
  return PAGINAS.find((pagina) => pagina.ruta === camino) ?? null
}

export function esPublica(pagina) {
  return pagina.roles === null
}

export function puedeVer(pagina, usuario) {
  if (esPublica(pagina)) return true
  return Boolean(usuario?.rol) && pagina.roles.includes(usuario.rol)
}

export function paginasDelMenu(usuario) {
  return PAGINAS.filter((pagina) => puedeVer(pagina, usuario))
}

// Después de iniciar sesión: vuelve a la página que pidió si su rol la puede ver; si no, al inicio.
export function destinoTrasEntrar(volver, usuario) {
  const pagina = buscarPagina(rutaSegura(volver, RUTA_INICIO))
  return pagina && puedeVer(pagina, usuario) ? pagina.ruta : RUTA_INICIO
}
