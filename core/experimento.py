"""M5 — Experimentos controlados y reproducibles: mismos parámetros para ambos generadores."""
import numpy as np
from core import prng, qrng, estadistica, ml
from core.config import CANTIDADES_CLAVES, LONGITUDES_CLAVE, N_QUBITS

def generar(n_claves: int, longitud: int, semilla: int, semilla_asignada: bool = True) -> dict:
    """Genera n_claves de 'longitud' bits con cada generador (CU-01 a CU-03)."""
    if longitud not in LONGITUDES_CLAVE:
        raise ValueError(f"La longitud debe ser una de {LONGITUDES_CLAVE}")
    n_bits = n_claves * longitud
    return {"config": {"n_claves": n_claves, "longitud_clave": longitud, "n_qubits": N_QUBITS,
                       "semilla": semilla, "semilla_asignada": semilla_asignada},
            "secuencias": {"PRNG": prng.generar_bits_prng(n_bits, semilla),
                           "QRNG": qrng.generar_bits_qrng(n_bits)}}

def claves(exp: dict, generador: str) -> np.ndarray:
    """Vista de la secuencia como matriz (n_claves, longitud)."""
    c = exp["config"]
    return exp["secuencias"][generador].reshape(c["n_claves"], c["longitud_clave"])

def analizar(exp: dict) -> dict:
    exp["estadistica"] = {g: estadistica.analizar(b) for g, b in exp["secuencias"].items()}
    return exp

def clasificar(exp: dict) -> dict:
    exp["ml"] = ml.entrenar_y_evaluar(claves(exp, "PRNG"), claves(exp, "QRNG"))
    return exp

def ejecutar(n_claves: int, longitud: int, semilla: int) -> dict:
    """Experimento completo: generación, evaluación estadística y clasificación."""
    return clasificar(analizar(generar(n_claves, longitud, semilla)))

def serie_por_volumen(longitud: int, semilla: int, volumenes=CANTIDADES_CLAVES) -> list[dict]:
    """Repite el experimento con 100, 1.000 y 10.000 claves y la misma semilla (CU-18)."""
    filas = []
    for n in volumenes:
        r = ejecutar(n, longitud, semilla)["ml"]
        for modelo, m in r["resultados"].items():
            filas.append({"n_claves": n, "modelo": modelo, "accuracy": m["accuracy"], "sensibilidad": m["sensibilidad"],
                          "especificidad": m["especificidad"], "p_valor_vs_azar": m["p_valor_vs_azar"]})
    return filas
