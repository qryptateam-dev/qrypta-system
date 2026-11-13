"""Único punto de acceso al estado temporal de la pestaña (st.session_state). Sin base de datos."""
import streamlit as st

CLAVE = "experimento"

def obtener():
    return st.session_state.get(CLAVE)

def guardar(exp: dict) -> None:
    st.session_state[CLAVE] = exp
    for clave in ("exportacion", "serie"):          # un experimento nuevo invalida lo derivado del anterior
        st.session_state.pop(clave, None)

def requerir(*partes: str) -> dict:
    """Detiene la vista con un aviso si falta una etapa previa del experimento."""
    exp = obtener()
    if exp is None:
        st.warning("Primero genere las claves en «2. Laboratorio de Generación de Claves».")
        st.stop()
    for p in partes:
        if p not in exp:
            st.warning(f"Falta completar la etapa previa: {p}.")
            st.stop()
    return exp
