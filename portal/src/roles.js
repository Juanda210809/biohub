// Los roles internos de BioHub (los mismos de Identidad).
export const ROLES = {
  INVESTIGADOR: 'INVESTIGADOR',
  CIENTIFICO_AUTORIZADO: 'CIENTIFICO_AUTORIZADO',
  ALTO_RANGO: 'ALTO_RANGO',
  AUDITOR: 'AUDITOR',
  ADMINISTRADOR: 'ADMINISTRADOR',
}

export const ROLES_INTERNOS = Object.values(ROLES)

const NOMBRES = {
  INVESTIGADOR: 'Investigador',
  CIENTIFICO_AUTORIZADO: 'Científico autorizado',
  ALTO_RANGO: 'Científico de alto rango',
  AUDITOR: 'Auditor',
  ADMINISTRADOR: 'Administrador',
}

export function nombreRol(rol) {
  return NOMBRES[rol] || 'Sin rol asignado'
}
