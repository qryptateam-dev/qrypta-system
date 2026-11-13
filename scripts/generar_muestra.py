"""Genera la muestra del estudio (Anteproyecto, apartados Unidad de Análisis, Población y Muestra y Análisis de los Datos): 30 repeticiones por cada volumen (100, 1.000 y
10.000 claves de 256 bits por generador) = 90 experimentos y 180 conjuntos de claves.
Se ejecuta en la computadora del equipo, NO en Cloud Run. Uso:
    python -m scripts.generar_muestra --repeticiones 30 --salida muestra
"""
import argparse
from pathlib import Path
import pandas as pd
from scipy.stats import binom
from core import experimento, informe
from core.config import CANTIDADES_CLAVES, LONGITUD_ESTUDIO

SEMILLA_BASE = 20260000          # semillas documentadas: SEMILLA_BASE + volumen + repetición
ALFA = 0.01                      # nivel de significancia de la prueba binomial de cada experimento
CONDICIONES = 12                 # 4 modelos × 3 volúmenes (corrección de Bonferroni)


def minimo_significativas(repeticiones: int, alfa: float = ALFA, condiciones: int = CONDICIONES) -> int:
    """Menor S tal que P(S' >= S) < alfa / condiciones, con S' ~ Binomial(repeticiones, alfa) bajo H0.
    Con 30 repeticiones devuelve 4 (P = 0,00022 < 0,00083)."""
    return next(s for s in range(repeticiones + 1) if binom.sf(s - 1, repeticiones, alfa) < alfa / condiciones)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeticiones", type=int, default=30)
    ap.add_argument("--volumenes", type=int, nargs="+", default=list(CANTIDADES_CLAVES))
    ap.add_argument("--salida", default="muestra")
    a = ap.parse_args()
    salida = Path(a.salida); salida.mkdir(exist_ok=True)
    filas = []
    for n_claves in a.volumenes:
        for rep in range(a.repeticiones):
            semilla = SEMILLA_BASE + n_claves + rep
            exp = experimento.ejecutar(n_claves, LONGITUD_ESTUDIO, semilla)
            (salida / f"exp_{n_claves}_{rep:02d}.csv").write_text(informe.exportar_csv(exp), encoding="utf-8")
            for modelo, m in exp["ml"]["resultados"].items():
                filas.append({"n_claves": n_claves, "repeticion": rep, "semilla_prng": semilla, "modelo": modelo,
                              "accuracy": m["accuracy"], "tasa_error": m["tasa_error"], "sensibilidad": m["sensibilidad"],
                              "especificidad": m["especificidad"], "p_valor_vs_azar": m["p_valor_vs_azar"],
                              "es_mejor_modelo": modelo == exp["ml"]["mejor_modelo"],
                              **{f"{g}_{k}": exp["estadistica"][g][k] for g in ("PRNG", "QRNG")
                                 for k in ("entropia_observada", "p_monobit", "p_runs", "autocorrelacion_max")}})
            print(f"{n_claves} claves · repetición {rep + 1}/{a.repeticiones} lista")
    df = pd.DataFrame(filas)
    df.to_csv(salida / "resultados_detalle.csv", index=False)
    resumen = (df.groupby(["n_claves", "modelo"])[["accuracy", "sensibilidad", "especificidad"]]
                 .agg(["mean", "std"]).round(4))
    resumen.to_csv(salida / "resumen_clasificacion.csv")
    print(resumen.to_string())
    # decisión por condición (modelo × volumen): S repeticiones significativas de las realizadas
    s_min = minimo_significativas(a.repeticiones)
    decision = (df.assign(sig=df.p_valor_vs_azar < ALFA).groupby(["n_claves", "modelo"])
                  .agg(repeticiones=("sig", "size"), significativas=("sig", "sum")))
    decision["distingue_las_fuentes"] = decision["significativas"] >= s_min
    decision.to_csv(salida / "decision_por_condicion.csv")
    print(f"\nDecisión por condición (se requieren al menos {s_min} repeticiones con p < {ALFA}):")
    print(decision.to_string())

if __name__ == "__main__":
    main()
