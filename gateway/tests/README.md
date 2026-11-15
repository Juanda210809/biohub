# Pruebas de HU-14

Con Docker activo, desde la raiz:

    python -m pip install -r gateway/requirements-test.txt ruff
    python -m pytest gateway/tests -q -W error
    ruff check gateway/tests

Cinco pruebas unitarias de configuracion y cuatro de integracion con Kong real y
upstream simulado. Ver gateway/HU-14.md para alcance y limitaciones.
