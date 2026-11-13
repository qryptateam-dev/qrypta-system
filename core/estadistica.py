"""M3 — Entropía de Shannon, frecuencia, autocorrelación, pruebas NIST SP 800-22 (Monobit y Runs) y complejidad lineal
(algoritmo de Berlekamp-Massey). Incluye los indicadores por clave que usan los modelos de clasificación (M4)."""
import math
import numpy as np
from core.config import LAGS_AUTOCORRELACION, LAGS_POR_CLAVE, ALFA, DECIMACION_COMPLEJIDAD, GRADO_MT19937

ENTROPIA_ESPERADA = 1.0     # bits de entropía por bit en una fuente ideal

def entropia_shannon(bits: np.ndarray) -> float:
    """Entropía observada por bit (máximo 1,0)."""
    p1 = float(np.mean(bits)); p0 = 1 - p1
    return -sum(p * math.log2(p) for p in (p0, p1) if p > 0)

def entropia_por_byte(bits: np.ndarray) -> float:
    """Entropía de bloques de 8 bits (máximo 8,0)."""
    n = len(bits) // 8 * 8
    valores = np.packbits(bits[:n])
    frec = np.bincount(valores, minlength=256) / len(valores)
    frec = frec[frec > 0]
    return float(-(frec * np.log2(frec)).sum())

def monobit(bits: np.ndarray) -> float:
    """NIST SP 800-22, 2.1 — p-valor = erfc(|S_n| / sqrt(2n))."""
    n = len(bits)
    s = 2 * int(np.sum(bits, dtype=np.int64)) - n      # int64: evita desbordamiento con uint8
    return math.erfc(abs(s) / math.sqrt(2 * n))

def runs(bits: np.ndarray) -> float:
    """NIST SP 800-22, 2.3 (rachas) — incluye la prueba previa de frecuencia (tau = 2/sqrt(n))."""
    n = len(bits)
    pi = float(np.mean(bits))
    if abs(pi - 0.5) >= 2 / math.sqrt(n):
        return 0.0
    v_obs = 1 + int(np.count_nonzero(bits[1:] != bits[:-1]))
    num = abs(v_obs - 2 * n * pi * (1 - pi))
    den = 2 * math.sqrt(2 * n) * pi * (1 - pi)
    return math.erfc(num / den)

def autocorrelacion(bits: np.ndarray, max_lag: int = LAGS_AUTOCORRELACION) -> list[float]:
    """Correlación de Pearson entre la secuencia (±1) y sí misma desplazada 1..max_lag bits."""
    x = 2 * bits.astype(np.float64) - 1
    x = x - x.mean()
    den = float(np.dot(x, x))
    return [float(np.dot(x[:-k], x[k:]) / den) for k in range(1, max_lag + 1)]

def berlekamp_massey(bits: np.ndarray) -> int:
    """Complejidad lineal: longitud del LFSR más corto que genera la secuencia (Massey, 1969).
    Es el algoritmo de la prueba 2.10 del NIST SP 800-22, aplicado aquí a la secuencia completa."""
    s = np.asarray(bits, dtype=np.uint8)
    n = len(s)
    r = s[::-1].copy()                                     # r[n-i : n-i+L] = s[i-1], s[i-2], …, s[i-L]
    c = np.zeros(n + 1, np.uint8); b = np.zeros(n + 1, np.uint8)
    c[0] = b[0] = 1
    L, m, grado_b = 0, 1, 0
    for i in range(n):
        d = int(s[i])
        if L:
            d ^= np.count_nonzero(c[1:L + 1] & r[n - i:n - i + L]) & 1
        if not d:
            m += 1
            continue
        if 2 * L <= i:
            t = c[:L + 1].copy(); grado_t = L
            c[m:m + grado_b + 1] ^= b[:grado_b + 1]
            b[:grado_b + 1] = 0; b[:grado_t + 1] = t; grado_b = grado_t
            L, m = i + 1 - L, 1
        else:
            c[m:m + grado_b + 1] ^= b[:grado_b + 1]
            m += 1
    return L

