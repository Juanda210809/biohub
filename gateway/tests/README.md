# Pruebas del API Gateway

Las pruebas unitarias verifican que la configuración declarativa conserve la ruta externa, la autenticación por consumidor, la cuota y el bloqueo del endpoint interno del PDP.

La integración levanta una instancia temporal de Kong con la configuración real y un upstream HTTP de prueba. Comprueba autenticación, reescritura de ruta, encabezados de cuota y rechazo 429 en la petición 61. Requiere Docker.

```powershell
python -m pip install -r gateway/requirements-test.txt
python -m pytest gateway/tests/test_kong_config.py -q
python -m pytest gateway/tests/test_kong_integration.py -q
```

La falta de Docker hace fallar la integracion; no se omite silenciosamente. Para probar tambien los 11 contenedores, la replicacion y los permisos SQL, ejecutar python -m pytest gateway/tests db/tests -q -W error. Ver db/README.md para el aislamiento de los datos de prueba.
