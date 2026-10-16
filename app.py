"""Esqueleto de demo: pegas o subes texto -> el LLM extrae datos estructurados -> se muestran y se guardan.
Ejecuta con:  streamlit run app.py
Adáptalo al reto (cambia el modelo Pydantic y el prompt).
"""
import sqlite3

import pandas as pd
import streamlit as st
from pydantic import BaseModel

from llm import PROVIDER, ask, ask_structured

st.set_page_config(page_title="Mavericks demo", layout="wide")
st.title("Prototipo GenAI")
st.caption(f"Proveedor LLM: {PROVIDER}")


# 1) CAMBIA ESTO según el reto: qué datos quieres extraer/estructurar
class Resultado(BaseModel):
    resumen: str
    puntos_clave: list[str]
    riesgos: list[str]


# 2) Base de datos local (SQLite viene con Python)
conn = sqlite3.connect("demo.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS resultados (id INTEGER PRIMARY KEY, entrada TEXT, salida TEXT)")

col_in, col_out = st.columns(2)

with col_in:
    archivo = st.file_uploader("Sube un .txt (opcional)", type=["txt"])
    texto = st.text_area("Entrada", value=archivo.read().decode("utf-8") if archivo else "", height=300)
    modo = st.radio("Modo", ["Texto libre", "Datos estructurados"], horizontal=True)
    lanzar = st.button("Analizar", type="primary", disabled=not texto.strip())

with col_out:
    if lanzar:
        with st.spinner("Pensando..."):
            if modo == "Texto libre":
                salida = ask(texto, system="Eres un analista experto. Responde en español, claro y breve.")
                st.markdown(salida)
            else:
                obj = ask_structured(texto, Resultado, system="Analiza el texto y extrae los datos pedidos en español.")
                salida = obj.model_dump_json(ensure_ascii=False)
                st.json(obj.model_dump())
        conn.execute("INSERT INTO resultados (entrada, salida) VALUES (?, ?)", (texto, salida))
        conn.commit()

st.divider()
st.subheader("Historial")
st.dataframe(pd.read_sql("SELECT * FROM resultados ORDER BY id DESC", conn), use_container_width=True)
