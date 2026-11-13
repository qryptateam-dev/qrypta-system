"""M3 — Entropía de Shannon, frecuencia, autocorrelación y pruebas NIST SP 800-22 (Monobit y Runs).
Incluye los indicadores por clave que usan los modelos de clasificación (M4)."""
import math
import numpy as np
from core.config import LAGS_AUTOCORRELACION, LAGS_POR_CLAVE, ALFA

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
