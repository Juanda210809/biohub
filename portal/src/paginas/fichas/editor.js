// Lógica pura del editor de fichas (HU-04): pasa los atributos del servidor a filas editables,
// valida lo que valida el servicio (para avisar antes de enviar) y arma el cuerpo del PUT.
// No usa React ni llama al backend, para poder probarla.

export const TIPOS = [
  { valor: 'NUMERO', nombre: 'Número' },
  { valor: 'TEXTO', nombre: 'Texto' },
  { valor: 'FECHA', nombre: 'Fecha' },
  { valor: 'SELECCION', nombre: 'Selección (lista de opciones)' },
]

// Las mismas reglas que el servicio: clave en camelCase y etiqueta de hasta 100 caracteres.
const CLAVE_VALIDA = /^[a-z][a-zA-Z0-9]{0,59}$/
export const ETIQUETA_MAXIMA = 100

const REGLAS_VACIAS = {
  minimo: '', maximo: '', unidad: '', longitudMaxima: '', patron: '', fechaMinima: '', fechaMaxima: '', opciones: '',
}

let contador = 0
function nuevoId() {
  contador += 1
  return `fila-${contador}`
}

function texto(valor) {
  return valor === undefined || valor === null ? '' : String(valor)
}

function vacio(valor) {
  return String(valor ?? '').trim() === ''
}

// Un atributo que ya está en la ficha vigente: su clave y su tipo no se pueden cambiar.
export function filaDesdeAtributo(atributo) {
  const reglas = atributo.reglas || {}
  return {
    id: nuevoId(),
    existente: true,
    clave: atributo.clave,
    etiqueta: atributo.etiqueta,
    tipo: atributo.tipo,
    obligatorio: Boolean(atributo.obligatorio),
    publicable: Boolean(atributo.publicable),
    reglas: {
      ...REGLAS_VACIAS,
      minimo: texto(reglas.minimo),
      maximo: texto(reglas.maximo),
      unidad: texto(reglas.unidad),
      longitudMaxima: texto(reglas.longitudMaxima),
      patron: texto(reglas.patron),
      fechaMinima: texto(reglas.fechaMinima),
      fechaMaxima: texto(reglas.fechaMaxima),
      opciones: Array.isArray(reglas.opciones) ? reglas.opciones.join('\n') : '',
    },
  }
}

export function filaNueva() {
  return {
    id: nuevoId(), existente: false, clave: '', etiqueta: '', tipo: 'TEXTO',
    obligatorio: false, publicable: false, reglas: { ...REGLAS_VACIAS },
  }
}

export function opcionesDe(fila) {
  return fila.reglas.opciones.split('\n').map((opcion) => opcion.trim()).filter(Boolean)
}

// Solo las reglas que corresponden al tipo de la fila (las demás se ignoran).
export function construirReglas(fila) {
  const reglas = fila.reglas
  const salida = {}
  if (fila.tipo === 'NUMERO') {
    if (!vacio(reglas.minimo)) salida.minimo = Number(reglas.minimo)
    if (!vacio(reglas.maximo)) salida.maximo = Number(reglas.maximo)
    if (!vacio(reglas.unidad)) salida.unidad = reglas.unidad.trim()
  } else if (fila.tipo === 'TEXTO') {
    if (!vacio(reglas.longitudMaxima)) salida.longitudMaxima = Number(reglas.longitudMaxima)
    if (!vacio(reglas.patron)) salida.patron = reglas.patron
  } else if (fila.tipo === 'FECHA') {
    if (!vacio(reglas.fechaMinima)) salida.fechaMinima = reglas.fechaMinima
    if (!vacio(reglas.fechaMaxima)) salida.fechaMaxima = reglas.fechaMaxima
  } else if (fila.tipo === 'SELECCION') {
    salida.opciones = opcionesDe(fila)
  }
  return salida
}

