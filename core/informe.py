"""M6 — Informe del experimento: conclusión automática, CSV verificable (formato 1) y PDF de lectura."""
import io
import os
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")                       # sin interfaz gráfica (contenedor)
import matplotlib.pyplot as plt
from fpdf import FPDF
from core import ml, verificacion
from core.config import ALFA

# Fuente TTF con acentos y «—»: la del contenedor (paquete fonts-dejavu-core) o, al probar localmente,
# la de Windows o macOS. QRYPTA_FUENTE_PDF permite indicar otra ruta.
_FUENTES = [os.environ.get("QRYPTA_FUENTE_PDF", ""),
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/Library/Fonts/Arial Unicode.ttf"]
FUENTE = next((f for f in _FUENTES if f and Path(f).is_file()), _FUENTES[1])

def conclusion(exp: dict) -> str:
    """Conclusión experimental generada con reglas fijas a partir de los resultados (sin servicios externos)."""
    c, r = exp["config"], exp["ml"]
    est = exp["estadistica"]
    pasan = {g: est[g]["aprueba_monobit"] and est[g]["aprueba_runs"] for g in ("PRNG", "QRNG")}
    if all(pasan.values()):
        t1 = "Ambos generadores superaron las pruebas Monobit y de rachas (p ≥ 0,01)."
    else:
        fallan = " y ".join(g for g, ok in pasan.items() if not ok)
        t1 = f"No superó alguna de las pruebas Monobit o de rachas: {fallan}."
    n_txt = f"{c['n_claves']:,}".replace(",", ".")
    significativos = [n for n, m in r["resultados"].items() if m["p_valor_vs_azar"] < ALFA]
    mejor = r["mejor_modelo"]; acc = r["resultados"][mejor]["accuracy"] * 100
    if significativos:
        t2 = (f"Con {n_txt} claves de {c['longitud_clave']} bits por generador, clasificaron el origen por encima "
              f"del azar (p < 0,01): {', '.join(significativos)}.")
    else:
        t2 = (f"Con {n_txt} claves de {c['longitud_clave']} bits por generador, ningún modelo clasificó el origen "
              f"por encima del azar (p ≥ 0,01).")
    acc_txt = f"{acc:.1f}".replace(".", ",")
    t3 = f"Mejor modelo: {mejor}, con {acc_txt} % de precisión (accuracy)."
    t4 = "Detectar una diferencia estadística no equivale a romper una clave ni constituye un ataque criptográfico."
    return " ".join([t1, t2, t3, t4])

def filas_experimento(exp: dict) -> list[tuple[str, str, str]]:
    """Convierte el experimento en filas (seccion, campo, valor). El orden es fijo: define la huella."""
    f = [("config", "longitud_clave", str(exp["config"]["longitud_clave"])),
         ("config", "n_qubits", str(exp["config"]["n_qubits"])),
         ("modelos", "particion", ml.PARTICION)]
    f += [("modelos", f"{nombre}_parametros", ml.PARAMETROS[nombre]) for nombre in exp["ml"]["resultados"]]
    for gen in ("PRNG", "QRNG"):
        e = exp["estadistica"][gen]
        for campo in ("frecuencia_unos", "entropia_esperada", "entropia_observada", "entropia_diferencia",
                      "entropia_byte", "autocorrelacion_max", "p_monobit", "p_runs"):
            f.append(("estadistica", f"{gen}_{campo}", f"{e[campo]:.6f}"))
    for nombre, m in exp["ml"]["resultados"].items():
        for campo in ("accuracy", "tasa_error", "sensibilidad", "especificidad", "p_valor_vs_azar"):
            f.append(("clasificacion", f"{nombre}_{campo}", f"{m[campo]:.6f}"))
        f.append(("clasificacion", f"{nombre}_matriz_confusion", str(m["matriz_confusion"])))
    f.append(("clasificacion", "mejor_modelo", exp["ml"]["mejor_modelo"]))
    f.append(("conclusion", "texto", conclusion(exp)))
    for gen in ("PRNG", "QRNG"):
        f.append(("secuencia", f"{gen}_hex", np.packbits(exp["secuencias"][gen]).tobytes().hex()))
    return f

def exportar_csv(exp: dict) -> str:
    """Cada llamada genera un código nuevo (CU-11). La semilla y la cantidad de claves van en la sección config."""
    return verificacion.construir_csv(exp["config"]["semilla"], exp["config"]["n_claves"], filas_experimento(exp))

def _grafico_clasificacion(exp: dict) -> bytes:
    res = exp["ml"]["resultados"]; nombres = list(res)
    x = np.arange(len(nombres))
    fig, ax = plt.subplots(figsize=(7, 3), dpi=150)
    for i, (campo, etiqueta) in enumerate((("accuracy", "Precisión (accuracy)"), ("sensibilidad", "Sensibilidad"), ("especificidad", "Especificidad"))):
        ax.bar(x + (i - 1) * 0.26, [res[n][campo] for n in nombres], 0.26, label=etiqueta)
    ax.axhline(0.5, ls="--", lw=1, color="gray"); ax.set_xticks(x, nombres, fontsize=7)
    ax.set_ylim(0, 1); ax.legend(fontsize=7, ncol=3); fig.tight_layout()
    buf = io.BytesIO(); fig.savefig(buf, format="png"); plt.close(fig)
    return buf.getvalue()

def exportar_pdf(exp: dict, codigo: str) -> bytes:
    """Copia de lectura: muestra el mismo código que el CSV, pero no es verificable (RN-005)."""
    c = exp["config"]
    pdf = FPDF(); pdf.add_page()
    pdf.add_font("DejaVu", "", FUENTE); pdf.set_font("DejaVu", size=15)
    pdf.cell(0, 10, "Informe del experimento — Simulador QRYPTA", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", size=9)
    pdf.multi_cell(0, 5, f"Código de verificación: {codigo}\nCopia de lectura. Para verificar el informe use el archivo CSV.",
                   new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2); pdf.set_font("DejaVu", size=10)
    pdf.multi_cell(0, 6, f"Configuración: {c['n_claves']} claves de {c['longitud_clave']} bits por generador · semilla PRNG {c['semilla']}",
                   new_x="LMARGIN", new_y="NEXT")
    for gen in ("PRNG", "QRNG"):
        e = exp["estadistica"][gen]
        pdf.multi_cell(0, 6, f"{gen}: entropía observada {e['entropia_observada']:.5f} (esperada 1, diferencia {e['entropia_diferencia']:.5f}) · "
                             f"Monobit p={e['p_monobit']:.4f} · Rachas p={e['p_runs']:.4f}", new_x="LMARGIN", new_y="NEXT")
    pdf.image(io.BytesIO(_grafico_clasificacion(exp)), w=180)
    pdf.ln(2); pdf.set_font("DejaVu", size=11)
    pdf.cell(0, 7, "Conclusión experimental", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", size=10)
    pdf.multi_cell(0, 6, conclusion(exp), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
