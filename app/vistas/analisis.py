import math
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from app import estado, didactica as dd
from core import experimento, estadistica
from core.config import GRADO_MT19937

st.title("3. Análisis de Entropía y Aleatoriedad")
dd.paso(2, "Medir la aleatoriedad")
exp = estado.requerir("secuencias")
dd.objetivo("Aplicar a las claves de cada generador las mismas mediciones que se usan para evaluar generadores reales, "
            "y comparar los resultados lado a lado.")
if "estadistica" not in exp:
    experimento.analizar(exp)
est = exp["estadistica"]

st.subheader("Resumen comparativo")
METRICAS = [("Proporción de unos (ideal: 50 %)", lambda e: dd.pct(e["frecuencia_unos"], 2)),
            ("Entropía esperada (bits por bit)", lambda e: "1"),
            ("Entropía observada (bits por bit)", lambda e: dd.num(e["entropia_observada"], 8)),
            ("Diferencia (esperada − observada)", lambda e: dd.cientifico(e["entropia_diferencia"])),
            ("Entropía por byte (máximo 8)", lambda e: dd.num(e["entropia_byte"], 4)),
            ("Prueba Monobit", lambda e: f"{'Pasa' if e['aprueba_monobit'] else 'No pasa'} (p = {dd.pval(e['p_monobit'])})"),
            ("Prueba de rachas", lambda e: f"{'Pasa' if e['aprueba_runs'] else 'No pasa'} (p = {dd.pval(e['p_runs'])})"),
            ("Autocorrelación máxima (ideal: 0)", lambda e: dd.num(e["autocorrelacion_max"], 4)),
            ("Complejidad lineal (ideal: mitad de los bits)", lambda e: f"{dd.num(e['complejidad_lineal'])} de {dd.num(e['bits_analizados'])} "
                                                                       f"({'pasa' if e['aprueba_complejidad'] else 'no pasa'}, p = {dd.pval(e['p_complejidad'])})")]
st.dataframe(pd.DataFrame([{"Medición": nombre, **{dd.TITULO[g]: f(est[g]) for g in ("PRNG", "QRNG")}} for nombre, f in METRICAS]),
             hide_index=True, width="stretch")

# ---- Entropía
st.subheader("1. Entropía: ¿cuánta incertidumbre hay?")
ent = {g: estadistica.indicadores_por_clave(experimento.claves(exp, g))[:, 1] for g in ("PRNG", "QRNG")}
fig = go.Figure([go.Histogram(x=ent[g], name=dd.TITULO[g], marker_color=dd.COLOR[g], opacity=0.55, nbinsx=30, histnorm="percent") for g in ("PRNG", "QRNG")])
fig.add_vline(x=1.0, line_dash="dash", annotation_text="Esperada (1)")
fig.update_layout(barmode="overlay", title="Entropía de cada clave, por generador", xaxis_title="Entropía (bits por bit)",
                  yaxis_title="% de las claves", height=330, legend=dict(orientation="h", y=-0.3))
st.plotly_chart(fig, width="stretch")
dd.interpretacion(dd.interpretar_entropia(est) + "\n\n" + dd.interpretar_entropia_por_clave(ent["PRNG"], ent["QRNG"]))
dd.como_leer(dd.LEER_ENTROPIA, "Qué es la entropía y cómo leer este gráfico")

# ---- Pruebas NIST
st.subheader("2. Pruebas del NIST: ¿podría ser una moneda perfecta?")
dd.interpretacion(dd.interpretar_pruebas(est))
dd.como_leer(dd.LEER_PRUEBAS, "Qué miden Monobit y rachas, y qué es el p-valor")

# ---- Autocorrelación
st.subheader("3. Autocorrelación: ¿un bit anticipa a los siguientes?")
banda = dd.Z99 / math.sqrt(est["PRNG"]["n_bits"])
lags = list(range(1, len(est["PRNG"]["autocorrelacion"]) + 1))
fig = go.Figure([go.Scatter(x=lags + lags[::-1], y=[banda] * len(lags) + [-banda] * len(lags), fill="toself",
                            fillcolor="rgba(150,150,150,0.25)", line=dict(width=0), name="Rango del azar (99 %)", hoverinfo="skip")]
                + [go.Scatter(x=lags, y=e["autocorrelacion"], mode="lines+markers", name=dd.TITULO[g], line_color=dd.COLOR[g]) for g, e in est.items()])
fig.add_hline(y=0, line_color="gray")
tope = max(2.2 * banda, 1.3 * max(e["autocorrelacion_max"] for e in est.values()))
fig.update_yaxes(range=[-tope, tope])
fig.update_layout(title="Autocorrelación por desplazamiento", xaxis_title="Desplazamiento k (bits)", yaxis_title="Correlación",
                  height=340, legend=dict(orientation="h", y=-0.3))
st.plotly_chart(fig, width="stretch")
dd.interpretacion(dd.interpretar_autocorrelacion(est))
dd.como_leer(dd.LEER_AUTOCORRELACION)

# ---- Complejidad lineal
st.subheader("4. Complejidad lineal: ¿existe una regla que genere los bits?")
nb = est["PRNG"]["bits_analizados"]
fig = go.Figure([go.Bar(x=[dd.TITULO[g] for g in ("PRNG", "QRNG")], y=[est[g]["complejidad_lineal"] for g in ("PRNG", "QRNG")],
                        marker_color=[dd.COLOR[g] for g in ("PRNG", "QRNG")], text=[dd.num(est[g]["complejidad_lineal"]) for g in ("PRNG", "QRNG")],
                        textposition="outside", showlegend=False)])
fig.add_hline(y=nb / 2, line_dash="dash", annotation_text=f"Fuente ideal ({dd.num(nb // 2)})")
if nb / 2 > GRADO_MT19937:
    fig.add_hline(y=GRADO_MT19937, line_dash="dot", line_color="gray", annotation_text=f"Estado del MT19937 ({dd.num(GRADO_MT19937)})",
                  annotation_position="bottom right")
fig.update_layout(title=f"Complejidad lineal ({dd.num(nb)} bits analizados por generador)", yaxis_title="Complejidad lineal",
                  yaxis_range=[0, nb / 2 * 1.2], height=340)
st.plotly_chart(fig, width="stretch")
dd.interpretacion(dd.interpretar_complejidad(est))
dd.como_leer(dd.LEER_COMPLEJIDAD, "Qué es la complejidad lineal y por qué se necesitan 10.000 claves")

st.caption("Es esperable que ambos generadores aprueben las pruebas de primer orden (CU-06, flujo 4a). La complejidad lineal, en "
           "cambio, mide si existe una regla determinista. En el paso siguiente: ¿puede una IA distinguir las claves una por una?")
dd.siguiente("clasificacion", "Siguiente: 4. Clasificación con IA")
