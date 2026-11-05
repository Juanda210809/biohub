## Historia

SCRUM-__ · HU-__ · (nombre de la historia)

## Qué cambia

- 

## Cómo probarlo

1. `docker compose up --build`
2. 

## Definición de terminado

- [ ] Cumple todos los criterios de aceptación de la historia en Jira
- [ ] Tiene pruebas automáticas y pasan (`python -m pytest` o `npm run lint && npm run build`)
- [ ] Las rutas nuevas aparecen en `/docs` del servicio
- [ ] Funciona con todo el sistema levantado (`docker compose up`)
- [ ] No sube el archivo `.env` ni contraseñas
- [ ] Si cambié una ruta que otros usan, avisé en el grupo
