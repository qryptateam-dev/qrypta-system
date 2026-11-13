import pandas as pd
import plotly.express as px
import streamlit as st
from app import estado, didactica as dd
from core import experimento, estadistica

AVISO = ("La clasificación mide si un modelo detecta diferencias estadísticas entre los generadores. "
         "Detectar un patrón no equivale a romper una clave ni constituye un ataque criptográfico.")

st.title("4. Clasificación con IA")
dd.paso(3, "¿Puede una IA distinguir los generadores?")
exp = estado.requerir("secuencias")
c = exp["config"]
dd.objetivo("Entrenar cuatro modelos de aprendizaje automático para que, viendo una clave, digan de qué generador salió. "
            "Si lo logran claramente mejor que adivinando, existe una diferencia detectable entre los generadores.")
st.info(AVISO, icon=":material/shield:")

with st.expander("Cómo funciona el experimento, paso a paso", icon=":material/menu_book:"):
    st.markdown(f"""
1. **Indicadores.** Cada clave se resume en 12 números: proporción de unos, entropía, cantidad de rachas, racha más larga
   y autocorrelación en 8 desplazamientos. Es lo único que ve el modelo; no conoce la semilla ni el generador.
2. **Etiqueta.** Cada clave lleva su origen real: 1 = PRNG, 0 = QRNG.
3. **Partición 70/30.** De las {dd.num(2 * c['n_claves'])} claves, el 70 % se usa para entrenar y el 30 % para evaluar.
   Ambas partes tienen la misma cantidad de claves de cada generador.
4. **Cuatro modelos:**
   - **Árbol de Decisión:** una serie de preguntas del tipo «¿la racha más larga es mayor que 9?».
   - **Random Forest:** 100 árboles que votan.
   - **SVM con kernel lineal:** busca un plano que separe las dos clases.
   - **Red Neuronal (MLP):** dos capas de neuronas (32 y 16) que combinan los indicadores.
5. **Evaluación.** Se mide cuántas claves de prueba clasificó bien cada modelo.
""")

st.subheader("Así ve la IA cada clave")
muestra = pd.concat([pd.DataFrame(estadistica.indicadores_por_clave(experimento.claves(exp, g)[:3]),
                                  columns=estadistica.NOMBRES_INDICADORES).assign(origen=g) for g in ("PRNG", "QRNG")])
NOMBRES = {"frecuencia_unos": "Prop. de unos", "entropia": "Entropía", "cantidad_rachas": "Rachas", "racha_maxima": "Racha más larga",
           **{f"autocorrelacion_lag{k}": f"Autocorr. k={k}" for k in range(1, 9)}}
st.dataframe(muestra.rename(columns=NOMBRES).set_index("origen").round(3), width="stretch")
st.caption("Tres claves de cada generador. ¿Ve alguna columna que permita separarlas a simple vista?")

if st.button("Entrenar y comparar los 4 modelos", type="primary"):
    with st.spinner("Entrenando…"):
        experimento.clasificar(exp)
    st.session_state.pop("exportacion", None)

if "ml" in exp:
    r = exp["ml"]
    filas = [{"Modelo": n, "Precisión": dd.pct(m["accuracy"]), "Tasa de error": dd.pct(m["tasa_error"]),
              "Sensibilidad": dd.pct(m["sensibilidad"]), "Especificidad": dd.pct(m["especificidad"]),
              "p-valor": dd.pval(m["p_valor_vs_azar"]),
              "¿Supera al azar?": "Sí" if m["p_valor_vs_azar"] < dd.ALFA else "No"} for n, m in r["resultados"].items()]
    st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")
    dd.interpretacion(dd.interpretar_clasificacion(r))
    dd.como_leer(dd.LEER_CLASIFICACION, "Qué significa cada métrica")

st.header("Experimento controlado por volumen de datos")
st.write("¿Cambiaría el resultado con más datos? Repita el experimento con 100, 1.000 y 10.000 claves, la misma semilla "
         "y la misma longitud. Tarda unos segundos.")
if st.button("Ejecutar serie por volumen"):
    with st.spinner("Ejecutando los tres experimentos…"):
        st.session_state["serie"] = experimento.serie_por_volumen(c["longitud_clave"], c["semilla"])
if "serie" in st.session_state:
    df = pd.DataFrame(st.session_state["serie"])
    fig = px.line(df, x="n_claves", y="accuracy", color="modelo", markers=True, log_x=True, range_y=[0, 1],
                  labels={"n_claves": "Claves por generador", "accuracy": "Precisión (accuracy)", "modelo": "Modelo"})
    fig.add_hline(y=0.5, line_dash="dash", annotation_text="Azar (50 %)")
    fig.update_layout(legend=dict(orientation="h", y=-0.3), yaxis_tickformat=".0%")
    fig.update_xaxes(tickvals=[100, 1000, 10000], ticktext=["100", "1.000", "10.000"])
    st.plotly_chart(fig, width="stretch")
    dd.interpretacion(dd.interpretar_serie(st.session_state["serie"]))
    dd.como_leer(dd.LEER_SERIE)
    with st.expander("Ver los datos de la serie"):
        st.dataframe(pd.DataFrame([{"Claves por generador": dd.num(f["n_claves"]), "Modelo": f["modelo"],
                                    "Precisión": dd.pct(f["accuracy"]), "Sensibilidad": dd.pct(f["sensibilidad"]),
                                    "Especificidad": dd.pct(f["especificidad"]), "p-valor": dd.pval(f["p_valor_vs_azar"])}
                                   for f in st.session_state["serie"]]), hide_index=True, width="stretch")

if "ml" in exp:
    dd.siguiente("dashboard", "Siguiente: 5. Dashboard e Informe")
