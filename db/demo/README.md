# Datos de demostración

Al levantar el sistema (`docker compose up`), el servicio `datos-demo` carga **22 hallazgos de julio a noviembre de 2026** para que la demo muestre todas las historias con datos que tienen sentido. Corre una sola vez y termina; si los datos ya estaban, no duplica nada.

| Archivo | Qué es |
|---|---|
| `datos-demo.sql` | Los hallazgos: coordenadas, versiones, auditoría y su copia pública |
| `cargar-datos-demo.sh` | Espera a que Registro y Gobernanza creen sus tablas, carga el SQL y espera la copia en BD Reportes |
| `generar_datos_demo.py` | Genera `datos-demo.sql`. Solo hace falta si se cambian los hallazgos |

## Qué trae

| Ecosistema · departamento | Jul | Ago | Sep | Oct | Nov | Especie |
|---|---|---|---|---|---|---|
| Bosque húmedo · Cauca | 1 | 1 | 1 | 3 | 1 | Rana dorada (*Phyllobates terribilis*) |
| Páramo · Boyacá | 1 | 1 | 1 | 1 | 1 | Azulejo común (*Thraupis episcopus*) |
| Manglar · Nariño | 2 | 2 | 2 | 1 | 3 | Azulejo común (*Thraupis episcopus*) |

- **Índices de presión (HU-15):** el reporte automático de **octubre** sale con Bosque húmedo **ALTA** (3,0), Páramo **NORMAL** (1,0) y Manglar **BAJA** (0,5). Al generar **noviembre** a mano, Manglar sale **ALTA** (1,8), Páramo **NORMAL** y Bosque húmedo **BAJA** (0,6).
- **Historial (HU-12):** dos hallazgos tienen reclasificaciones en días distintos, así que reconstruir una fecha anterior muestra el antes y el después:
  - **Manglar, 14 de agosto:** registrado como reinita cerúlea y reclasificado el 3 de septiembre a azulejo común (grabaciones de canto). Reconstruir el **1 de septiembre** muestra la reinita.
  - **Páramo, 18 de septiembre:** tres versiones. Azulejo común, reinita cerúlea el 7 de octubre (fotografías) y otra vez azulejo común el 10 de noviembre (análisis genético LG-2026-114). Reconstruir el **20 de octubre** muestra la reinita.
- **Ubicación (HU-07):** cada hallazgo tiene coordenadas aproximadas de su zona. Alto rango las ve; los demás roles ven solo región y departamento.
- Todos los registró `investigador@biohub.local` y las reclasificaciones las hizo `cientifico@biohub.local`. Cada uno tiene su fila en la auditoría.

## Volver a empezar

`docker compose down -v` borra las bases; el siguiente `docker compose up` vuelve a cargar todo.
