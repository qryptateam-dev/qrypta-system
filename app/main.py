"""Punto de entrada de Streamlit: define el menú lateral de 6 vistas (Informe Técnico, sección 7)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # permite 'import core'
import streamlit as st

st.set_page_config(page_title="QRYPTA — Simulador de aleatoriedad", page_icon="🔐", layout="wide")

VISTAS = Path(__file__).parent / "vistas"
menu = st.navigation([
    st.Page(VISTAS / "inicio.py", title="1. Inicio y Guía de Uso", default=True),
    st.Page(VISTAS / "laboratorio.py", title="2. Laboratorio de Generación de Claves"),
    st.Page(VISTAS / "analisis.py", title="3. Análisis de Entropía y Aleatoriedad"),
    st.Page(VISTAS / "clasificacion.py", title="4. Clasificación con IA"),
    st.Page(VISTAS / "dashboard.py", title="5. Dashboard e Informe"),
    st.Page(VISTAS / "verificar.py", title="6. Verificar Informe"),
])
menu.run()
