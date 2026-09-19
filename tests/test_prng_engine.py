import random
from core.prng_engine import generar_secuencia_prng, cifrar_xor

def test_es_mersenne_twister():
    estado = random.Random().getstate()
    assert estado[0] == 3
    assert len(estado[1]) == 625     # 624 palabras + índice = estado de MT19937

def test_reproducibilidad_semilla():
    assert generar_secuencia_prng(50, seed=1) == generar_secuencia_prng(50, seed=1)

def test_longitud_y_valores_binarios():
    bits = generar_secuencia_prng(1000, seed=42)
    assert len(bits) == 1000 and set(bits) <= {0, 1}

def test_xor_es_involutivo():
    msg = b"HOLA"
    clave = bytes([7, 12, 200, 3])
    assert cifrar_xor(cifrar_xor(msg, clave), clave) == msg