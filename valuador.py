import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.figure_factory as ff
import urllib.parse
import requests

# 1. CONFIGURACIÓN PREMIUM Y TIPOGRAFÍA MONTSERRAT
st.set_page_config(page_title="Terminal Quanti Pro", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Montserrat', sans-serif !important;
    }
    
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    h1 {font-weight: 800; color: #FFFFFF; font-size: 28px !important;}
    h2 {font-weight: 700; color: #F0F2F6; font-size: 20px !important;}
    h3 {font-weight: 700; color: #F0F2F6; font-size: 16px !important;}
    
    .stMetric label {font-size: 13px !important; font-weight: 600;}
    .stMetric div {font-size: 24px !important; font-weight: 700;}
    
    .stButton>button {
        width: 100%; background-color: #2ecc71; color: white;
        font-weight: bold; border-radius: 8px; border: none;
        padding: 0.5rem; font-size: 15px !important; margin-top: 10px;
    }
    .stButton>button:hover { background-color: #27ae60; }
    </style>
""", unsafe_allow_html=True)

# 2. SEED DE SESIÓN PARA MEMORIA INTERMEDIA
if "watchlist_items" not in st.session_state:
    st.session_state.watchlist_items = ["VIST", "YPF", "AAPL", "GGAL", "AMD", "NVDA"]

if "cartera_data" not in st.session_state:
    st.session_state.cartera_data = [
        {"Ticker": "VIST", "Nominales": 100, "Precio Compra (USD)": 50.0},
        {"Ticker": "WMT", "Nominales": 50, "Precio Compra (USD)": 75.0},
        {"Ticker": "KO", "Nominales": 80, "Precio Compra (USD)": 60.0},
        {"Ticker": "SPY", "Nominales": 10, "Precio Compra (USD)": 500.0}
    ]

if "analisis_ok" not in st.session_state:
    st.session_state.analisis_ok = False
    st.session_state.res = None
    st.session_state.t_act = ""

# 3. BACKEND DE EXTRACCIÓN Y TRADUCCIÓN
def traducir_espanol(texto):
    if not texto: return "Sin descripción disponible."
    try:
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=es&dt=t&q=" + urllib.parse.quote(texto)
        r = requests.get(url, timeout=3).json()
        return "".join([frase[0] for frase in r[0] if frase[0]])
    except: return texto

def obtener_datos(symbol):
    try:
        t = yf.Ticker(symbol)
        inf = t.info
        if not inf or len(inf) < 5: return None
        logo = f"https://icons.duckduckgo.com/ip3/{symbol.lower()}.com.ico"
        desc = traducir_espanol(inf.get("longBusinessSummary", "")) if symbol == st.session_state.get("t_act", "") else ""
        
        common = {"Ticker": symbol, "Nombre": inf.get("longName", symbol), "Precio Actual": inf.get('currentPrice', inf.get('previousClose', 1.0)), "Logo": logo, "Descripcion": desc}
        
        if "ebitda" in inf or "forwardPE" in inf:
            td, caj, eb = inf.get("totalDebt", 0), inf.get("totalCash", 0), inf.get("ebitda", 1)
            common.update({"Tipo": "ACCION", "Forward P/E": inf.get("forwardPE", 12), "EV/EBITDA": inf.get("enterpriseToEbitda", 7), "P/B Ratio": inf.get("priceToBook", 1.5), "Deuda Neta/EBITDA": (td-caj)/eb if eb else 0, "Liquidez Corriente": inf.get("currentRatio", 1.2), "Beta": inf.get("beta", 1), "Margen Neto": inf.get("profitMargins", 0.1), "ROE": inf.get("returnOnEquity", 0.1), "FCF_Total": inf.get("freeCashflow", 1e8), "Acciones": inf.get("sharesOutstanding", 1e7), "Div_Rate": inf.get("dividendRate", 0)})
        else:
            common.update({"Tipo": "ETF", "P/E Canasta": inf.get("trailingPE", 15), "Expense Ratio": inf.get("feesExpensesInvestmentPercentage", 0.001), "Dividend Yield": inf.get("dividendYield", 0.02), "Beta": inf.get("beta", 1)})
        return common
    except: return None

# 4. ENTORNO GLOBAL (MENÚ SUPERIOR DIRECTO)
st.title("📊 Terminal Analítica Cuantitativa")
menu = st.radio("Sección Operativa:", ["🌐 DASHBOARD GENERAL", "🔍 INTELIGENCIA Y SCREENING", "💼 PORTAFOLIO MULTIACTIVO"], horizontal=True)
st.markdown("---")

# ==========================================
# SECCIÓN 1: DASHBOARD GENERAL
# ==========================================
if menu == "🌐 DASHBOARD GENERAL":
    st.subheader("📌 Mi Watchlist de Seguimiento")
    
    c1, c2 = st.columns([4, 1])
    with c2:
        st.markdown("**Panel de Control:**")
        nuevo = st.text_input("Sumar Activo:", value="").upper().strip()
        if st.button("➕ Agregar") and nuevo:
            if nuevo not in st.session_state.watchlist_items:
                st.session_state.watchlist_items.append(nuevo)
                st.rerun()
        
        quitar = st.selectbox("Quitar Activo:", [""] + st.session_state.watchlist_items)
        if st.button("🗑️ Quitar") and quitar:
            st.session_state.watchlist_items.remove(quitar)
            st.rerun()
            
    with c1:
        if st.session_state.watchlist_items:
            with st.spinner("Sincronizando cotizaciones de la Watchlist..."):
                registros_w = [obtener_datos(t) for t in st.session_state.watchlist_items if obtener_datos(t)]
                if registros_w:
                    df_w = pd.DataFrame(registros_w)
                    st.dataframe(df_w[["Ticker", "Nombre", "Precio Actual", "Tipo"]].set_index("Ticker"), use_container_width=True)
        else:
            st.info("No hay activos cargados en la lista de seguimiento.")

# ==========================================
# SECCIÓN 2: INTELIGENCIA Y SCREENING
# ==========================================
elif menu == "🔍 INTELIGENCIA Y SCREENING":
    c_s1, c_s2 = st.columns([1, 2])
    t_obj = c_s1.text_input("📍 ACTIVO OBJETIVO:", value="VIST").upper().strip()
    t_comp = c_s2.text_input("🔍 COMPETIDORES DEL SECTOR (separados por coma):", value="YPF, XOM, PAM").upper()
    competidores = [c.strip() for c in t_comp.split(",") if c.strip()]
    
    if st.button("🔥 EJECUTAR DIAGNÓSTICO INTEGRAL"):
        st.session_state.t_act = t_obj
        with st.spinner("Procesando estados contables y métricas de volatilidad..."):
            lista_datos = []
            for tk in [t_obj] + competidores:
                r = obtener_datos(tk)
                if r: lista_datos.append(r)
                
            if not lista_datos or not any(d["Ticker"] == t_obj for d in lista_datos):
                fake = {"Ticker": t_obj, "Nombre": f"{t_obj} Corp", "Precio Actual": 50.0, "Logo": "https://cdn-icons-png.flaticon.com/512/2967/2967304.png", "Descripcion": "Simulación activa por corte nocturno de API externa.", "Tipo": "ACCION", "Forward P/E": 11.5, "EV/EBITDA": 5.4, "P/B Ratio": 1.3, "Deuda Neta/EBITDA": 1.1, "Liquidez Corriente": 1.4, "Beta": 1.1, "Margen Neto": 0.12, "ROE": 0.16, "FCF_Total": 400000000, "Acciones": 80000000, "Div_Rate": 1.0}
                lista_datos.append(fake)
                
            st.session_state.res = lista_datos
            st.session_state.analisis_ok = True

    if st.session_state.get("analisis_ok"):
        df = pd.DataFrame(st.session_state.res)
        obj = df[df['Ticker'] == st.session_state.t_act].iloc[0]
        
        st.markdown(f"### <img src='{obj['Logo']}' width='32'> {obj['Nombre']} ({obj['Ticker']})", unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["📝 ANÁLISIS FUNDAMENTAL", "📈 ANÁLISIS TÉCNICO", "🧮 VALOR INTRÍNSECO (DCF + MONTECARLO)"])
        
        with tab1:
            st.subheader("ℹ️ Perfil Operativo de la Compañía")
            st.write(obj["Descripcion"])
            
            if obj["Tipo"] == "ACCION":
                st.markdown("---")
                st.subheader("📋 Matriz Comparativa del Sector (Ganadores Resaltados)")
                df_acc = df[df['Tipo'] == "ACCION"].copy().set_index("Ticker")
                if not df_acc.empty:
                    cols = [c for c in ["Forward P/E", "EV/EBITDA", "Deuda Neta/EBITDA", "ROE", "Margen Neto"] if c in df_acc.columns]
                    st.dataframe(df_acc[cols].style.highlight_min(subset=cols[:3], color="#1b4d22").highlight_max(subset=cols[3:], color="#1b4d22"), use_container_width=True)

        with tab2:
            st.subheader("📐 Terminal de Timing y Osciladores")
            try:
                h = yf.Ticker(obj["Ticker"]).history(period="1y")
                if len(h) > 15:
                    cierre = h['Close']
                    ema = cierre.ewm(span=30, adjust=False).mean()
                    
                    # Panel A
                    fig_a = go.Figure()
                    fig_a.add_trace(go.Scatter(x=h.index, y=cierre, name="Precio", line=dict(color='#3498db', width=2)))
                    fig_a.add_trace(go.Scatter(x=h.index, y=ema, name="EMA 30 Ruedas", line=dict(color='#e74c3c', width=1.5)))
                    fig_a.update_layout(title="Panel A: Estructura de Mediano Plazo vs. EMA 30", height=280, template="plotly_dark", margin=dict(l=15
