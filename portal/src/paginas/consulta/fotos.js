// Fotos de referencia de las especies del catálogo, con licencia libre de Wikimedia Commons.
// Las licencias CC BY y CC BY-SA exigen citar al autor y la licencia: la ficha lo muestra
// debajo de la foto y portal/public/especies/CREDITOS.md lo resume.
const FOTOS = {
  'Phyllobates terribilis': {
    src: '/especies/phyllobates-terribilis.jpg',
    tipo: 'Anfibio',
    autor: 'Holger Krisp',
    licencia: 'CC BY 3.0',
    licenciaUrl: 'https://creativecommons.org/licenses/by/3.0/',
    fuente: 'https://commons.wikimedia.org/wiki/File:Schrecklicher_Pfeilgiftfrosch_Phyllobates_terribilis.jpg',
  },
  'Setophaga cerulea': {
    src: '/especies/setophaga-cerulea.jpg',
    tipo: 'Ave',
    autor: 'Mdf',
    licencia: 'CC BY-SA 3.0',
    licenciaUrl: 'https://creativecommons.org/licenses/by-sa/3.0/',
    fuente: 'https://commons.wikimedia.org/wiki/File:Dendroica-cerulea-002.jpg',
  },
  'Thraupis episcopus': {
    src: '/especies/thraupis-episcopus.jpg',
    tipo: 'Ave',
    autor: 'Charles J. Sharp',
    licencia: 'CC BY-SA 4.0',
    licenciaUrl: 'https://creativecommons.org/licenses/by-sa/4.0/',
    fuente: 'https://commons.wikimedia.org/wiki/File:Blue-grey_tanager_(Thraupis_episcopus_quaesita)_Las_Tangaras.jpg',
  },
  'Dendrobates truncatus': {
    src: '/especies/dendrobates-truncatus.jpg',
    tipo: 'Anfibio',
    autor: 'José Gabriel Julio Guzmán',
    licencia: 'CC BY 4.0',
    licenciaUrl: 'https://creativecommons.org/licenses/by/4.0/',
    fuente: 'https://commons.wikimedia.org/wiki/File:Dendrobates_truncatus_62296583.jpg',
  },
  'Rupicola peruvianus': {
    src: '/especies/rupicola-peruvianus.jpg',
    tipo: 'Ave',
    autor: 'Charles J. Sharp',
    licencia: 'CC BY-SA 4.0',
    licenciaUrl: 'https://creativecommons.org/licenses/by-sa/4.0/',
    fuente: 'https://commons.wikimedia.org/wiki/File:Andean_cock-of-the-rock_(Rupicola_peruvianus)_Antioquia_4.jpg',
  },
  'Phoenicopterus ruber': {
    src: '/especies/phoenicopterus-ruber.jpg',
    tipo: 'Ave',
    autor: 'Charles J. Sharp',
    licencia: 'CC BY-SA 4.0',
    licenciaUrl: 'https://creativecommons.org/licenses/by-sa/4.0/',
    fuente: 'https://commons.wikimedia.org/wiki/File:American_flamingo_(Phoenicopterus_ruber).JPG',
  },
}

export function fotoDeEspecie(especie) {
  return FOTOS[String(especie || '').trim()] ?? null
}
