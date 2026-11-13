"""M2 — Motor QRNG simulado (Hadamard + medición en Qiskit Aer, un solo lote)."""
import math
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from core.config import N_QUBITS

_SIMULADOR = AerSimulator()          # se crea una sola vez por proceso

def circuito_hadamard(n_qubits: int = N_QUBITS) -> QuantumCircuit:
    qc = QuantumCircuit(n_qubits, n_qubits)
    qc.h(range(n_qubits))
    qc.measure(range(n_qubits), range(n_qubits))
    return qc

def generar_bits_qrng(n_bits: int, n_qubits: int = N_QUBITS) -> np.ndarray:
    """Un único job: shots = ceil(n_bits / n_qubits); memory=True conserva el orden de los shots.
    No se fija seed_simulator: cada ejecución es un lote independiente (sección 7.4)."""
    shots = math.ceil(n_bits / n_qubits)
    resultado = _SIMULADOR.run(circuito_hadamard(n_qubits), shots=shots, memory=True).result()
    memoria = resultado.get_memory()                        # lista de 'shots' cadenas de n_qubits
    bits = np.frombuffer("".join(memoria).encode("ascii"), dtype=np.uint8) - ord("0")
    return bits[:n_bits].astype(np.uint8)
