// HU-02 · HU-18 · Usuarios y roles.
// HU-18: crear, modificar, desactivar y reactivar cuentas internas (nunca se borran: RNF-09).
// HU-02: asignar uno de los 5 roles o dejar la cuenta sin rol; los permisos cambian de inmediato.
// El menú solo muestra esta página al ADMINISTRADOR, pero quien protege es el PDP de Identidad.
import { useEffect, useMemo, useState } from 'react'
import { nombreRol, ROLES_INTERNOS } from '../../roles.js'
import { actualizarUsuario } from '../../sesion.js'
import { useSesion } from '../../SesionContexto.jsx'
import {
  activarCuenta,
  asignarRol,
  CLAVE_MAXIMA,
  CLAVE_MINIMA,
  cambiosCuenta,
  crearCuenta,
  desactivarCuenta,
  erroresDelServidor,
  filtrarUsuarios,
  listarUsuarios,
  mensajeGeneral,
  modificarCuenta,
  reemplazarUsuario,
  resumenCuentas,
  SIN_ROL,
  validarCuenta,
} from './usuarios.js'
import './usuarios.css'

function SelectorRol({ valor, onChange, disabled, etiqueta, incluirTodos = false }) {
  return (
    <select value={valor} onChange={(evento) => onChange(evento.target.value)} disabled={disabled} aria-label={etiqueta}>
      {incluirTodos && <option value="TODOS">Todos los roles</option>}
      <option value={SIN_ROL}>Sin rol</option>
      {ROLES_INTERNOS.map((rol) => <option key={rol} value={rol}>{nombreRol(rol)}</option>)}
    </select>
  )
}

function Campo({ etiqueta, error, ayuda, children }) {
  return (
    <label className="usuarios-campo">
      <span>{etiqueta}</span>
      {children}
      {error ? <small className="usuarios-error-campo">{error}</small> : ayuda && <small className="texto-suave">{ayuda}</small>}
    </label>
  )
}

