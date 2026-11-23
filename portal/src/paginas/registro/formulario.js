// Lógica pura del formulario de registrar hallazgo (HU-03): valores iniciales, validación en el
// navegador y armado del cuerpo del POST. No usa React ni llama al backend, para poder probarla.

// Los tipos de atributo que la ficha puede traer (los mismos validadores del servicio Registro).
export const TIPOS_SOPORTADOS = ['NUMERO', 'TEXTO', 'FECHA', 'SELECCION']

// Fecha de hoy en la zona del navegador, como AAAA-MM-DD (toISOString daría la fecha en UTC).
export function hoyLocal(ahora = new Date()) {
  const mes = String(ahora.getMonth() + 1).padStart(2, '0')
  const dia = String(ahora.getDate()).padStart(2, '0')
  return `${ahora.getFullYear()}-${mes}-${dia}`
}

export function formularioInicial(ahora = new Date()) {
  return {
    especieId: '',
    expedicionId: '',
    fechaHallazgo: hoyLocal(ahora),
    latitud: '',
    longitud: '',
    precisionM: '',
    region: '',
    departamento: '',
    ecosistema: '',
    atributos: {},
  }
}

function vacio(valor) {
  return valor === undefined || valor === null || String(valor).trim() === ''
}

function esNumero(valor) {
  return !vacio(valor) && Number.isFinite(Number(valor))
}

// Nombres de lugar (región, departamento, ecosistema): letras, espacios, guiones, puntos y
// apóstrofos. Descarta cosas como "X" o "123"; no puede saber si el lugar existe de verdad.
const NOMBRE_VALIDO = /^\p{L}[\p{L}\s.'-]*$/u

function errorDeNombre(valor) {
  const texto = valor.trim()
  if (texto.length < 3) return 'Escribe al menos 3 letras'
  if (texto.length > 80) return 'No puede tener más de 80 caracteres'
  if (!NOMBRE_VALIDO.test(texto)) return 'Usa solo letras, espacios, guiones o puntos'
  return null
}

function errorDeAtributo(atributo, valor) {
  const reglas = atributo.reglas || {}
  if (atributo.tipo === 'NUMERO') {
    if (!esNumero(valor)) return 'debe ser un número'
    const numero = Number(valor)
    if (reglas.minimo != null && numero < reglas.minimo) return `debe ser mayor o igual a ${reglas.minimo}`
    if (reglas.maximo != null && numero > reglas.maximo) return `debe ser menor o igual a ${reglas.maximo}`
  }
  if (atributo.tipo === 'TEXTO') {
    const texto = String(valor)
    if (reglas.longitudMaxima != null && texto.length > reglas.longitudMaxima) {
      return `no puede tener más de ${reglas.longitudMaxima} caracteres`
    }
  }
  if (atributo.tipo === 'FECHA') {
    // AAAA-MM-DD se compara como texto sin problema.
    if (reglas.fechaMinima && valor < reglas.fechaMinima) return `no puede ser anterior a ${reglas.fechaMinima}`
    if (reglas.fechaMaxima && valor > reglas.fechaMaxima) return `no puede ser posterior a ${reglas.fechaMaxima}`
  }
  if (atributo.tipo === 'SELECCION') {
    const opciones = reglas.opciones || []
    if (!opciones.some((opcion) => String(opcion) === String(valor))) return 'escoge una de las opciones'
  }
  return null
}

// Devuelve { campo: mensaje }. Los atributos de la ficha van con la clave "atributos.<clave>".
export function validarFormulario(formulario, ficha) {
  const errores = {}

  if (vacio(formulario.especieId)) errores.especieId = 'Escoge la especie'
  if (vacio(formulario.expedicionId)) errores.expedicionId = 'Escoge la expedición'
  if (vacio(formulario.fechaHallazgo)) errores.fechaHallazgo = 'Indica la fecha del hallazgo'

  if (!esNumero(formulario.latitud)) errores.latitud = 'Escribe la latitud'
  else if (Math.abs(Number(formulario.latitud)) > 90) errores.latitud = 'La latitud va entre -90 y 90'

  if (!esNumero(formulario.longitud)) errores.longitud = 'Escribe la longitud'
  else if (Math.abs(Number(formulario.longitud)) > 180) errores.longitud = 'La longitud va entre -180 y 180'

  if (!vacio(formulario.precisionM) && (!esNumero(formulario.precisionM) || Number(formulario.precisionM) < 0)) {
    errores.precisionM = 'La precisión debe ser un número mayor o igual a 0'
  }

  if (vacio(formulario.region) && vacio(formulario.departamento)) {
    errores.region = 'Indica al menos la región o el departamento'
  }

  for (const campo of ['region', 'departamento', 'ecosistema']) {
    if (vacio(formulario[campo])) continue
    const mensaje = errorDeNombre(formulario[campo])
    if (mensaje) errores[campo] = mensaje
  }

  for (const atributo of ficha?.atributos ?? []) {
    if (!TIPOS_SOPORTADOS.includes(atributo.tipo)) continue
    const valor = formulario.atributos[atributo.clave]
    if (vacio(valor)) {
      if (atributo.obligatorio) errores[`atributos.${atributo.clave}`] = 'es obligatorio'
      continue
    }
    const mensaje = errorDeAtributo(atributo, valor)
    if (mensaje) errores[`atributos.${atributo.clave}`] = mensaje
  }

  return errores
}

// El cuerpo exacto que espera POST /api/v1/registro/hallazgos (JSON en camelCase).
export function construirCuerpo(formulario, ficha) {
  const cuerpo = {
    especieId: formulario.especieId,
    expedicionId: formulario.expedicionId,
    fechaHallazgo: formulario.fechaHallazgo,
    latitud: Number(formulario.latitud),
    longitud: Number(formulario.longitud),
    atributos: {},
  }
  if (!vacio(formulario.precisionM)) cuerpo.precisionM = Number(formulario.precisionM)
  for (const campo of ['region', 'departamento', 'ecosistema']) {
    if (!vacio(formulario[campo])) cuerpo[campo] = formulario[campo].trim()
  }

  for (const atributo of ficha?.atributos ?? []) {
    if (!TIPOS_SOPORTADOS.includes(atributo.tipo)) continue
    const valor = formulario.atributos[atributo.clave]
    if (vacio(valor)) continue
    if (atributo.tipo === 'NUMERO') cuerpo.atributos[atributo.clave] = Number(valor)
    else if (atributo.tipo === 'SELECCION') {
      const opcion = (atributo.reglas?.opciones || []).find((o) => String(o) === String(valor))
      cuerpo.atributos[atributo.clave] = opcion ?? valor
    } else cuerpo.atributos[atributo.clave] = String(valor).trim()
  }
  return cuerpo
}

// Convierte el error del servicio ({ detalles: [{ campo, mensaje }] }) en mensajes por campo.
// Lo que no corresponde a un campo del formulario va en "general".
export function erroresDelServidor(error, ficha) {
  const claves = new Set((ficha?.atributos ?? []).map((atributo) => atributo.clave))
  const campos = {}
  const general = []
  for (const detalle of error?.detalles ?? []) {
    const nombre = detalle?.campo
    if (nombre && claves.has(nombre)) campos[`atributos.${nombre}`] ??= detalle.mensaje
    else if (nombre && nombre !== 'cuerpo' && /^[a-zA-Z]+$/.test(nombre)) campos[nombre] ??= detalle.mensaje
    else if (detalle?.mensaje) general.push(detalle.mensaje)
  }
  return { campos, general }
}
