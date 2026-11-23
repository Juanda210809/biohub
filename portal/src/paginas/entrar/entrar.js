// HU-01 · Reglas de la pantalla de inicio de sesión, separadas del diseño para poder probarlas.
const PATRON_CORREO = /^[^@\s]+@[^@\s]+\.[^@\s]+$/

// Revisa el formulario antes de llamar a Identidad. Devuelve { campo: mensaje } (vacío = todo bien).
export function validarCredenciales(correo, contrasena) {
  const errores = {}
  const correoLimpio = String(correo ?? '').trim()
  if (!correoLimpio) errores.correo = 'Escribe tu correo.'
  else if (!PATRON_CORREO.test(correoLimpio)) errores.correo = 'Escribe un correo válido, por ejemplo nombre@biohub.local.'
  if (!contrasena) errores.contrasena = 'Escribe tu contraseña.'
  return errores
}

// Traduce el error de Identidad a un mensaje para la persona.
// Con 401 nunca dice si falló el correo o la contraseña (criterio de HU-01).
export function mensajeErrorEntrar(fallo) {
  switch (fallo?.status) {
    case 401:
      return 'Correo o contraseña incorrectos. Si el problema sigue, pide al administrador que revise tu cuenta.'
    case 422:
      return 'Revisa el correo y la contraseña.'
    case 429:
      return 'Hiciste muchos intentos seguidos. Espera un minuto y vuelve a intentarlo.'
    case 503:
      return 'El inicio de sesión no está disponible en este momento. Intenta de nuevo en unos minutos.'
    default:
      return 'No pudimos conectar con BioHub. Verifica que los servicios estén activos.'
  }
}
