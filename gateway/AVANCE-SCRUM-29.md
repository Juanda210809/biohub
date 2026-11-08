# Avance de SCRUM-29 y SCRUM-30

Rama: feature/SCRUM-29-api-externa.

## Completado y verificado

- Kong: ruta externa estable, API key, cuota de 60 solicitudes/minuto por consumidor y bloqueo del PDP interno.
- Bloqueo del acceso alternativo /api/v1/consulta/externa (incluida la variante codificada).
- Bases de datos publicadas solo en 127.0.0.1 para clientes SQL locales.
- Pruebas del sistema completo con 11 contenedores, conexiones de los cinco servicios, Redis y portal.
- Replicacion de un hallazgo publico desde operacional hacia Consulta y Reportes; lectura permitida y escritura rechazada para svc_consulta.
- CI ejecuta pruebas del gateway y del sistema completo. La ausencia de Docker produce un fallo explicito.
- Prueba de cuota ajustada para empezar lejos del cambio de minuto.

## Validacion local

12 pruebas aprobadas: 6 unitarias de configuracion y 6 de integracion. Ruff aprobado.
Ultima ejecucion: python -m pytest gateway/tests db/tests -q -W error; sin advertencias ni omisiones.
La regresion del acceso alternativo fue reproducida antes de corregirla (200 en lugar de 403).
Las pruebas usan proyectos, puertos y volumenes temporales; no usan el archivo .env personal.

## Pendiente

1. Integrar con Luna el inventario real de /externa/hallazgos. Actualmente responde un mensaje de ejemplo.
2. Probar el contrato y la ausencia de coordenadas exactas sobre ese inventario real.
3. Revisar el PR y la ejecucion de CI del ultimo commit antes de fusionar.
4. Para despliegue: definir dominio/TLS y provisionar claves reales. Si hay varias instancias de Kong, usar contadores compartidos.

HU-13 y HU-14 no se consideran cerradas. El acceso local a las bases no equivale a segmentar las redes internas de Docker.
Consultar git status, el historial de la rama y el PR para comprobar que avance esta publicado.

## Ejecutar

Con Docker activo, desde la raiz:

    python -m pip install -r gateway/requirements-test.txt ruff
    python -m pytest gateway/tests db/tests -q -W error
    ruff check gateway/tests db/tests

Detalles de infraestructura en db/README.md y del contrato externo en gateway/README.md.
