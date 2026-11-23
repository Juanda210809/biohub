# Datos de demostración

Al levantar el sistema (`docker compose up`), el servicio `datos-demo` carga **57 hallazgos de julio a noviembre de 2026**, de **6 especies** en **9 zonas** de las 5 regiones naturales, para que la demo muestre todas las historias con datos que tienen sentido. Corre una sola vez y termina; si los datos ya estaban, no duplica nada.

| Archivo | Qué es |
|---|---|
| `datos-demo.sql` | Los hallazgos: coordenadas, versiones, auditoría y su copia pública |
| `cargar-datos-demo.sh` | Espera a que Registro y Gobernanza creen sus tablas, carga el SQL y espera la copia en BD Reportes |
| `generar_datos_demo.py` | Genera `datos-demo.sql`. Solo hace falta si se cambian los hallazgos |

## Qué trae

| Ecosistema · departamento | Región | Jul | Ago | Sep | Oct | Nov | Especie | Octubre |
|---|---|---|---|---|---|---|---|---|
| Bosque húmedo · Cauca | Pacífico | 1 | 1 | 1 | 3 | 1 | Rana dorada (*Phyllobates terribilis*) | ALTA (3,0) |
| Laguna costera · La Guajira | Caribe | 1 | 1 | 1 | 2 | 2 | Flamenco americano (*Phoenicopterus ruber*) | ALTA (2,0) |
| Robledal · Santander | Andina | 0 | 0 | 2 | 1 | 2 | Reinita cerúlea (*Setophaga cerulea*) | ALTA (1,5) |
| Páramo · Boyacá | Andina | 1 | 1 | 1 | 1 | 1 | Azulejo común (*Thraupis episcopus*) | NORMAL (1,0) |
| Bosque seco · Córdoba | Caribe | 1 | 1 | 1 | 1 | 2 | Rana venenosa de franjas amarillas (*Dendrobates truncatus*) | NORMAL (1,0) |
| Sabana inundable · Casanare | Orinoquía | 1 | 1 | 1 | 1 | 1 | Azulejo común (*Thraupis episcopus*) | NORMAL (1,0) |
| Manglar · Nariño | Pacífico | 2 | 2 | 2 | 1 | 3 | Azulejo común (*Thraupis episcopus*) | BAJA (0,5) |
| Bosque de niebla · Risaralda | Andina | 2 | 2 | 1 | 1 | 2 | Gallito de roca andino (*Rupicola peruvianus*) | BAJA (0,6) |
| Selva amazónica · Amazonas | Amazonía | 1 | 1 | 1 | 0 | 1 | Azulejo común (*Thraupis episcopus*) | BAJA (0,0) |

- **Especies:** las 3 primeras del catálogo vienen con la migración de Registro; la rana de franjas amarillas, el gallito de roca y el flamenco los agrega `datos-demo.sql`, con los mismos tipos (Anfibio y Ave) y fichas. Sus fotos de referencia están en `portal/public/especies/`.
- **Índices de presión (HU-15):** el reporte automático de **octubre** sale con 3 zonas en **ALTA**, 3 en **NORMAL** y 3 en **BAJA** (última columna). Al generar **noviembre** a mano, Bosque húmedo sale **BAJA** (0,6), Páramo y Sabana inundable **NORMAL**, y el resto **ALTA**.
- **Historial (HU-12):** dos hallazgos tienen reclasificaciones en días distintos, así que reconstruir una fecha anterior muestra el antes y el después:
  - **Manglar, 14 de agosto:** registrado como reinita cerúlea y reclasificado el 3 de septiembre a azulejo común (grabaciones de canto). Reconstruir el **1 de septiembre** muestra la reinita.
  - **Páramo, 18 de septiembre:** tres versiones. Azulejo común, reinita cerúlea el 7 de octubre (fotografías) y otra vez azulejo común el 10 de noviembre (análisis genético LG-2026-114). Reconstruir el **20 de octubre** muestra la reinita.
- **Ubicación (HU-07):** cada hallazgo tiene coordenadas aproximadas de su zona. Alto rango las ve; los demás roles ven solo región y departamento.
- Todos los registró `investigador@biohub.local` y las reclasificaciones las hizo `cientifico@biohub.local`. Cada uno tiene su fila en la auditoría.

## Volver a empezar

`docker compose down -v` borra las bases; el siguiente `docker compose up` vuelve a cargar todo.