function erroresDeReglas(fila) {
  const reglas = fila.reglas
  const errores = []
  if (fila.tipo === 'NUMERO') {
    const minimoOk = vacio(reglas.minimo) || Number.isFinite(Number(reglas.minimo))
    const maximoOk = vacio(reglas.maximo) || Number.isFinite(Number(reglas.maximo))
    if (!minimoOk) errores.push('El mínimo debe ser un número.')
    if (!maximoOk) errores.push('El máximo debe ser un número.')
    if (minimoOk && maximoOk && !vacio(reglas.minimo) && !vacio(reglas.maximo)
      && Number(reglas.minimo) > Number(reglas.maximo)) {
      errores.push('El mínimo no puede ser mayor que el máximo.')
    }
  } else if (fila.tipo === 'TEXTO') {
    if (!vacio(reglas.longitudMaxima)) {
      const largo = Number(reglas.longitudMaxima)
      if (!Number.isInteger(largo) || largo < 1) errores.push('La longitud máxima debe ser un entero mayor o igual a 1.')
    }
  } else if (fila.tipo === 'FECHA') {
    if (!vacio(reglas.fechaMinima) && !vacio(reglas.fechaMaxima) && reglas.fechaMinima > reglas.fechaMaxima) {
      errores.push('La fecha mínima no puede ser posterior a la máxima.')
    }
  } else if (fila.tipo === 'SELECCION') {
    const opciones = opcionesDe(fila)
    if (opciones.length === 0) errores.push('Escribe al menos una opción (una por línea).')
    else if (new Set(opciones).size !== opciones.length) errores.push('Las opciones no pueden repetirse.')
  }
  return errores
}

// { porFila: { [posición]: { clave, etiqueta, reglas } }, general: [mensajes] }
export function validarFilas(filas) {
  const porFila = {}
  const general = []
  const poner = (posicion, campo, mensaje) => {
    porFila[posicion] ??= {}
    porFila[posicion][campo] ??= mensaje
  }

  if (filas.length === 0) general.push('La ficha debe tener al menos un atributo.')

  const vistas = new Set()
  filas.forEach((fila, posicion) => {
    const clave = fila.clave.trim()
    if (!CLAVE_VALIDA.test(clave)) {
      poner(posicion, 'clave', 'Empieza con minúscula y usa solo letras y números, sin espacios (máximo 60). Ejemplo: temperaturaAgua')
    } else if (vistas.has(clave)) {
      poner(posicion, 'clave', 'Esta clave ya está en otro atributo')
    }
    vistas.add(clave)

    const etiqueta = fila.etiqueta.trim()
    if (etiqueta === '') poner(posicion, 'etiqueta', 'Escribe la etiqueta que verá el investigador')
    else if (etiqueta.length > ETIQUETA_MAXIMA) poner(posicion, 'etiqueta', `Máximo ${ETIQUETA_MAXIMA} caracteres`)

    const reglas = erroresDeReglas(fila)
    if (reglas.length > 0) poner(posicion, 'reglas', reglas.join(' '))
  })

  return { porFila, general }
}

export function hayErrores(errores) {
  return errores.general.length > 0 || Object.keys(errores.porFila).length > 0
}

function atributosDe(filas) {
  return filas.map((fila) => ({
    clave: fila.clave.trim(),
    etiqueta: fila.etiqueta.trim(),
    tipo: fila.tipo,
    obligatorio: fila.obligatorio,
    publicable: fila.publicable,
    reglas: construirReglas(fila),
  }))
}

// El cuerpo exacto de PUT /api/v1/registro/tipos-especie/{id}/ficha: la lista COMPLETA de atributos.
export function construirCuerpo(revisionBase, filas) {
  return { revisionBase, atributos: atributosDe(filas) }
}

// Sirve para saber si hay cambios sin publicar (compara contra la firma de cuando se cargó).
export function firma(filas) {
  return JSON.stringify(atributosDe(filas))
}

const CAMPOS_DE_FILA = ['clave', 'etiqueta', 'tipo', 'reglas']

// Convierte el error del servicio ({ detalles: [{ campo: "atributos[2].clave", mensaje }] }).
export function erroresDelServidor(error) {
  const porFila = {}
  const general = []
  for (const detalle of error?.detalles ?? []) {
    const coincide = /^atributos(?:\[(\d+)\]|\.(\d+))\.(\w+)$/.exec(detalle?.campo ?? '')
    if (coincide) {
      const posicion = Number(coincide[1] ?? coincide[2])
      const campo = CAMPOS_DE_FILA.includes(coincide[3]) ? coincide[3] : 'otro'
      porFila[posicion] ??= {}
      porFila[posicion][campo] ??= detalle.mensaje
    } else if (detalle?.mensaje) {
      general.push(detalle.campo && detalle.campo !== 'cuerpo' ? `${detalle.campo}: ${detalle.mensaje}` : detalle.mensaje)
    }
  }
  return { porFila, general }
}

// Los tipos de especie salen de las especies del catálogo (no hay un endpoint aparte).
export function tiposDeEspecie(especies) {
  const tipos = new Map()
  for (const especie of especies) {
    if (!tipos.has(especie.tipoEspecieId)) tipos.set(especie.tipoEspecieId, especie.tipoEspecie)
  }
  return [...tipos]
    .map(([id, nombre]) => ({ id, nombre }))
    .sort((a, b) => a.nombre.localeCompare(b.nombre, 'es'))
}
