import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import datetime
import requests
from bs4 import BeautifulSoup
import plotly.graph_objects as go

# Configuración inicial
st.set_page_config(page_title="Terminal Pro", layout="wide")

# Inicialización de estado
if "cartera_list_v4" not in st.session_state:
    st.session_state.cartera_list_v4 = []

# Menú principal
menu = st.radio("Sección:", ["🔍 ANÁLISIS", "💼 PORTAFOLIO"], horizontal=True)

if menu == "🔍 ANÁLISIS":
    st.subheader("Análisis Técnico")
    tk = st.text_input("Ticker", "VIST")
    if st.button("Correr Análisis"):
        st.write(f"Analizando {tk}...")
        # Aquí va toda tu lógica de análisis

elif menu == "💼 PORTAFOLIO":
    st.subheader("Gestión de Portafolio")
    
    # Formulario de carga
    with st.form("carga"):
        tk = st.text_input("Ticker")
        nom = st.number_input("Cantidad", 1)
        sub = st.form_submit_button("Cargar")
        if sub:
            st.session_state.cartera_list_v4.append({"Ticker": tk, "Nominales": nom, "Precio": 0, "Mercado": 0, "PL": 0})
            st.rerun()
            
    df = pd.DataFrame(st.session_state.cartera_list_v4)
    if not df.empty:
        df_editado = st.data_editor(df, use_container_width=True)
        st.session_state.cartera_list_v4 = df_editado.to_dict(orient="records")
        
        # Reporte
        if st.button("Generar Reporte"):
            filas_html = "".join([f"<tr><td>{x['Ticker']}</td><td>{x['Nominales']}</td></tr>" for x in st.session_state.cartera_list_v4])
            html = f"<table>{filas_html}</table>"
            st.download_button("Descargar Reporte", html, "reporte.html")
