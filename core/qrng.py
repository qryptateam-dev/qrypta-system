"""M2 — Motor QRNG simulado: modelo de fuente cuántica ideal.

1. Qiskit calcula el estado del circuito (Hadamard sobre cada qubit) y sus probabilidades de medición.
2. Cada medición se sortea con el generador criptográfico del sistema operativo (módulo secrets),
   que se alimenta de entropía física de la máquina.

No se usa el muestreo de Qiskit Aer: Aer sortea las mediciones con un Mersenne Twister interno
(mt19937_64), de modo que su salida tiene la misma estructura lineal que el PRNG clásico
(complejidad lineal 19.937). Tampoco Statevector.sample_memory, que usa el PRNG de NumPy (PCG64).
"""
import math
import secrets
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from core.config import N_QUBITS

MUESTREO = "Statevector de Qiskit + secrets (CSPRNG del sistema operativo)"   # se registra en el informe


def circuito_hadamard(n_qubits: int = N_QUBITS) -> QuantumCircuit:
    qc = QuantumCircuit(n_qubits)
    qc.h(range(n_qubits))
    return qc


def probabilidades(qc: QuantumCircuit) -> np.ndarray:
    """Probabilidad de cada resultado de medir todos los qubits (índice = resultado como entero, convención de Qiskit)."""
    return Statevector(qc).probabilities()


def uniformes(n: int) -> np.ndarray:
    """n números uniformes en [0, 1) con 53 bits de precisión, tomados de secrets (sin semilla, irrepetibles)."""
    x = np.frombuffer(secrets.token_bytes(8 * n), dtype=np.uint64)
    return (x >> np.uint64(11)).astype(np.float64) * 2.0 ** -53


def muestrear(probs: np.ndarray, shots: int) -> np.ndarray:
    """Sortea 'shots' resultados según 'probs' (método de la transformada inversa)."""
    acumulada = np.cumsum(probs)
    acumulada /= acumulada[-1]
    return np.minimum(np.searchsorted(acumulada, uniformes(shots), side="right"), len(probs) - 1)


def generar_bits_circuito(qc: QuantumCircuit, n_bits: int) -> np.ndarray:
    """Mide el circuito las veces necesarias y devuelve n_bits (0/1, uint8), en el orden de las cadenas de Qiskit
    (qubit de mayor índice a la izquierda)."""
    n_qubits = qc.num_qubits
    shots = math.ceil(n_bits / n_qubits)
    resultados = muestrear(probabilidades(qc), shots)
    bits = (resultados[:, None] >> np.arange(n_qubits - 1, -1, -1)) & 1
    return bits.astype(np.uint8).ravel()[:n_bits]


def generar_bits_qrng(n_bits: int, n_qubits: int = N_QUBITS) -> np.ndarray:
    """shots = ceil(n_bits / n_qubits). Sin semilla: cada ejecución es un lote independiente e irrepetible (sección 7.4)."""
    return generar_bits_circuito(circuito_hadamard(n_qubits), n_bits)
