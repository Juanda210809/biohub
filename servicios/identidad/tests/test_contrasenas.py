from app.dominio.contrasenas import hashear, verificar


def test_no_guarda_la_contrasena_en_texto_plano():
    hash_guardado = hashear("mi-clave", rondas=4)
    assert "mi-clave" not in hash_guardado
    assert hash_guardado.startswith("$2b$")


def test_verifica_la_contrasena_correcta():
    assert verificar("mi-clave", hashear("mi-clave", rondas=4)) is True


def test_rechaza_la_contrasena_incorrecta():
    assert verificar("otra-clave", hashear("mi-clave", rondas=4)) is False


def test_un_hash_danado_cuenta_como_incorrecta():
    assert verificar("mi-clave", "esto-no-es-un-hash") is False