def p_complejidad_lineal(L: int, n: int) -> float:
    """P(complejidad ≤ L) para n bits de una fuente ideal. Cantidad exacta de secuencias con complejidad l
    (Rueppel, 1986): 1 si l = 0 y 2^min(2n−2l, 2l−1) si l ≥ 1. Prueba unilateral: una complejidad baja indica estructura."""
    h = n // 2
    if L < 0:
        return 0.0
    if L <= h:
        total = 1 + 2 * (4 ** L - 1) // 3
    else:
        total = 1 + 2 * (4 ** h - 1) // 3 + (4 ** (n - h) - 4 ** (n - min(L, n))) // 3
    exponente = math.log2(total) - n
    return 0.0 if exponente < -1074 else min(1.0, 2.0 ** exponente)

def complejidad_lineal(bits: np.ndarray, decimacion: int = DECIMACION_COMPLEJIDAD) -> dict:
    """Complejidad lineal de la subsecuencia formada por 1 de cada 'decimacion' bits (el primero de cada bloque).
    Con 32 se toma un bit por palabra de 32 bits; el mismo procedimiento se aplica a ambos generadores."""
    sub = bits[::decimacion]
    n = len(sub)
    L = berlekamp_massey(sub)
    p = p_complejidad_lineal(L, n)
    return {"bits_analizados": n, "complejidad_lineal": L, "complejidad_esperada": n / 2,
            "p_complejidad": p, "aprueba_complejidad": p >= ALFA,
            "alcanza_grado_mt": n >= 2 * GRADO_MT19937}   # con menos bits, una estructura de grado 19.937 no se revela

def analizar(bits: np.ndarray) -> dict:
    """Evaluación integrada de una secuencia completa (todas las claves de un generador)."""
    p_mono, p_runs = monobit(bits), runs(bits)
    observada = entropia_shannon(bits)
    auto = autocorrelacion(bits)
    return {
        "n_bits": int(len(bits)),
        "frecuencia_unos": float(np.mean(bits)),
        "entropia_esperada": ENTROPIA_ESPERADA,
        "entropia_observada": observada,
        "entropia_diferencia": ENTROPIA_ESPERADA - observada,
        "entropia_byte": entropia_por_byte(bits),
        "p_monobit": p_mono, "aprueba_monobit": p_mono >= ALFA,
        "p_runs": p_runs, "aprueba_runs": p_runs >= ALFA,
        "autocorrelacion": auto,
        "autocorrelacion_max": float(max(abs(a) for a in auto)),
        **complejidad_lineal(bits),
    }

NOMBRES_INDICADORES = (["frecuencia_unos", "entropia", "cantidad_rachas", "racha_maxima"]
                       + [f"autocorrelacion_lag{k}" for k in range(1, LAGS_POR_CLAVE + 1)])

def indicadores_por_clave(claves: np.ndarray) -> np.ndarray:
    """claves: matriz (n_claves, longitud) de 0/1. Devuelve (n_claves, 12) con NOMBRES_INDICADORES."""
    c = claves.astype(np.int8)
    p1 = c.mean(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        ent = -(np.where(p1 > 0, p1 * np.log2(p1), 0.0) + np.where(p1 < 1, (1 - p1) * np.log2(1 - p1), 0.0))
    iguales = c[:, 1:] == c[:, :-1]
    rachas = 1 + (~iguales).sum(axis=1)
    actual = np.ones(len(c), dtype=np.int32); maxima = actual.copy()
    for j in range(iguales.shape[1]):                       # racha más larga de bits iguales
        actual = np.where(iguales[:, j], actual + 1, 1)
        maxima = np.maximum(maxima, actual)
    x = 2.0 * c - 1
    auto = [(x[:, :-k] * x[:, k:]).mean(axis=1) for k in range(1, LAGS_POR_CLAVE + 1)]
    return np.column_stack([p1, ent, rachas, maxima, *auto])