function FormularioCuenta({ cuenta, onCancelar, onGuardado }) {
  const nueva = !cuenta
  const [datos, setDatos] = useState({
    nombre: cuenta?.nombre ?? '',
    correo: cuenta?.correo ?? '',
    contrasena: '',
    confirmacion: '',
    rol: SIN_ROL,
  })
  const [errores, setErrores] = useState({})
  const [general, setGeneral] = useState('')
  const [guardando, setGuardando] = useState(false)

  function cambiar(campo) {
    return (evento) => setDatos((previos) => ({ ...previos, [campo]: evento.target.value }))
  }

  async function guardar(evento) {
    evento.preventDefault()
    setGeneral('')
    const encontrados = validarCuenta(datos, { nueva })
    setErrores(encontrados)
    if (Object.keys(encontrados).length > 0) return

    setGuardando(true)
    try {
      if (nueva) {
        const creada = await crearCuenta({
          nombre: datos.nombre.trim(),
          correo: datos.correo.trim().toLowerCase(),
          contrasena: datos.contrasena,
        })
        if (datos.rol === SIN_ROL) {
          onGuardado(creada, `Cuenta de ${creada.nombre} creada sin rol: no podrá usar funciones internas hasta que le asignes uno.`)
          return
        }
        try {
          const conRol = await asignarRol(creada.id, datos.rol)
          onGuardado(conRol, `Cuenta de ${conRol.nombre} creada con el rol ${nombreRol(conRol.rol)}.`)
        } catch (fallo) {
          onGuardado(creada, `La cuenta se creó, pero no se pudo asignar el rol: ${mensajeGeneral(fallo)} Asígnalo desde la tabla.`, 'error')
        }
        return
      }

      const cambios = cambiosCuenta(cuenta, datos)
      if (Object.keys(cambios).length === 0) {
        setGeneral('No hay cambios para guardar.')
        return
      }
      const modificada = await modificarCuenta(cuenta.id, cambios)
      onGuardado(modificada, `Se guardaron los cambios de ${modificada.nombre}.`)
    } catch (fallo) {
      const { campos, general: mensaje } = erroresDelServidor(fallo)
      setErrores(campos)
      setGeneral(mensaje)
    } finally {
      setGuardando(false)
    }
  }

  return (
    <form className="usuarios-panel" onSubmit={guardar} noValidate>
      <div className="usuarios-panel-titulo">
        <div>
          <span className="etiqueta-superior">{nueva ? 'NUEVA CUENTA INTERNA' : 'MODIFICAR CUENTA'}</span>
          <h3>{nueva ? 'Crear cuenta' : `Editar a ${cuenta.nombre}`}</h3>
        </div>
        <button type="button" className="boton boton-secundario" onClick={onCancelar} disabled={guardando}>Cancelar</button>
      </div>

      <div className="usuarios-rejilla-campos">
        <Campo etiqueta="Nombre completo" error={errores.nombre}>
          <input value={datos.nombre} onChange={cambiar('nombre')} maxLength={120} autoComplete="off" aria-invalid={Boolean(errores.nombre)} autoFocus />
        </Campo>
        <Campo etiqueta="Correo" error={errores.correo}>
          <input type="email" value={datos.correo} onChange={cambiar('correo')} autoComplete="off" aria-invalid={Boolean(errores.correo)} />
        </Campo>
        <Campo
          etiqueta={nueva ? 'Contraseña inicial' : 'Nueva contraseña (opcional)'}
          error={errores.contrasena}
          ayuda={nueva ? `Entre ${CLAVE_MINIMA} y ${CLAVE_MAXIMA} caracteres.` : 'Déjala vacía para no cambiarla.'}
        >
          <input type="password" value={datos.contrasena} onChange={cambiar('contrasena')} autoComplete="new-password" aria-invalid={Boolean(errores.contrasena)} />
        </Campo>
        <Campo etiqueta="Confirmar contraseña" error={errores.confirmacion}>
          <input type="password" value={datos.confirmacion} onChange={cambiar('confirmacion')} autoComplete="new-password" aria-invalid={Boolean(errores.confirmacion)} />
        </Campo>
        {nueva && (
          <Campo etiqueta="Rol" ayuda="Puedes crearla sin rol y asignarlo después.">
            <SelectorRol valor={datos.rol} onChange={(rol) => setDatos((previos) => ({ ...previos, rol }))} etiqueta="Rol de la cuenta nueva" />
          </Campo>
        )}
      </div>

      {general && <p className="aviso-error" role="alert">{general}</p>}

      <div className="usuarios-panel-acciones">
        <button type="submit" className="boton boton-primario" disabled={guardando}>
          {guardando ? 'Guardando…' : nueva ? 'Crear cuenta' : 'Guardar cambios'}
        </button>
      </div>
    </form>
  )
}

