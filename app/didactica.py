"""Textos explicativos e interpretación automática de los resultados (vistas 1 a 6).
Las funciones que empiezan con 'interpretar_' son puras: reciben números y devuelven texto en Markdown,
de modo que se pueden probar sin Streamlit. Están redactadas para que los resultados se puedan interpretar
sin formación especializada en criptografía; el simulador es una herramienta experimental y su uso no se evalúa."""
import math
import numpy as np
import streamlit as st
from scipy.stats import chisquare
from core.config import ALFA, GRADO_MT19937

GEN = {"PRNG": "clásico (PRNG)", "QRNG": "cuántico simulado (QRNG)"}
COLOR = {"PRNG": "#2E6DB4", "QRNG": "#E8740C"}   # mismo color de cada generador en todos los gráficos
TITULO = {"PRNG": "Clásico (PRNG)", "QRNG": "Cuántico simulado (QRNG)"}
Z99 = 2.576                     # banda del 99 % para la autocorrelación (coherente con α = 0,01)

# ---------------------------------------------------------------- formato de números (es-PY)
def num(x: float, d: int = 0) -> str:
    """1234.5 -> '1.234,5'"""
    return f"{x:,.{d}f}".replace(",", "§").replace(".", ",").replace("§", ".")

def pct(x: float, d: int = 1) -> str:
    return f"{num(100 * x, d)} %"

SUP = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")

def cientifico(x: float) -> str:
    """0.00000026 -> '2,6 × 10⁻⁷' (para diferencias muy pequeñas)."""
    if x == 0:
        return "0"
    m, e = f"{x:.1e}".split("e")
    return f"{m.replace('.', ',')} × 10{str(int(e)).translate(SUP)}"

def pval(p: float) -> str:
    return "< 0,0001" if p < 1e-4 else num(p, 4)

# ---------------------------------------------------------------- componentes de interfaz
def paso(n: int, titulo: str) -> None:
    st.progress(n / 4, text=f"Paso {n} de 4 · {titulo}")

def objetivo(texto: str) -> None:
    st.markdown(f"**¿Qué va a hacer aquí?** {texto}")

def como_leer(texto: str, titulo: str = "Cómo leer este gráfico") -> None:
    with st.expander(titulo, icon=":material/menu_book:"):
        st.markdown(texto)

def interpretacion(texto: str) -> None:
    st.info(f"**Interpretación de sus resultados.** {texto}", icon=":material/insights:")

def siguiente(pagina: str, etiqueta: str) -> None:
    st.divider()
    st.page_link(f"vistas/{pagina}.py", label=etiqueta, icon=":material/arrow_forward:")

