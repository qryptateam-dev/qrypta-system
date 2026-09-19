import random
 
def generar_secuencia_prng(cantidad_bits: int, seed: int | None = None) -> list[int]:
    rng = random.Random(seed)
    return [rng.getrandbits(1) for _ in range(cantidad_bits)]

def cifrar_xor(mensaje: bytes, clave: bytes) -> bytes:
    return bytes(m ^ k for m, k in zip(mensaje, clave))
