// Funciones de apoyo de las pantallas de Gobernanza y Reportes (HU-08, HU-12 y HU-15).
// Son puras (sin React ni red), así se prueban en utilidades.test.js.

const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
  'septiembre', 'octubre', 'noviembre', 'diciembre']

// "2026-10-20" o "2026-10-20T05:10:46Z" -> "20 oct. 2026"
export function fechaCorta(valor) {
  if (!valor) return 'Sin fecha'
  const texto = String(valor)
  const fecha = texto.length <= 10 ? new Date(`${texto}T12:00:00`) : new Date(texto)
  if (Number.isNaN(fecha.getTime())) return texto
  return new Intl.DateTimeFormat('es-CO', { day: '2-digit', month: 'short', year: 'numeric' }).format(fecha)
}

// Con hora, para "vigente desde" y "generado en".
export function fechaConHora(valor) {
  if (!valor) return 'Sin fecha'
  const fecha = new Date(valor)
  if (Number.isNaN(fecha.getTime())) return String(valor)
  return new Intl.DateTimeFormat('es-CO', {
    day: '2-digit', month: 'short', year: 'numeric', hour: 'numeric', minute: '2-digit',
  }).format(fecha)
}

export function nombreLugar(hallazgo) {
  return [hallazgo?.departamento, hallazgo?.region].filter(Boolean).join(', ') || 'Ubicación general no disponible'
}

// Busca por especie, región, departamento o ecosistema, sin importar tildes ni mayúsculas.
function normalizar(texto) {
  return String(texto ?? '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
}

export function filtrarHallazgos(hallazgos, busqueda) {
  const termino = normalizar(busqueda).trim()
  if (!termino) return hallazgos
  return hallazgos.filter((h) =>
    [h.especie, h.region, h.departamento, h.ecosistema].some((campo) => normalizar(campo).includes(termino)),
  )
}

// Las especies a las que se puede reclasificar: todas menos la que el hallazgo ya tiene.
export function especiesDestino(especies, especieActual) {
  return especies.filter((e) => e.nombreCientifico !== especieActual)
}

// error.detalles = [{ campo, mensaje }] -> { justificacion: 'La justificación es obligatoria' }
export function erroresPorCampo(error) {
  const resultado = {}
  for (const detalle of Array.isArray(error?.detalles) ? error.detalles : []) {
    if (detalle?.campo && !resultado[detalle.campo]) resultado[detalle.campo] = detalle.mensaje
  }
  return resultado
}

// Mensaje claro para cada error conocido del backend; si no lo conocemos, el que mandó el servicio.
const MENSAJES = {
  misma_especie: 'El hallazgo ya está clasificado como esa especie.',
  especie_no_existe: 'La especie elegida ya no existe en el catálogo.',
  hallazgo_no_existe: 'El hallazgo no existe o todavía no llegó a Gobernanza.',
  sin_version_en_fecha: 'En esa fecha el hallazgo todavía no se había registrado.',
  indices_no_generados: 'Ese mes todavía no tiene índices calculados.',
  periodo_invalido: 'El mes no es válido o todavía no ha empezado.',
  sin_permiso: 'Tu rol no tiene permiso para esta acción.',
}

export function mensajeError(error) {
  if (!error) return ''
  if (error.codigo && MENSAJES[error.codigo]) return MENSAJES[error.codigo]
  if (error.status === 403) return MENSAJES.sin_permiso
  if (!error.status) return 'No pudimos conectar con BioHub. Verifica que los servicios estén activos.'
  return error.message || 'Ocurrió un error inesperado.'
}

// "2026-11-18" de hoy, en la hora del navegador (Colombia para el equipo).
export function hoyIso(ahora = new Date()) {
  const y = ahora.getFullYear()
  const m = String(ahora.getMonth() + 1).padStart(2, '0')
  const d = String(ahora.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

// El mes que terminó: "2026-10" si hoy es noviembre de 2026.
export function mesAnterior(ahora = new Date()) {
  const fecha = new Date(ahora.getFullYear(), ahora.getMonth() - 1, 1)
  return `${fecha.getFullYear()}-${String(fecha.getMonth() + 1).padStart(2, '0')}`
}

export function mesActual(ahora = new Date()) {
  return `${ahora.getFullYear()}-${String(ahora.getMonth() + 1).padStart(2, '0')}`
}

// "2026-10" -> "octubre de 2026"
export function nombreMes(periodo) {
  const [anio, mes] = String(periodo || '').split('-').map(Number)
  if (!anio || !mes || mes < 1 || mes > 12) return String(periodo || '')
  return `${MESES[mes - 1]} de ${anio}`
}

// "atributos.altitudMsnm" -> "Altitud msnm"; "especie" -> "Especie"
export function etiquetaCampo(campo) {
  const limpio = String(campo).replace(/^atributos\./, '')
  const texto = limpio.replaceAll('_', ' ').replace(/([a-záéíóúñ])([A-ZÁÉÍÓÚÑ])/g, '$1 $2').toLocaleLowerCase('es-CO')
  return texto.charAt(0).toLocaleUpperCase('es-CO') + texto.slice(1)
}

export function valorLegible(valor) {
  if (valor === null || valor === undefined || valor === '') return '—'
  if (typeof valor === 'object') return JSON.stringify(valor)
  if (typeof valor === 'number') return valor.toLocaleString('es-CO')
  return String(valor)
}

// El autor llega como un id (UUID). Se muestra corto, sin inventar nombres que no tenemos.
export function autorCorto(id) {
  if (!id) return 'Autor desconocido'
  const texto = String(id)
  return texto.length > 12 ? `Usuario …${texto.slice(-6)}` : `Usuario ${texto}`
}

export const NIVELES = {
  ALTA: { texto: 'Alta', descripcion: 'Más actividad de lo habitual' },
  NORMAL: { texto: 'Normal', descripcion: 'Dentro de lo habitual' },
  BAJA: { texto: 'Baja', descripcion: 'Menos actividad de lo habitual' },
  SIN_HISTORIA: { texto: 'Sin historia', descripcion: 'Sin hallazgos en los 3 meses anteriores' },
}

// 2.5 -> "2,50"; null -> "—"
export function indiceLegible(indice) {
  if (indice === null || indice === undefined) return '—'
  return Number(indice).toLocaleString('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

// Ancho de la barra de un índice, en %, contra el índice más alto del mes (mínimo visible 2 %).
export function anchoBarra(indice, maximo) {
  if (indice === null || indice === undefined || !maximo) return 0
  return Math.max(2, Math.min(100, (Number(indice) / Number(maximo)) * 100))
}

export function resumenIndices(ecosistemas = []) {
  const conIndice = ecosistemas.filter((e) => e.indice !== null && e.indice !== undefined)
  return {
    ecosistemas: ecosistemas.length,
    hallazgos: ecosistemas.reduce((total, e) => total + (e.hallazgos || 0), 0),
    alta: ecosistemas.filter((e) => e.nivel === 'ALTA').length,
    maximo: conIndice.reduce((max, e) => Math.max(max, Number(e.indice)), 0),
  }
}
