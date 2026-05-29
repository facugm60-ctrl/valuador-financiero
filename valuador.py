import streamlit as st
import pandas as pd
import yfinance as yf
import datetime
import requests
from bs4 import BeautifulSoup
import plotly.graph_objects as go

# Configuración básica
st.set_page_config(page_title="Terminal Pro", layout="wide")

# (Aquí irían tus estilos CSS que ya tenías funcionando)

# Funciones de soporte
@st.cache_data(ttl=600)
def obtener_dolar_mep():
    return 1433.25 # Valor de referencia

# Inicialización de estado
if "cartera_list" not in st.session_state:
    st.session_state.cartera_list = [
        {"Ticker": "VIST", "Nominales": 100, "Ratio": 1, "Precio": 52.0, "Mercado": 55.0, "PL": 5.7}
    ]

st.title("Terminal Financiera")

# Pestañas de navegación
tab1, tab2 = st.tabs(["Dashboard", "Portafolio"])

with tab2:
    st.subheader("Control de Posiciones")
    
    # Editor de tabla
    df_editor = st.data_editor(
        pd.DataFrame(st.session_state.cartera_list),
        use_container_width=True,
        num_rows="dynamic"
    )
    
    # Botón para generar reporte corregido
    if st.button("Generar Reporte de Descarga"):
        # Aseguramos que la variable que usa el reporte sea la del editor
        filas_portfolio_pdf = df_editor.to_dict(orient="records")
        
        # Lógica del reporte HTML/PDF
        filas_html_reporte = "".join([
            f"<tr><td>{x['Ticker']}</td><td>{x['Nominales']}</td><td>{x['Ratio']}</td><td>{x['Precio']}</td><td>{x['Mercado']}</td><td style='color:#2ecc71'>{x['PL']}</td></tr>" 
            for x in filas_portfolio_pdf
        ])
        
        html_documento = f"""
        <html>
        <body>
            <h1>Reporte de Portafolio</h1>
            <table border='1'>
                <thead><tr><th>Ticker</th><th>Cantidad</th><th>Ratio</th><th>Precio</th><th>Mercado</th><th>PL (%)</th></tr></thead>
                <tbody>{filas_html_reporte}</tbody>
            </table>
        </body>
        </html>
        """
        
        st.download_button(
            label="Descargar Reporte HTML",
            data=html_documento,
            file_name="reporte_portfolio.html",
            mime="text/html"
        )
        st.success("Reporte generado exitosamente. Hacé clic en el botón de descarga.")
