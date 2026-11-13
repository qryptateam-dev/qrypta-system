import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from app import estado, didactica as dd
from core import informe

st.title("5. Dashboard e Informe")
dd.paso(4, "Reunir los resultados y comunicarlos")
exp = estado.requerir("secuencias", "estadistica", "ml")
dd.objetivo("Ver en un solo lugar lo que mostró cada etapa, leer la conclusión del experimento y exportar un informe "
            "que cualquiera pueda verificar.")
est, r = exp["estadistica"], exp["ml"]
res, mejor = r["resultados"], r["mejor_modelo"]

st.subheader("Comparación entre generadores")
fila = lambda nombre, f: {"Métrica": nombre, "Generador clásico (PRNG)": f(est["PRNG"]), "Generador cuántico simulado (QRNG)": f(est["QRNG"])}
tabla = [fila("Entropía observada (esperada: 1)", lambda e: dd.num(e["entropia_observada"], 8)),
         fila("Frecuencia 0 / 1", lambda e: f"{dd.pct(1 - e['frecuencia_unos'], 2)} / {dd.pct(e['frecuencia_unos'], 2)}"),
         fila("Autocorrelación máxima (16 desplazamientos)", lambda e: dd.num(e["autocorrelacion_max"], 4)),
         fila("Patrones detectados (Monobit / rachas)", lambda e: "Ninguno" if e["aprueba_monobit"] and e["aprueba_runs"] else "Sí"),
         {"Métrica": f"Clasificación por IA ({mejor})", "Generador clásico (PRNG)": f"{dd.pct(res[mejor]['sensibilidad'])} reconocidas",
          "Generador cuántico simulado (QRNG)": f"{dd.pct(res[mejor]['especificidad'])} reconocidas"}]
st.dataframe(pd.DataFrame(tabla), hide_index=True, width="stretch")
iguales = all(est[g]["aprueba_monobit"] and est[g]["aprueba_runs"] for g in ("PRNG", "QRNG"))
dd.interpretacion(("En las mediciones estadísticas, las dos columnas son prácticamente iguales: ambos generadores "
                   "tienen entropía casi máxima, equilibrio entre ceros y unos y bits independientes. " if iguales else
                   "Al menos un generador no pasó alguna prueba estadística; revise el paso 3 y repita con otra semilla. ")
                  + f"En la última fila, el mejor modelo ({mejor}) reconoció {dd.pct(res[mejor]['sensibilidad'])} de las claves PRNG "
                  f"y {dd.pct(res[mejor]['especificidad'])} de las QRNG; adivinando se esperaría 50 % en cada una.")

nombres = list(res)
fig = go.Figure([go.Bar(name=etq, x=nombres, y=[res[n][campo] for n in nombres])
                 for campo, etq in (("accuracy", "Precisión (accuracy)"), ("sensibilidad", "Sensibilidad"), ("especificidad", "Especificidad"))])
fig.add_hline(y=0.5, line_dash="dash", annotation_text="Azar (50 %)")
fig.update_layout(barmode="group", title="Capacidad de clasificación por modelo", yaxis_range=[0, 1], height=360,
                  yaxis_tickformat=".0%", legend=dict(orientation="h", y=-0.2))
st.plotly_chart(fig, width="stretch")
dd.interpretacion(dd.interpretar_clasificacion(r))
dd.como_leer("Cada modelo tiene tres barras: precisión (aciertos totales), sensibilidad (aciertos en claves PRNG) y "
             "especificidad (aciertos en claves QRNG). La línea punteada es lo que se obtiene adivinando. "
             "Un modelo que distingue los generadores tendría sus **tres** barras claramente por encima de la línea; "
             "si una sube y otra baja, el modelo solo prefiere una respuesta.")

modelo = st.selectbox("Matriz de confusión del modelo", nombres, index=nombres.index(mejor))
m = res[modelo]["matriz_confusion"]
st.plotly_chart(go.Figure(go.Heatmap(z=m, x=["Predicho QRNG", "Predicho PRNG"], y=["Real QRNG", "Real PRNG"], text=m,
                texttemplate="%{text}", colorscale="Blues", showscale=False)).update_layout(height=300, yaxis_autorange="reversed"),
                width="stretch")
dd.interpretacion(dd.interpretar_matriz(modelo, res[modelo]))
dd.como_leer(dd.LEER_MATRIZ, "Cómo leer la matriz de confusión")

st.subheader("Conclusión experimental")
with st.container(border=True):
    st.write(informe.conclusion(exp))
st.caption("La conclusión se redacta automáticamente con reglas fijas a partir de los p-valores; es la misma que lleva el informe.")

st.header("Exportar informe verificable")
st.caption("Cada exportación genera un código distinto. Entregue el CSV: el PDF es solo una copia de lectura.")
with st.expander("¿Cómo funciona el código de verificación?", icon=":material/menu_book:"):
    st.markdown("""
El código tiene la forma `QRY1-<número aleatorio>-<fecha>-<huella>-<firma>`:

- **Número aleatorio (128 bits):** hace que cada exportación sea única, aunque se exporte dos veces el mismo experimento.
- **Huella:** un resumen SHA-256 del contenido del CSV. Si se cambia un solo carácter, la huella deja de coincidir.
- **Firma (HMAC-SHA256):** se calcula con una clave secreta que solo conoce el servidor. Sin ella nadie puede fabricar
  un código válido.

El simulador **no guarda** los informes: verifica recalculando la firma. Por eso no necesita base de datos.
""")
if st.button("Preparar exportación", type="primary"):
    try:
        csv_texto = informe.exportar_csv(exp)
    except RuntimeError:
        st.error("El servicio no tiene configurada la clave de verificación; no se puede emitir el informe."); st.stop()
    codigo = csv_texto.splitlines()[0].split(",", 1)[1]
    st.session_state["exportacion"] = {"csv": csv_texto.encode("utf-8"), "pdf": informe.exportar_pdf(exp, codigo), "codigo": codigo}
exp_ = st.session_state.get("exportacion")
if exp_:
    ident = exp_["codigo"].split("-")[1][:8]
    st.success(f"ID de exportación: {ident}")
    st.code(exp_["codigo"])
    c1, c2 = st.columns(2)
    c1.download_button("Descargar CSV (verificable)", exp_["csv"], file_name=f"QRYPTA_{ident}.csv", mime="text/csv")
    c2.download_button("Descargar PDF (lectura)", exp_["pdf"], file_name=f"QRYPTA_{ident}.pdf", mime="application/pdf")
    st.markdown("**¿Y ahora?** Entregue el CSV tal como se descargó. Puede comprobar que es válido en la vista 6, y volver al "
                "Laboratorio para repetir el experimento con otra semilla, otra cantidad de claves u otra longitud: "
                "comparar varias corridas es la mejor forma de distinguir un resultado real de una casualidad.")
    st.page_link("vistas/verificar.py", label="Comprobar el informe: 6. Verificar Informe", icon=":material/verified:")
