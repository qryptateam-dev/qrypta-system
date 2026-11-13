"""M1 — Motor PRNG clásico (Mersenne Twister MT19937)."""
import hashlib
import math
import random
import secrets
import unicodedata
import numpy as np

SEMILLA_MAX = 2**32 - 1
MAX_CARACTERES_SEMILLA = 32

def normalizar_texto(texto: str) -> str:
    """Quita espacios de los extremos y repetidos, y pasa a minúsculas: 'Gato  Azul ' -> 'gato azul'."""
    return " ".join(unicodedata.normalize("NFC", texto).split()).casefold()

def interpretar_semilla(entrada: str) -> tuple[int, str]:
    """Convierte lo que escribe el usuario en una semilla de 32 bits (CU-01).
    - Solo dígitos: se usa el número tal cual (0 a 4294967295).
    - Texto corto: primeros 4 bytes del SHA-256 del texto normalizado. El texto solo elige la semilla:
      no se cifra, no se analiza y no se guarda en el informe.
    Devuelve (semilla, "numero" | "texto")."""
    texto = normalizar_texto(entrada)
    if not texto:
        raise ValueError("La semilla está vacía.")
    if texto.isdigit():
        if int(texto) > SEMILLA_MAX:
            raise ValueError(f"El número debe estar entre 0 y {SEMILLA_MAX}.")
        return int(texto), "numero"
    if len(texto) > MAX_CARACTERES_SEMILLA:
        raise ValueError(f"El texto puede tener hasta {MAX_CARACTERES_SEMILLA} caracteres.")
    return int.from_bytes(hashlib.sha256(texto.encode("utf-8")).digest()[:4], "big"), "texto"

def nueva_semilla() -> int:
    """Semilla aleatoria para cuando el usuario no ingresa una (CU-01, flujo 4a)."""
    return secrets.randbelow(SEMILLA_MAX + 1)

def generar_bits_prng(n_bits: int, semilla: int) -> np.ndarray:
    """Devuelve n_bits (0/1, uint8) a partir de palabras completas de 32 bits de MT19937."""
    if not 0 <= semilla <= SEMILLA_MAX:
        raise ValueError("La semilla debe estar entre 0 y 4294967295")
    rng = random.Random(semilla)
    n_palabras = math.ceil(n_bits / 32)
    palabras = np.array([rng.getrandbits(32) for _ in range(n_palabras)], dtype=">u4")
    return np.unpackbits(palabras.view(np.uint8))[:n_bits]
