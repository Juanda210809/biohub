# API externa de BioHub

La URL de entrada para consumidores es /externa/v1/hallazgos. Kong elimina /externa/v1 y envia la solicitud al servicio consulta, ruta /externa/hallazgos. Los consumidores conservan la URL publica si cambia la ubicacion interna de Consulta.

Enviar la credencial en el encabezado apikey. La configuracion del repo contiene exclusivamente una credencial de demostracion local. Los consumidores reales y sus claves deben provisionarse en el entorno de despliegue; no deben guardarse en Git.

    curl.exe -i -H "apikey: clave-demo-universidad" http://localhost:8000/externa/v1/hallazgos

- Sin clave o con clave invalida: 401.
- Hasta 60 solicitudes por minuto por consumidor: la peticion pasa a Consulta.
- Exceso de cuota: 429 en Kong, sin llegar a Consulta.
- Los encabezados X-RateLimit-Limit-Minute y X-RateLimit-Remaining-Minute informan la cuota.
- /api/v1/consulta/externa y sus subrutas: 403 para evitar saltarse autenticacion y cuota.
- /api/v1/identidad/interno y sus subrutas: 403 desde el gateway.

La politica local de cuota corresponde al despliegue actual de una instancia de Kong. Un despliegue con varias instancias requiere una politica de contadores compartidos y sus pruebas.

El contrato de datos corresponde a Consulta: la respuesta debe provenir del inventario publico y nunca incluir coordenadas exactas. El endpoint actual es un marcador pendiente de completar con su responsable.

Ver db/README.md para ejecutar las pruebas unitarias y de integracion y gateway/AVANCE-SCRUM-29.md para el estado de la entrega.
