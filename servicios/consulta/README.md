# Servicio Consulta Pública

**Dueño:** Luna
**Historias del MVP:** HU-05 Consultar ficha pública · HU-06 Ver región o departamento · HU-13 API externa · HU-20 Caché

| Qué | Dónde |
|---|---|
| Arranque de la app | `app/main.py` |
| Rutas (endpoints) | `app/api/` |
| Reglas del negocio | `app/dominio/` |
| Acceso a la base | `app/repositorio/` y `app/db.py` |
| Preguntar permisos al PDP | `app/autorizacion.py` |
| Caché de la ficha pública (patrón Decorator) | `app/dominio/servicio_fichas.py` |
| Pruebas | `tests/` |

Este servicio **no crea tablas**: solo lee la copia de `hallazgo_publico`
que llega por replicación a la BD Consulta. Su usuario de base es de solo lectura.


## Listado de hallazgos para el portal

`GET /api/v1/consulta/hallazgos?limite=50&desplazamiento=0` (por Kong). Sirve para escoger un
hallazgo y abrir su ficha (`GET /hallazgos/{id}`). Pasa por el PDP con `ver_ficha_publica`, así
que lo puede usar el visitante sin sesión; si llega un token Bearer se le pasa al PDP.

- Respuesta: `{ hallazgos: [{ hallazgo_id, especie, region, departamento, ecosistema,
  fecha_hallazgo, atributos_publicos, version, actualizado_en }], limite, desplazamiento, cantidad }`,
  del más reciente al más antiguo. Es la misma consulta y lista blanca de la API externa (HU-13):
  nunca trae coordenadas.
- `limite` de 1 a 100 (por defecto 50) y `desplazamiento` desde 0; fuera de rango responde 422.


## Caché de la ficha pública: patrón Decorator (HU-20, Entrega 2 · 6.2)

`GET /hallazgos/{id}` primero le pregunta al PDP (`ver_ficha_publica`) y luego pide la ficha a una
`IConsulta`, sin saber si la respuesta sale de Redis o de la base:

- `ConsultaBD`: el componente concreto, lee `hallazgo_publico` de la BD Consulta.
- `ConsultaCacheada`: el decorador; envuelve otra `IConsulta` y pone Redis delante (clave
  `ficha_publica:{id}`, 300 s). Si Redis falla, responde desde la base.
- `armar_consulta(sesion)` arma la cadena `ConsultaCacheada(ConsultaBD(sesion))`.

La caché solo guarda la ficha pública, que no tiene coordenadas (RNF-05). Pruebas en
`tests/test_consulta_cacheada.py`.