# ---------------------------------------------------------------- vista 2: histograma y mapa de frecuencia
def interpretar_bytes(bytes_: np.ndarray, generador: str) -> str:
    n = len(bytes_)
    grupos = np.bincount(bytes_ // 4, minlength=64)               # las 64 barras del histograma
    esperado = n / 64
    p = chisquare(grupos).pvalue
    celdas = np.bincount(bytes_, minlength=256)
    t = (f"Se analizaron {num(n)} bytes del generador {GEN[generador]}. Si todos los valores fueran igual de probables, "
         f"cada barra tendría unas {num(esperado)} apariciones; en sus datos van de {num(grupos.min())} a {num(grupos.max())}. "
         f"En el mapa, cada celda debería tener unas {num(n / 256, 1)} y van de {num(celdas.min())} a {num(celdas.max())}. ")
    if p >= ALFA:
        t += (f"La prueba χ² de uniformidad da p = {pval(p)} (≥ 0,01): esas diferencias son las que produce el azar; "
              "no hay valores preferidos.")
    else:
        t += (f"La prueba χ² de uniformidad da p = {pval(p)} (< 0,01): algunos valores aparecen más de lo que explicaría el azar. "
              "Ocurre en 1 de cada 100 fuentes perfectas; si se repite con otra semilla, sería una señal de sesgo.")
    if esperado < 50:
        t += " Con pocos datos las barras varían mucho; con 10.000 claves el histograma se ve casi plano."
    return t

LEER_HISTOGRAMA = """
- Cada clave se corta en **bytes** (grupos de 8 bits), y cada byte es un número entre 0 y 255.
- **Histograma:** cada barra agrupa 4 valores consecutivos (0–3, 4–7, …) y su altura es cuántas veces aparecieron.
  En una fuente aleatoria las barras tienen **alturas parecidas**: el histograma es aproximadamente plano.
- **Mapa de frecuencia:** los 256 valores en una cuadrícula de 16 × 16 (fila = primera cifra hexadecimal,
  columna = segunda). Un color uniforme, con manchas sueltas, es lo esperable. Una **fila, columna o diagonal**
  claramente más oscura indicaría un patrón.
- Las barras nunca son idénticas: el azar siempre produce pequeñas diferencias. La pregunta es si son
  **más grandes de lo que el azar explica**; eso es lo que responde la prueba χ².
"""

# ---------------------------------------------------------------- vista 3: entropía, pruebas NIST y autocorrelación
def entropia_de(p1: float) -> float:
    return -sum(p * math.log2(p) for p in (p1, 1 - p1) if p > 0)

def interpretar_entropia(est: dict) -> str:
    partes = []
    for g in ("PRNG", "QRNG"):
        e = est[g]
        partes.append(f"el generador {GEN[g]} obtuvo **{num(e['entropia_observada'], 8)}** bits por bit "
                      f"(diferencia con el ideal: {cientifico(e['entropia_diferencia'])}; {pct(e['frecuencia_unos'], 2)} de unos)")
    t = "Con todas las claves juntas, " + " y ".join(partes) + ". "
    peor = max(est[g]["entropia_diferencia"] for g in ("PRNG", "QRNG"))
    if peor < 1e-3:
        t += ("Ambas fuentes están prácticamente en el máximo posible: ceros y unos aparecen en proporciones casi iguales. "
              "Para comparar: una fuente con 55 % de unos tendría 0,9928, y una con 90 %, solo 0,4690. ")
    else:
        t += "Al menos una fuente se aleja del máximo: hay más ceros que unos, o al revés. "
    t += ("Una entropía alta es **necesaria pero no suficiente**: la secuencia 0101 0101… tiene entropía 1 y es totalmente "
          "predecible. Por eso se complementa con las pruebas siguientes.")
    return t

def interpretar_entropia_por_clave(ent_prng: np.ndarray, ent_qrng: np.ndarray) -> str:
    bordes = np.linspace(min(ent_prng.min(), ent_qrng.min()), 1, 31)
    h1 = np.histogram(ent_prng, bordes)[0] / len(ent_prng); h2 = np.histogram(ent_qrng, bordes)[0] / len(ent_qrng)
    solape = float(np.minimum(h1, h2).sum())
    return (f"La entropía media por clave es {num(ent_prng.mean(), 4)} en el PRNG y {num(ent_qrng.mean(), 4)} en el QRNG. "
            "Es menor que 1 porque una sola clave es una muestra pequeña: en 256 bits es raro obtener exactamente 128 unos. "
            f"Las dos distribuciones se superponen en un **{pct(solape, 0)}**. Este es un adelanto del paso 4: si las claves de "
            "ambos generadores se ven iguales a través de sus indicadores, un modelo de IA no tiene en qué apoyarse para distinguirlas.")

def interpretar_pruebas(est: dict) -> str:
    filas = []
    for g in ("PRNG", "QRNG"):
        e = est[g]
        estado = lambda ok: "pasa" if ok else "**no pasa**"
        filas.append(f"Generador {GEN[g]}: Monobit p = {pval(e['p_monobit'])} ({estado(e['aprueba_monobit'])}); "
                     f"rachas p = {pval(e['p_runs'])} ({estado(e['aprueba_runs'])}).")
    fallas = [g for g in ("PRNG", "QRNG") if not (est[g]["aprueba_monobit"] and est[g]["aprueba_runs"])]
    if not fallas:
        cierre = ("Ambos generadores pasan: ninguna de las dos pruebas encuentra desequilibrios ni repeticiones anómalas. "
                  "Es el resultado esperable; el Mersenne Twister fue diseñado para superar pruebas de este tipo.")
    else:
        cierre = (f"No pasa: {' y '.join(GEN[g] for g in fallas)}. Antes de concluir, repita con otra semilla: una fuente perfecta "
                  "también falla 1 de cada 100 veces con α = 0,01. Si falla de forma sistemática, hay un patrón real.")
    return " ".join(filas) + " " + cierre

def interpretar_autocorrelacion(est: dict) -> str:
    n = est["PRNG"]["n_bits"]; banda = Z99 / math.sqrt(n)
    t = f"Con {num(n)} bits, la banda gris va de −{num(banda, 4)} a +{num(banda, 4)}. "
    fuera = {g: [k + 1 for k, a in enumerate(est[g]["autocorrelacion"]) if abs(a) > banda] for g in ("PRNG", "QRNG")}
    for g in ("PRNG", "QRNG"):
        t += (f"Generador {GEN[g]}: valor más alejado de cero {num(est[g]['autocorrelacion_max'], 4)}; "
              + ("todos los desplazamientos quedan dentro de la banda. " if not fuera[g] else
                 f"fuera de la banda en el desplazamiento {', '.join(map(str, fuera[g]))}. "))
    if not any(fuera.values()):
        t += "Conocer un bit no ayuda a adivinar los siguientes: los bits se comportan como independientes."
    else:
        t += ("Que 1 de 16 puntos quede apenas fuera puede ocurrir por azar (se esperan 0,16 por generador). "
              "Varios puntos lejos de la banda, o el mismo desplazamiento en distintas corridas, indicarían dependencia.")
    return t

def interpretar_complejidad(est: dict) -> str:
    n = est["PRNG"]["bits_analizados"]
    cl = {g: est[g]["complejidad_lineal"] for g in ("PRNG", "QRNG")}
    t = (f"Se analizaron {num(n)} bits de cada generador (1 de cada 32). Una fuente ideal tendría una complejidad lineal "
         f"cercana a la mitad, **{num(n // 2)}**. El generador {GEN['PRNG']} obtuvo **{num(cl['PRNG'])}** "
         f"(p = {pval(est['PRNG']['p_complejidad'])}) y el {GEN['QRNG']}, **{num(cl['QRNG'])}** "
         f"(p = {pval(est['QRNG']['p_complejidad'])}). ")
    if not est["PRNG"]["alcanza_grado_mt"]:
        return t + (f"Con esta cantidad de claves, los dos quedan en la mitad: el Mersenne Twister puede tener una complejidad de hasta "
                    f"{num(GRADO_MT19937)}, y para revelarla hacen falta al menos el doble de bits ({num(2 * GRADO_MT19937)}). "
                    "**Repita el experimento con 10.000 claves de 256 bits** para ver la diferencia.")
    if not est["PRNG"]["aprueba_complejidad"] and est["QRNG"]["aprueba_complejidad"]:
        return t + (f"La diferencia es clara: por más bits que se analicen, el PRNG nunca supera {num(GRADO_MT19937)}, el tamaño de su "
                    "estado interno. Sus bits siguen una regla lineal fija, algo esperable en un algoritmo determinista. "
                    "El QRNG simulado, en cambio, se comporta como una fuente ideal: ninguna regla lineal más corta que la mitad de "
                    "la secuencia la reproduce. **Esta es la diferencia que las pruebas anteriores y la IA por clave no ven.** "
                    "No es un defecto del Mersenne Twister para su uso habitual (simulación); explica por qué no se usa para generar claves.")
    if est["PRNG"]["aprueba_complejidad"] and est["QRNG"]["aprueba_complejidad"]:
        return t + "Ningún generador muestra estructura lineal en esta corrida."
    return t + "Al menos un generador muestra estructura lineal (p < 0,01)."

LEER_COMPLEJIDAD = f"""
La **complejidad lineal** responde: **¿cuál es la regla lineal más corta capaz de generar esta secuencia?**
Una regla lineal calcula cada bit combinando (con XOR) algunos de los bits anteriores. La complejidad es cuántos bits
anteriores necesita esa regla. Se calcula con el algoritmo de **Berlekamp-Massey**, el mismo de la prueba 2.10 del NIST SP 800-22.

- **Fuente ideal:** la regla más corta necesita la **mitad** de la secuencia. No hay atajo: los bits no siguen ninguna regla.
- **Algoritmo determinista lineal:** la complejidad se detiene en el tamaño de su estado, por más bits que se analicen.
  El Mersenne Twister tiene un estado de {num(GRADO_MT19937)} bits efectivos.

Se analiza **1 de cada 32 bits** porque el MT19937 entrega palabras de 32 bits; se aplica exactamente el mismo
procedimiento a los dos generadores. Para que una estructura de grado {num(GRADO_MT19937)} se revele hacen falta al menos
{num(2 * GRADO_MT19937)} bits analizados, es decir, unas 5.000 claves de 256 bits: por eso se ve con **10.000 claves**.

El p-valor es la probabilidad de que una fuente ideal tenga una complejidad igual o menor que la observada.
Medir la complejidad lineal **no** reconstruye ni predice ninguna clave: solo mide si existe una regla lineal corta.
"""

LEER_ENTROPIA = r"""
La **entropía de Shannon** mide cuánta incertidumbre tiene una fuente. Para bits, si $p$ es la proporción de unos:

$$H = -p\log_2 p - (1-p)\log_2(1-p)$$

| Proporción de unos | 50 % | 55 % | 70 % | 90 % | 100 % |
|---|---|---|---|---|---|
| Entropía $H$ (bits por bit) | 1,0000 | 0,9928 | 0,8813 | 0,4690 | 0 |

- **Esperada:** 1 bit por bit, el máximo, el de una moneda perfecta.
- **Observada:** la que se calcula con sus datos.
- **Diferencia:** cuánto falta para el ideal. Valores del orden de 0,000001 son normales.

El gráfico muestra la entropía **de cada clave por separado**. Cada curva es la distribución de esos valores en un generador:
si las curvas se superponen, las claves de ambos generadores tienen el mismo aspecto.
"""

LEER_PRUEBAS = """
Las pruebas del NIST (SP 800-22) responden una pregunta: **¿esta secuencia podría haber salido de una moneda perfecta?**

- **Monobit:** ¿hay aproximadamente la misma cantidad de ceros que de unos?
- **Rachas (Runs):** una racha es un bloque de bits iguales seguidos (en 0011101 hay 4: 00, 111, 0, 1).
  Muy pocas rachas indican bits "pegajosos"; demasiadas, bits que alternan en exceso.

El **p-valor** es la probabilidad de ver un desvío al menos así de grande si la fuente fuera perfecta.
Si p ≥ 0,01 la secuencia **pasa**: no hay evidencia de un problema. Si p < 0,01 **no pasa**.
Pasar una prueba no demuestra que la fuente sea aleatoria; solo que esa prueba no encontró un defecto.
"""

LEER_AUTOCORRELACION = """
La **autocorrelación** compara la secuencia consigo misma desplazada *k* bits: ¿el bit *i* se parece al bit *i + k*?

- Cerca de **0:** no hay relación (lo esperable).
- Cerca de **+1:** los bits tienden a repetirse cada *k* posiciones. Cerca de **−1:** tienden a alternar.

La **banda gris** marca el rango que el azar produce en el 99 % de los casos para esta cantidad de bits.
Puntos dentro de la banda: los bits se comportan como independientes.
"""

# ---------------------------------------------------------------- vista 4: clasificación y serie por volumen
def interpretar_clasificacion(ml: dict) -> str:
    res, mejor = ml["resultados"], ml["mejor_modelo"]; n = ml["n_prueba"]
    m = res[mejor]; acc = m["accuracy"]
    sig = [k for k, v in res.items() if v["p_valor_vs_azar"] < ALFA]
    (vn, fp), (fn, vp) = m["matriz_confusion"]
    t = (f"Los modelos se evaluaron con {num(n)} claves que no vieron al entrenar ({num(n // 2)} de cada generador). "
         f"El mejor fue **{mejor}**, que acertó el origen de {num(vp + vn)} claves: {pct(acc)}. ")
    if sig:
        t += (f"Superan al azar con p < 0,01: {', '.join(sig)}. Esos modelos encontraron alguna característica estadística que "
              "diferencia a los generadores. Antes de concluir, repita el experimento: un resultado real se mantiene con otras semillas.")
    else:
        t += (f"Ningún modelo supera al azar (todos con p ≥ 0,01). Que el mejor llegue a {pct(acc)} y no a 50,0 % exacto es normal: "
              f"con {num(n)} claves de prueba, adivinando al azar también se obtienen valores así. "
              "**Conclusión:** con estos indicadores, las claves de ambos generadores son indistinguibles. Es un resultado válido: "
              "responde la pregunta del experimento. Los indicadores describen cada clave por separado; la estructura del "
              "Mersenne Twister abarca miles de bits y solo aparece al analizar la secuencia completa (complejidad lineal, paso 3).")
    sesgados = [k for k, v in res.items() if abs(v["sensibilidad"] - v["especificidad"]) > 0.3]
    if sesgados:
        t += (f" Observe {', '.join(sesgados)}: su sensibilidad y especificidad son muy distintas porque tiende a responder casi "
              "siempre lo mismo. Su precisión igual queda cerca del 50 %: no está distinguiendo, solo prefiere una respuesta.")
    return t

def interpretar_serie(filas: list[dict]) -> str:
    vols = sorted({f["n_claves"] for f in filas})
    desv = {v: max(abs(f["accuracy"] - 0.5) for f in filas if f["n_claves"] == v) for v in vols}
    media = {v: np.mean([f["accuracy"] for f in filas if f["n_claves"] == v]) for v in vols}
    sig = sorted({f["n_claves"] for f in filas if f["p_valor_vs_azar"] < ALFA})
    t = "Precisión media de los cuatro modelos: " + "; ".join(f"{num(v)} claves → {pct(media[v])}" for v in vols) + ". "
    t += (f"Con {num(vols[0])} claves los modelos se alejan del 50 % hasta {num(100 * desv[vols[0]], 1)} puntos; "
          f"con {num(vols[-1])}, solo hasta {num(100 * desv[vols[-1]], 1)}. ")
    if media[vols[-1]] - media[vols[0]] > 0.05 and sig:
        t += ("La precisión **sube** al aumentar los datos: es lo que ocurre cuando existe un patrón real que los modelos aprenden "
              "mejor con más ejemplos.")
    else:
        t += ("La precisión **no sube** con más datos; lo que cambia es que las líneas se juntan alrededor del 50 %, porque con más "
              "claves la medición es más precisa. Si hubiera un patrón, más datos lo harían más visible: aquí no aparece.")
    return t

LEER_CLASIFICACION = """
Cada modelo responde, para cada clave de prueba, **«vino del PRNG» o «vino del QRNG»**. Luego se compara con la verdad:

| Métrica | Qué mide | Valor que indicaría que distingue |
|---|---|---|
| **Precisión (accuracy)** | Proporción total de aciertos | Claramente mayor que 50 % |
| **Tasa de error** | Proporción de errores (1 − precisión) | Claramente menor que 50 % |
| **Sensibilidad** | De las claves PRNG, cuántas reconoció como PRNG | Alta **junto con** especificidad alta |
| **Especificidad** | De las claves QRNG, cuántas reconoció como QRNG | Alta **junto con** sensibilidad alta |
| **p-valor vs. azar** | Probabilidad de acertar tanto lanzando una moneda | Menor que 0,01 |

Una precisión del 50 % es exactamente lo que se obtiene **adivinando**, porque hay la misma cantidad de claves de cada generador.
"""

LEER_SERIE = """
El experimento se repite con **100, 1.000 y 10.000 claves** por generador, con la misma semilla y la misma longitud.
El eje horizontal es logarítmico (cada marca multiplica los datos por 10); la línea punteada es el azar.

- Si hay un patrón, las líneas **suben** a medida que hay más datos.
- Si no lo hay, las líneas **se acercan al 50 %**: con pocos datos los resultados "saltan" más por azar.
"""

LEER_MATRIZ = """
La **matriz de confusión** cruza la respuesta del modelo (columnas) con el origen real de la clave (filas):

| | Predijo QRNG | Predijo PRNG |
|---|---|---|
| **Era QRNG** | Verdadero negativo (VN): acierto | Falso positivo (FP): error |
| **Era PRNG** | Falso negativo (FN): error | Verdadero positivo (VP): acierto |

Los aciertos están en la **diagonal**. Si el modelo adivina, las cuatro celdas tienen cantidades parecidas.
"""

def interpretar_matriz(nombre: str, m: dict) -> str:
    (vn, fp), (fn, vp) = m["matriz_confusion"]
    t = (f"{nombre}: de {num(vp + fn)} claves PRNG reconoció {num(vp)} (sensibilidad {pct(m['sensibilidad'])}); "
         f"de {num(vn + fp)} claves QRNG reconoció {num(vn)} (especificidad {pct(m['especificidad'])}). "
         f"La diagonal suma {num(vp + vn)} aciertos y la otra, {num(fp + fn)} errores. ")
    if m["p_valor_vs_azar"] < ALFA:
        return t + (f"Son más aciertos de los que explica el azar (p = {pval(m['p_valor_vs_azar'])}): "
                    "el modelo encontró una diferencia entre los generadores.")
    return t + (f"Esa diferencia puede aparecer adivinando (p = {pval(m['p_valor_vs_azar'])}): "
                "en la práctica, el modelo no distingue los generadores.")
