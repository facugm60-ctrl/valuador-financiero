import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

st.set_page_config(page_title="Valuador Financiero Pro", layout="wide")

st.title("📊 Plataforma de Valuación de Empresas Públicas")
st.markdown("Analizá ratios financieros, salud de balance, flujos descontados y tendencias en tiempo real.")

# Entrada de datos
col1, col2 = st.columns([1, 2])
with col1:
    ticker_objetivo = st.text_input("Introduce el Ticker Objetivo:", value="VIST").upper()
with col2:
    competidores_input = st.text_input("Introduce Competidores (separados por coma):", value="YPF, XOM, PAM")
    competidores = [c.strip().upper() for c in competidores_input.split(",") if c.strip()]

todos_los_tickers = [ticker_objetivo] + competidores

def obtener_ratios(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        if not info or ('currentPrice' not in info and 'previousClose' not in info):
            return None
            
        total_deuda = info.get("totalDebt", 0)
        caja = info.get("totalCash", 0)
        ebitda = info.get("ebitda", 0)
        
        deuda_neta = total_deuda - caja
        net_debt_ebitda = deuda_neta / ebitda if ebitda and ebitda > 0 else None
            
        return {
            "Ticker": ticker_symbol,
            "Nombre": info.get("longName", "N/A"),
            "Precio Actual": info.get('currentPrice', info.get('previousClose', 0)),
            "Forward P/E": info.get("forwardPE"),
            "EV/EBITDA": info.get("enterpriseToEbitda"),
            "P/B Ratio": info.get("priceToBook"),
            "Deuda Neta/EBITDA": net_debt_ebitda,
            "Liquidez Corriente": info.get("currentRatio"),
            "Beta": info.get("beta"),
            "Margen Neto": info.get("profitMargins"),
            "ROE": info.get("returnOnEquity"),
            "FCF_Total": info.get("freeCashflow"),
            "Acciones_Circulacion": info.get("sharesOutstanding")
        }
    except:
        return None

# --- FUNCIONES DE ESTILO INTELIGENTE ---
def resaltar_maximo(s):
    is_max = s == s.max()
    return ['background-color: rgba(46, 204, 113, 0.4); font-weight: bold' if v else '' for v in is_max]

def resaltar_minimo(s):
    valores_validos = s[s > 0]
    if valores_validos.empty: return ['' for _ in s]
    is_min = s == valores_validos.min()
    return ['background-color: rgba(46, 204, 113, 0.4); font-weight: bold' if v else '' for v in is_min]


if st.button("🔥 Correr Análisis de Valuación"):
    with st.spinner("Conectando con Wall Street y procesando balances..."):
        datos = []
        for t in todos_los_tickers:
            res = obtener_ratios(t)
            if res: datos.append(res)
            
        if datos:
            df = pd.DataFrame(datos)
            
            # --- SECCIÓN 1: MATRIZ COMPLETA DE DATOS ---
            st.subheader("📋 Matriz Completa de Datos Financieros y de Balance")
            
            df_mostrar = df.copy().drop(columns=["FCF_Total", "Acciones_Circulacion"])
            styled_df = df_mostrar.style.apply(resaltar_minimo, subset=["Forward P/E", "EV/EBITDA", "P/B Ratio", "Deuda Neta/EBITDA"])\
                                      .apply(resaltar_maximo, subset=["Liquidez Corriente", "Margen Neto", "ROE"])\
                                      .format({
                                          "Precio Actual": "{:.2f} USD", "Forward P/E": "{:.2f}",
                                          "P/B Ratio": "{:.2f}", "EV/EBITDA": "{:.2f}", 
                                          "Deuda Neta/EBITDA": "{:.2f}x", "Liquidez Corriente": "{:.2f}x",
                                          "Beta": "{:.2f}",
                                          "Margen Neto": lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A",
                                          "ROE": lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A"
                                      }, na_rep="N/A")
            
            st.dataframe(styled_df, width="stretch", column_config={
                "Forward P/E": st.column_config.NumberColumn("Forward P/E ❓", help="Mide cuántas veces pag