import numpy as np
import plotly.graph_objects as go
import streamlit as st
from app import estado, didactica as dd
from core import experimento, prng
from core.config import CANTIDADES_CLAVES, LONGITUDES_CLAVE

st.title("2. Laboratorio de Generación de Claves")
dd.paso(1, "Generar las claves")
dd.objetivo("Elegir cuántas claves generar y de qué longitud, y producirlas con los dos generadores **bajo los mismos "
            "parámetros**. Luego observará cómo se distribuyen sus valores.")

c1, c2, c3 = st.columns(3)
n_claves = c1.selectbox("Cantidad de claves por generador", CANTIDADES_CLAVES, index=1, format_func=lambda n: dd.num(n),
                        help="Más claves dan resultados más precisos, pero tardan más. Para empezar, 1.000 es un buen valor.")
longitud = c2.selectbox("Longitud de cada clave (bits)", LONGITUDES_CLAVE, index=len(LONGITUDES_CLAVE) - 1,
                        help="256 bits es la longitud habitual de una clave simétrica moderna (por ejemplo, AES-256).")
semilla_txt = c3.text_input("Semilla del PRNG: número o texto corto (opcional)", max_chars=prng.MAX_CARACTERES_SEMILLA,
                            placeholder="p. ej. 20260101 o gato azul",
                            help="Un número de 0 a 4294967295 o un texto de hasta 32 caracteres. Si su docente le asignó una, úsela.")
st.caption("No escriba nombres ni datos personales en la semilla. El texto solo sirve para elegir la semilla: "
           "no se cifra, no se analiza y no se guarda en el informe (el informe guarda el número que se obtiene de él).")

with st.expander("¿Qué es la semilla y por qué importa?", icon=":material/menu_book:"):
    st.markdown("""
El generador clásico es un algoritmo: la **semilla** es su punto de partida, y a partir de ella todo lo demás está determinado.

- **Número:** se usa tal cual.
- **Texto:** se normaliza (minúsculas, sin espacios repetidos) y se convierte en un número de 32 bits con **SHA-256**,
  una función *hash*: el mismo texto da siempre el mismo número, y textos parecidos dan números completamente distintos.
- **Vacío:** el simulador elige una semilla al azar y se la muestra.

**Pruebe esto:** genere dos veces con la misma semilla y compare la primera clave del PRNG. Será idéntica.
La del QRNG, en cambio, cambia siempre: su generador no tiene semilla.
""")

if st.button("Generar claves PRNG y QRNG", type="primary"):
    origen = "automatica"
    if semilla_txt.strip():
        try:
            semilla, origen = prng.interpretar_semilla(semilla_txt)
        except ValueError as e:
            st.error(str(e)); st.stop()
    else:
        semilla = prng.nueva_semilla()
    with st.spinner("Generando claves con ambos generadores…"):
        exp = experimento.generar(n_claves, longitud, semilla, origen != "automatica")
        exp["config"]["semilla_origen"] = origen
        exp["config"]["semilla_texto"] = prng.normalizar_texto(semilla_txt) if origen == "texto" else ""
        estado.guardar(exp)

exp = estado.obtener()
if exp:
    c = exp["config"]
    detalle = {"texto": f" (obtenida del texto «{c.get('semilla_texto', '')}»)",
               "automatica": " (generada automáticamente)"}.get(c.get("semilla_origen"), "")
    st.success(f"{dd.num(c['n_claves'])} claves de {c['longitud_clave']} bits por generador · "
               f"semilla del PRNG: {c['semilla']}{detalle}")

    st.subheader("Así se ve una clave")
    primera = experimento.claves(exp, "PRNG")[0]
    bits = "".join(map(str, primera[:64]))
    st.markdown("Primeros 64 bits de la primera clave del PRNG, en grupos de 8 (un byte por grupo):")
    st.code(" ".join(bits[i:i + 8] for i in range(0, 64, 8)))
    st.markdown("La misma información en **hexadecimal** (cada par de cifras es un byte): "
                f"`{np.packbits(primera[:64]).tobytes().hex()}`. Abajo, las primeras claves completas de cada generador.")

    cols = st.columns(2)
    for col, gen in zip(cols, ("PRNG", "QRNG")):
        with col:
            st.markdown(f"**Generador {dd.GEN[gen]}**")
            st.code("\n".join(np.packbits(k).tobytes().hex() for k in experimento.claves(exp, gen)[:3]) + "\n…")
            bytes_ = np.packbits(exp["secuencias"][gen])
            st.plotly_chart(go.Figure(go.Histogram(x=bytes_, xbins=dict(start=0, end=256, size=4), marker_color=dd.COLOR[gen]))
                            .update_layout(title="Histograma de valores por byte (0–255)", height=260, bargap=0.05,
                                           xaxis_title="Valor del byte", yaxis_title="Apariciones", margin=dict(t=40, b=20)),
                            width="stretch")
            mapa = np.bincount(bytes_, minlength=256).reshape(16, 16)
            etiquetas = [f"{i:x}" for i in range(16)]
            st.plotly_chart(go.Figure(go.Heatmap(z=mapa, x=etiquetas, y=etiquetas, colorscale="Blues",
                                                 hovertemplate="byte 0x%{y}%{x}: %{z} veces<extra></extra>"))
                            .update_layout(title="Mapa de frecuencia de bytes (16 × 16)", height=320,
                                           xaxis_title="Segunda cifra hexadecimal", yaxis_title="Primera cifra",
                                           xaxis_type="category", yaxis_type="category",
                                           yaxis_autorange="reversed", margin=dict(t=40, b=20)),
                            width="stretch")
            dd.interpretacion(dd.interpretar_bytes(bytes_, gen))
    dd.como_leer(dd.LEER_HISTOGRAMA, "Cómo leer el histograma y el mapa de frecuencia")
    dd.siguiente("analisis", "Siguiente: 3. Análisis de Entropía y Aleatoriedad")