export default function GestionUsuarios() {
  const { usuario: yo } = useSesion()
  const [usuarios, setUsuarios] = useState([])
  const [cargando, setCargando] = useState(true)
  const [errorCarga, setErrorCarga] = useState(null)
  const [recarga, setRecarga] = useState(0)
  const [filtros, setFiltros] = useState({ texto: '', estado: 'TODOS', rol: 'TODOS' })
  // null: sin formulario · { cuenta: null }: crear · { cuenta }: editar
  const [formulario, setFormulario] = useState(null)
  const [ocupado, setOcupado] = useState(null)
  const [aviso, setAviso] = useState(null)

  useEffect(() => {
    const controlador = new AbortController()
    setCargando(true)
    setErrorCarga(null)
    listarUsuarios({ signal: controlador.signal })
      .then((lista) => setUsuarios(Array.isArray(lista) ? lista : []))
      .catch((fallo) => {
        if (fallo.name !== 'AbortError') setErrorCarga(fallo)
      })
      .finally(() => {
        if (!controlador.signal.aborted) setCargando(false)
      })
    return () => controlador.abort()
  }, [recarga])

  const visibles = useMemo(() => filtrarUsuarios(usuarios, filtros), [usuarios, filtros])
  const resumen = useMemo(() => resumenCuentas(usuarios), [usuarios])
  const hayFiltros = filtros.texto || filtros.estado !== 'TODOS' || filtros.rol !== 'TODOS'

  function filtrar(campo, valor) {
    setFiltros((previos) => ({ ...previos, [campo]: valor }))
  }

  // Pone la cuenta que devolvió Identidad en la tabla. Si es la propia, actualiza la barra lateral.
  function aplicar(cuenta) {
    setUsuarios((lista) => (lista.some((u) => u.id === cuenta.id) ? reemplazarUsuario(lista, cuenta) : [...lista, cuenta]))
    if (cuenta.id === yo?.id) actualizarUsuario(cuenta)
  }

  function alGuardar(cuenta, texto, tipo = 'exito') {
    aplicar(cuenta)
    setFormulario(null)
    setAviso({ tipo, texto })
  }

  async function cambiarRol(cuenta, rol) {
    setOcupado(cuenta.id)
    setAviso(null)
    try {
      const actualizada = await asignarRol(cuenta.id, rol)
      aplicar(actualizada)
      setAviso({
        tipo: 'exito',
        texto: actualizada.rol
          ? `${actualizada.nombre} ahora es ${nombreRol(actualizada.rol)}. Sus permisos cambian desde su siguiente acción.`
          : `${actualizada.nombre} quedó sin rol: ya no puede usar funciones internas.`,
      })
    } catch (fallo) {
      setAviso({ tipo: 'error', texto: mensajeGeneral(fallo) })
    } finally {
      setOcupado(null)
    }
  }

  async function alternarActivo(cuenta) {
    if (cuenta.activo && !window.confirm(
      `¿Desactivar la cuenta de ${cuenta.nombre}?\n\nNo podrá iniciar sesión y sus sesiones abiertas dejarán de servir. `
      + 'La cuenta no se borra: su autoría en reclasificaciones pasadas se conserva.',
    )) return

    setOcupado(cuenta.id)
    setAviso(null)
    try {
      const actualizada = cuenta.activo ? await desactivarCuenta(cuenta.id) : await activarCuenta(cuenta.id)
      aplicar(actualizada)
      setAviso({
        tipo: 'exito',
        texto: actualizada.activo
          ? `La cuenta de ${actualizada.nombre} está activa de nuevo.`
          : `La cuenta de ${actualizada.nombre} quedó desactivada. Su historial se conserva.`,
      })
    } catch (fallo) {
      setAviso({ tipo: 'error', texto: mensajeGeneral(fallo) })
    } finally {
      setOcupado(null)
    }
  }

  return (
    <section className="usuarios">
      <div className="usuarios-encabezado">
        <div>
          <span className="etiqueta-superior">ADMINISTRACIÓN</span>
          <h2>Usuarios y roles</h2>
          <p className="texto-suave">Crea y administra las cuentas internas del Instituto y decide qué rol tiene cada una.</p>
        </div>
        {!formulario && (
          <button type="button" className="boton boton-primario" onClick={() => { setAviso(null); setFormulario({ cuenta: null }) }}>
            + Nueva cuenta
          </button>
        )}
      </div>

      {!cargando && !errorCarga && (
        <div className="usuarios-resumen">
          <div><strong>{resumen.total}</strong><span>cuentas</span></div>
          <div><strong>{resumen.activas}</strong><span>activas</span></div>
          <div><strong>{resumen.desactivadas}</strong><span>desactivadas</span></div>
          <div className={resumen.sinRol ? 'usuarios-resumen-alerta' : ''}><strong>{resumen.sinRol}</strong><span>sin rol</span></div>
        </div>
      )}

      {aviso && (
        <div className={aviso.tipo === 'error' ? 'aviso-error' : 'usuarios-aviso-exito'} role={aviso.tipo === 'error' ? 'alert' : 'status'}>
          <span>{aviso.texto}</span>
          <button type="button" className="usuarios-cerrar-aviso" onClick={() => setAviso(null)} aria-label="Cerrar aviso">×</button>
        </div>
      )}

      {formulario && (
        <FormularioCuenta
          key={formulario.cuenta?.id ?? 'nueva'}
          cuenta={formulario.cuenta}
          onCancelar={() => setFormulario(null)}
          onGuardado={alGuardar}
        />
      )}

      <div className="usuarios-herramientas">
        <input
          type="search"
          placeholder="Buscar por nombre o correo…"
          value={filtros.texto}
          onChange={(evento) => filtrar('texto', evento.target.value)}
          aria-label="Buscar cuentas por nombre o correo"
        />
        <select value={filtros.estado} onChange={(evento) => filtrar('estado', evento.target.value)} aria-label="Filtrar por estado">
          <option value="TODOS">Todas las cuentas</option>
          <option value="ACTIVAS">Activas</option>
          <option value="DESACTIVADAS">Desactivadas</option>
        </select>
        <SelectorRol valor={filtros.rol} onChange={(rol) => filtrar('rol', rol)} etiqueta="Filtrar por rol" incluirTodos />
      </div>

      {cargando && <p className="cargando-linea">Cargando cuentas…</p>}

      {!cargando && errorCarga && (
        <div className="estado-vacio" role="alert">
          <span className="estado-icono">{errorCarga.status === 403 ? '🔒' : '⚠️'}</span>
          <h3>{errorCarga.status === 403 ? 'Sin permiso para administrar cuentas' : 'No pudimos cargar las cuentas'}</h3>
          <p>{mensajeGeneral(errorCarga)}</p>
          <button type="button" className="boton boton-primario" onClick={() => setRecarga((valor) => valor + 1)}>Intentar de nuevo</button>
        </div>
      )}

      {!cargando && !errorCarga && visibles.length === 0 && (
        <div className="estado-vacio">
          <span className="estado-icono">🍃</span>
          <h3>{hayFiltros ? 'Ninguna cuenta coincide' : 'Todavía no hay cuentas'}</h3>
          {hayFiltros && (
            <button type="button" className="boton boton-secundario" onClick={() => setFiltros({ texto: '', estado: 'TODOS', rol: 'TODOS' })}>
              Limpiar filtros
            </button>
          )}
        </div>
      )}

      {!cargando && !errorCarga && visibles.length > 0 && (
        <div className="usuarios-tabla-contenedor">
          <table className="usuarios-tabla">
            <thead>
              <tr>
                <th scope="col">Nombre</th>
                <th scope="col">Correo</th>
                <th scope="col">Rol</th>
                <th scope="col">Estado</th>
                <th scope="col"><span className="usuarios-oculto">Acciones</span></th>
              </tr>
            </thead>
            <tbody>
              {visibles.map((cuenta) => {
                const esYo = cuenta.id === yo?.id
                const enProceso = ocupado === cuenta.id
                return (
                  <tr key={cuenta.id} className={cuenta.activo ? '' : 'usuarios-fila-inactiva'}>
                    <td>
                      <strong>{cuenta.nombre}</strong>
                      {esYo && <span className="usuarios-insignia-yo">Tú</span>}
                    </td>
                    <td className="usuarios-correo">{cuenta.correo}</td>
                    <td>
                      <SelectorRol
                        valor={cuenta.rol ?? SIN_ROL}
                        onChange={(rol) => cambiarRol(cuenta, rol)}
                        disabled={enProceso || esYo}
                        etiqueta={`Rol de ${cuenta.nombre}`}
                      />
                      {esYo && <small className="texto-suave usuarios-nota-fila">No puedes quitarte tu rol.</small>}
                    </td>
                    <td>
                      <span className={`usuarios-estado ${cuenta.activo ? 'usuarios-estado-activa' : 'usuarios-estado-inactiva'}`}>
                        {cuenta.activo ? 'Activa' : 'Desactivada'}
                      </span>
                    </td>
                    <td className="usuarios-acciones">
                      <button
                        type="button"
                        className="boton boton-secundario"
                        onClick={() => { setAviso(null); setFormulario({ cuenta }) }}
                        disabled={enProceso}
                      >
                        Editar
                      </button>
                      <button
                        type="button"
                        className={`boton ${cuenta.activo ? 'usuarios-boton-peligro' : 'boton-secundario'}`}
                        onClick={() => alternarActivo(cuenta)}
                        disabled={enProceso || esYo}
                        title={esYo ? 'No puedes desactivar tu propia cuenta' : undefined}
                      >
                        {enProceso ? '…' : cuenta.activo ? 'Desactivar' : 'Activar'}
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      <p className="usuarios-nota">
        Las cuentas nunca se borran: una cuenta desactivada no puede iniciar sesión, pero conserva su autoría en las
        reclasificaciones pasadas. Una cuenta sin rol no puede usar ninguna función interna.
      </p>
    </section>
  )
}
