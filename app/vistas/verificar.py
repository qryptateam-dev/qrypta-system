from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo
import io
import pandas as pd
import streamlit as st
from core import prng, verificacion

ZONA = ZoneInfo("America/Asuncion")
st.title("6. Verificar Informe")
st.caption("Página pública: no requiere cuenta. Los archivos se procesan en memoria y se descartan.")
st.markdown("Compruebe si un informe fue **emitido realmente por QRYPTA** y si su contenido **no fue modificado** después de "
            "exportarse. Sirve para revisar un informe propio, uno recibido o, en el caso de un docente, todas las entregas de un curso.")
individual, lote = st.tabs(["Individual (CU-12)", "En lote (CU-17)"])

with individual:
    codigo = st.text_input("Código de verificación", placeholder="QRY1-…")
    archivo = st.file_uploader("CSV del informe (opcional, para comprobar la integridad)", type=["csv"], key="csv_individual")
    if st.button("Verificar", key="btn_individual") and codigo:
        contenido = None
        if archivo is not None:
            _, contenido, _ = verificacion.leer_csv(archivo.getvalue().decode("utf-8", errors="replace"))
        r = verificacion.verificar_codigo(codigo, contenido)
        if not r["valido"]:
            st.error(f"NO VÁLIDO: {r['motivo']}")
        else:
            emitido = datetime.strptime(r["emitido_utc"], "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).astimezone(ZONA)
            st.success(f"VÁLIDO · emitido el {emitido:%d/%m/%Y %H:%M} (hora de Paraguay) · ID {r['id_exportacion']}")
            if "integro" in r:
                (st.success if r["integro"] else st.error)("El CSV es íntegro." if r["integro"] else "El CSV fue modificado después de exportarse.")

with lote:
    archivos = st.file_uploader(f"Entregas en CSV (máx. {verificacion.MAX_ARCHIVOS_LOTE})", type=["csv"], accept_multiple_files=True, key="csv_lote")
    semillas = st.file_uploader("Semillas asignadas (CSV: semilla,identificador) — opcional", type=["csv"], key="semillas")
    st.caption("Cada línea: la semilla asignada (número o texto corto, como la escribió el alumno) y un identificador, "
               "por ejemplo `gato azul,Alumno 07`. Los textos se convierten igual que en el Laboratorio.")
    usar_ventana = st.checkbox("Filtrar por ventana de entrega")
    desde = hasta = None
    if usar_ventana:
        c1, c2 = st.columns(2)
        d1 = c1.date_input("Desde"); d2 = c2.date_input("Hasta")
        desde = datetime.combine(d1, time.min, ZONA).astimezone(timezone.utc)
        hasta = datetime.combine(d2, time.max, ZONA).astimezone(timezone.utc)
    if st.button("Verificar lote", key="btn_lote") and archivos:
        asignadas = None
        if semillas is not None:
            df = pd.read_csv(io.BytesIO(semillas.getvalue()), dtype=str, header=None, names=["semilla", "id"])
            asignadas = {}
            for texto, ident in zip(df["semilla"].fillna(""), df["id"].fillna("")):
                if texto.strip().lower() == "semilla":
                    continue                                 # fila de encabezado
                try:
                    asignadas[str(prng.interpretar_semilla(texto)[0])] = ident
                except ValueError:
                    pass                                     # encabezados o líneas vacías
        try:
            filas = verificacion.verificar_lote({a.name: a.getvalue() for a in archivos}, desde, hasta, asignadas)
        except ValueError as e:
            st.error(str(e)); st.stop()
        tabla = pd.DataFrame([{**f, "alertas": "; ".join(f["alertas"])} for f in filas])
        st.dataframe(tabla, hide_index=True, width="stretch")
        st.download_button("Descargar resultados (CSV)", tabla.to_csv(index=False).encode("utf-8"), "verificacion_lote.csv", "text/csv")
