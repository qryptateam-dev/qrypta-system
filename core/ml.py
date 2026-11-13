"""M4 — Clasificación del origen de cada clave (PRNG o QRNG) con cuatro modelos de Scikit-Learn."""
import time
import numpy as np
from scipy.stats import binomtest
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier
from core.config import PROPORCION_PRUEBA, SEMILLA_MODELOS, ETIQUETA_PRNG, ETIQUETA_QRNG
from core.estadistica import indicadores_por_clave

# Parámetros fijos de los modelos y de la partición: se registran en cada informe (objetivo e).
PARTICION = f"{int((1 - PROPORCION_PRUEBA) * 100)}/{int(PROPORCION_PRUEBA * 100)} estratificada por clave; random_state={SEMILLA_MODELOS}"
PARAMETROS = {
    "Árbol de Decisión": f"max_depth=8; random_state={SEMILLA_MODELOS}",
    "Random Forest": f"n_estimators=100; max_depth=8; random_state={SEMILLA_MODELOS}",
    "SVM (kernel lineal)": f"StandardScaler + LinearSVC(C=1.0; max_iter=5000); random_state={SEMILLA_MODELOS}",
    "Red Neuronal (MLP)": f"StandardScaler + MLPClassifier(hidden_layer_sizes=(32, 16); max_iter=300; early_stopping=True); random_state={SEMILLA_MODELOS}",
}

def crear_modelos() -> dict:
    s = SEMILLA_MODELOS
    return {
        "Árbol de Decisión": DecisionTreeClassifier(max_depth=8, random_state=s),
        "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=8, n_jobs=1, random_state=s),
        "SVM (kernel lineal)": make_pipeline(StandardScaler(), LinearSVC(C=1.0, max_iter=5000, random_state=s)),
        "Red Neuronal (MLP)": make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=(32, 16), max_iter=300,
                                                                            early_stopping=True, random_state=s)),
    }

def construir_dataset(claves_prng: np.ndarray, claves_qrng: np.ndarray):
    """Una fila por clave: sus indicadores estadísticos. Etiqueta: 1 = PRNG, 0 = QRNG."""
    X = np.vstack([indicadores_por_clave(claves_prng), indicadores_por_clave(claves_qrng)])
    y = np.concatenate([np.full(len(claves_prng), ETIQUETA_PRNG), np.full(len(claves_qrng), ETIQUETA_QRNG)])
    return X, y

def entrenar_y_evaluar(claves_prng: np.ndarray, claves_qrng: np.ndarray) -> dict:
    X, y = construir_dataset(claves_prng, claves_qrng)
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=PROPORCION_PRUEBA, stratify=y, random_state=SEMILLA_MODELOS)
    resultados = {}
    for nombre, modelo in crear_modelos().items():
        t0 = time.perf_counter()
        modelo.fit(X_tr, y_tr)
        pred = modelo.predict(X_te)
        # matriz con el orden [QRNG, PRNG]: vn, fp / fn, vp   (positivo = PRNG)
        vn, fp, fn, vp = confusion_matrix(y_te, pred, labels=[ETIQUETA_QRNG, ETIQUETA_PRNG]).ravel()
        accuracy = (vp + vn) / len(y_te)
        resultados[nombre] = {
            "accuracy": float(accuracy),                       # «precisión (accuracy)» en los documentos
            "tasa_error": float(1 - accuracy),
            "sensibilidad": float(vp / (vp + fn)),             # claves PRNG reconocidas como PRNG
            "especificidad": float(vn / (vn + fp)),            # claves QRNG reconocidas como QRNG
            "matriz_confusion": [[int(vn), int(fp)], [int(fn), int(vp)]],
            "p_valor_vs_azar": float(binomtest(int(vp + vn), len(y_te), 0.5, alternative="greater").pvalue),
            "segundos": time.perf_counter() - t0,
        }
    mejor = max(resultados, key=lambda n: resultados[n]["accuracy"])
    return {"resultados": resultados, "mejor_modelo": mejor, "n_entrenamiento": len(y_tr), "n_prueba": len(y_te)}
