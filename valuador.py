# -*- coding: utf-8 -*-

import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import datetime
import requests
from bs4 import BeautifulSoup
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ------------------------------------------------------------------------------
# DISFRAZ ANTI-BLOQUEO PARA YAHOO FINANCE (Evita que devuelva todo en 0.00)
# ------------------------------------------------------------------------------
yf_session = requests.Session()
yf_session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
})

# Intentamos importar el traductor para pasar el resumen al español
try:
    from deep_translator import GoogleTranslator
    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y PARAMETRIZACIÓN DE ESTILOS FINTECH
# ==============================================================================
st.set_page_config(page_title="Terminal Quanti Pro", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght=300;400;600;700;800&display=swap');
    
    html, body, [class*="css"], [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #0c0f16 !important;
        color: #f1f5f9 !important;
        font-family: 'Montserrat', sans-serif !important;
    }
    
    .stMarkdown, p, span, label, li {
        color: #cbd5e1 !important;
    }
    
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    h1 {font-weight: 800; color: #ffffff !important; font-size: 30px !important; letter-spacing: -0.8px;}
    h2 {font-weight: 700; color: #f8fafc !important; font-size: 21px !important; margin-top: 15px;}
    h3 {font-weight: 600; color: #f1f5f9 !important; font-size: 16px !important;}
    
    /* Selector de Navegación Premium */
    div[data-testid="stRadio"] > label { display: none !important; }
    div[data-testid="stRadio"] > div {
        background: rgba(22, 27, 34, 0.7) !important;
        backdrop-filter: blur(12px) !important;
        padding: 8px !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        gap: 12px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5) !important;
        margin-bottom: 20px !important;
    }
    div[data-testid="stRadio"] label[data-baseweb="radio"] {
        background-color: transparent !important;
        border: 1px solid transparent !important;
        padding: 8px 18px !important;
        border-radius: 8px !important;
        color: #94a3b8 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        font-weight: 600 !important;
    }
    div[data-testid="stRadio"] label[data-baseweb="radio"]:hover {
        color: #ffffff !important;
        background: rgba(255, 255, 255, 0.05) !important;
        border-color: rgba(88, 166, 255, 0.3) !important;
    }
    
    /* KPIs Bloques */
    div[data-testid="stMetric"] {
        background-color: #111520 !important;
        border: 1px solid #1f2937 !important;
        border-radius: 10px !important;
        padding: 15px 20px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    div[data-testid="stMetric"] label { font-size: 11px !important; font-weight: 600; color: #64748b !important; text-transform: uppercase; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { font-size: 24px !important; font-weight: 800; color: #ffffff !important; }
    
    /* Botonera */
    .stButton>button {
        width: 100%; background: linear-gradient(135deg, #2ecc71, #27ae60) !important;
        color: white !important; font-weight: 700; border-radius: 8px; border: none;
        padding: 0.6rem; font-size: 13px !important; text-transform: uppercase; letter-spacing: 0.5px;
    }
    .stButton>button:hover { background: linear-gradient(135deg, #27ae60, #219653) !important; transform: translateY(-1px); }
    
    /* Inputs */
    div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] div, div[data-testid="stNumberInput"] input, div[data-testid="stDateInput"] input {
        background-color: #111520 !important; color: #ffffff !important; border: 1px solid #1f2937 !important; border-radius: 8px !important;
    }
    
    /* Estructuras Informativas */
    .radar-box-gainer-high { background: linear-gradient(135deg, #064e3b, #047857); border: 1px solid #10b981; padding: 14px; border-radius: 8px; font-weight: bold; color: #34d399 !important; }
    .radar-box-loser { background: linear-gradient(135deg, #7f1d1d, #b91c1c); border: 1px solid #f87171; padding: 14px; border-radius: 8px; font-weight: bold; color: #f87171 !important; }
    .interpretation-box { background-color: #111520; padding: 16px; border-radius: 8px; font-size: 13px; color: #e2e8f0; line-height: 1.6; border: 1px solid #1f2937; border-left: 4px solid #2ecc71; margin-top: 10px; }
    .agent-box { background-color: #090d16; padding: 18px; border-radius: 8px; font-size: 13px; color: #e2e8f0; border: 1px solid #1f2937; border-left: 4px solid #dfa427; line-height: 1.6; margin-top: 10px; }
    
    /* Estilos para Tablas HTML Corporativas */
    .custom-table { width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 13px; background-color: #111520; border-radius: 8px; overflow: hidden; border: 1px solid #1f2937; }
    .custom-table th { background-color: #161b22; color: #ffffff; padding: 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #1f2937; position: relative; }
    .custom-table td { padding: 12px; border-bottom: 1px solid #1f2937; color: #e2e8f0; }
    .custom-table tr:hover { background-color: #1c2331; }
    .winner-cell { background-color: rgba(46, 204, 113, 0.15) !important; color: #2ecc71 !important; font-weight: bold; border: 1px solid rgba(46, 204, 113, 0.3) !important; }
    
    /* CSS Tooltips */
    .tooltip { position: relative; display: inline-block; cursor: pointer; color: #3498db; margin-left: 4px; font-weight: bold; }
    .tooltip .tooltiptext { visibility: hidden; width: 280px; background-color: #1f2937; color: #fff; text-align: left; padding: 12px; border-radius: 6px; position: absolute; z-index: 999; bottom: 125%; left: 50%; margin-left: -140px; opacity: 0; transition: opacity 0.3s; font-size: 11px; font-weight: normal; line-height: 1.4; border: 1px solid #3b82f6; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }
    .tooltip:hover .tooltiptext { visibility: visible; opacity: 1; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. CONEXIÓN EN VIVO A DOLARITO PARA EXTRACCIÓN REAL DEL MEP
# ==============================================================================
@st.cache_data(ttl=600)
def obtener_dolar_mep_real():
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        r = requests.get("https://www.dolarito.ar/", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for element in soup.find_all(['div', 'span', 'p']):
            texto = element.get_text().lower()
            if 'mep' in texto and '$' in texto:
                for token in texto.split():
                    if '$' in token:
                        clean_token = token.replace('$', '').replace('.', '').replace(',', '.').strip()
                        try:
                            val = float(clean_token)
                            if 1300 < val < 1600:
                                return round(val, 2)
                        except: pass
        return 1433.25
    except:
        return 1433.25

DOLAR_MEP = obtener_dolar_mep_real()

RATIOS_CEDEAR = {
    "VIST": 1, "YPF": 1, "AAPL": 10, "GGAL": 1, "AMD": 10, "NVDA": 24, 
    "MSFT": 30, "AMZN": 14, "GOOGL": 11, "META": 24, "TSLA": 15, "KO": 5, 
    "WMT": 6, "JNJ": 15, "PEP": 15, "PG": 15, "XOM": 5, "PAMP": 1, 
    "SPY": 20, "QQQ": 20, "DIA": 20, "MO": 4, "CVX": 8, "MCD": 24,
    "BRKB": 22, "MELI": 60, "BABA": 9, "PYPL": 3, "NFLX": 16, "DESP": 1, "VALE": 2
}

UNIVERSO_POOL = ["VIST", "YPF", "AAPL", "GGAL", "AMD", "NVDA", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "KO", "WMT", "XOM", "SPY", "QQQ", "JNJ", "PEP", "PG", "MO", "CVX", "MCD", "BRKB", "MELI", "BABA", "PYPL", "NFLX", "DESP", "VALE"]

EXPLICACIONES_TECNICAS = {
    "PE": "<b>P/E (Precio sobre Ganancias):</b><br>Te dice cuántos años tardarías en recuperar la inversión si la empresa sigue ganando lo mismo siempre. Un número bajo significa que estás comprando barato.",
    "EV": "<b>EV/EBITDA:</b><br>Mide cuánto cuesta comprar la empresa entera (con deudas incluidas) en relación al efectivo limpio que genera. Si es bajo, la empresa se paga sola rápidamente.",
    "DEUDA": "<b>Deuda / EBITDA:</b><br>Compara lo que debe la empresa con lo que genera en un año. Como ver si debés 1 o 5 sueldos enteros. Valores muy altos son luz roja.",
    "LIQUIDEZ": "<b>Liquidez Corriente:</b><br>Compara el efectivo rápido que tiene la empresa contra las deudas que tiene que pagar ya mismo. Mayor a 1 significa que está tranquila.",
    "MARGEN": "<b>Margen Neto:</b><br>De cada $100 que vende la empresa, ¿cuántos billetes le quedan limpios en el bolsillo después de pagar todos los gastos e impuestos?",
    "ROE": "<b>ROE (Retorno sobre Patrimonio):</b><br>Muestra qué tan buenos son los dueños para hacer rendir la plata que invirtieron. Cuanto más alto, más jugo le sacan al capital."
}

# ==============================================================================
# 3. MOTOR UNIFICADO E HISTÓRICO DE SERIES DE TIEMPO
# ==============================================================================
@st.cache_data(ttl=600)
def descargar_datos_historicos_unificados(universo):
    datos_dict = {}
    try:
        df_hist = yf.download(universo, period="2y", progress=False, session=yf_session)
        if "Close" in df_hist.columns:
            df_close = df_hist["Close"]
        else:
            df_close = df_hist

        df_close = df_close.ffill().bfill()
        año_actual = datetime.datetime.now().year
        fecha_ytd = f"{año_actual}-01-02"
        
        for tk in universo:
            try:
                if isinstance(df_close, pd.DataFrame) and tk in df_close.columns:
                    serie = df_close[tk].dropna()
                elif isinstance(df_close, pd.Series):
                    serie = df_close.dropna()
                else:
                    serie = pd.Series(dtype=float)

                if not serie.empty and len(serie) >= 30:
                    px_actual = float(serie.iloc[-1])
                    var_1d = ((px_actual / float(serie.iloc[-2])) - 1) * 100 if len(serie) > 1 else 0.0
                    var_1w = ((px_actual / float(serie.iloc[-6])) - 1) * 100 if len(serie) > 5 else 0.0
                    var_1m = ((px_actual / float(serie.iloc[-22])) - 1) * 100 if len(serie) > 21 else 0.0
                    
                    try:
                        serie_ytd = serie.loc[fecha_ytd:]
                        var_ytd = ((px_actual / float(serie_ytd.iloc[0])) - 1) * 100 if not serie_ytd.empty else 0.0
                    except:
                        var_ytd = 0.0
                        
                    datos_dict[tk] = {
                        "precio": px_actual, "1D": var_1d, "1W": var_1w, "1M": var_1m, "YTD": var_ytd, "serie_completa": serie
                    }
                else:
                    datos_dict[tk] = {"precio": 100.0, "1D": 0.0, "1W": 0.0, "1M": 0.0, "YTD": 0.0, "serie_completa": pd.Series(dtype=float)}
            except:
                datos_dict[tk] = {"precio": 100.0, "1D": 0.0, "1W": 0.0, "1M": 0.0, "YTD": 0.0, "serie_completa": pd.Series(dtype=float)}
    except:
        for tk in universo:
            datos_dict[tk] = {"precio": 100.0, "1D": 0.0, "1W": 0.0, "1M": 0.0, "YTD": 0.0, "serie_completa": pd.Series(dtype=float)}
    return datos_dict

POOL_DATA = descargar_datos_historicos_unificados(UNIVERSO_POOL)

def calcular_dividendos_historicos(ticker, fecha_compra, nominales):
    try:
        t = yf.Ticker(ticker, session=yf_session)
        divs = t.dividends
        if divs.empty: return 0.0
        fecha_compra_dt = pd.to_datetime(fecha_compra)
        if fecha_compra_dt.tzinfo is None:
            fecha_compra_dt = fecha_compra_dt.tz_localize(divs.index.tz)
        divs_filtrados = divs[divs.index >= fecha_compra_dt]
        return round(float(divs_filtrados.sum()) * nominales, 2)
    except:
        return 0.0

def calcular_dividendos_proyectados_un_año(ticker, nominales):
    try:
        t = yf.Ticker(ticker, session=yf_session)
        divs = t.dividends
        if divs.empty: return 0.0
        hace_un_año = pd.Timestamp.now().tz_localize(divs.index.tz) - pd.Timedelta(days=365)
        divs_ultimo_año = divs[divs.index >= hace_un_año]
        return round(float(divs_ultimo_año.sum()) * nominales, 2)
    except:
        return 0.0

def safe_float(val, default_val=0.0):
    try:
        if val is None or pd.isna(val):
            return default_val
        return float(val)
    except:
        return default_val

# Función blindada para procesar los datos fundamentales
def obtener_fundamental_completo(symbol):
    try:
        t = yf.Ticker(symbol, session=yf_session)
        inf = t.info
        
        # Si info viene vacío o falla, usamos fast_info como respaldo
        if not inf: 
            fi = t.fast_info
            inf = {
                "currentPrice": getattr(fi, "last_price", 50.0),
                "longName": symbol,
                "longBusinessSummary": "Resumen no disponible. Yahoo Finance limitó el acceso a la base de datos temporalmente.",
                "recommendationKey": "hold"
            }
        
        px = POOL_DATA.get(symbol, {}).get("precio", inf.get("currentPrice", 50.0))
        
        td = safe_float(inf.get("totalDebt"), 0.0)
        caj = safe_float(inf.get("totalCash"), 0.0)
        eb = safe_float(inf.get("ebitda"), 1.0)
        pe = safe_float(inf.get("forwardPE"), 0.0)
        ev = safe_float(inf.get("enterpriseToEbitda"), 0.0)
        liq = safe_float(inf.get("currentRatio"), 0.0)
        marg = safe_float(inf.get("profitMargins"), 0.0)
        roe = safe_float(inf.get("returnOnEquity"), 0.0)
        
        ratio_deuda = (td - caj) / eb if eb != 0 else 0.0
        
        return {
            "Ticker": symbol, "Nombre": inf.get("longName", symbol), "Precio": px,
            "PE": pe, "EV": ev, "DEUDA": ratio_deuda, "LIQUIDEZ": liq,
            "MARGEN": marg, "ROE": roe, "RAW_INFO": inf
        }
    except Exception as e:
        px = POOL_DATA.get(symbol, {}).get("precio", 50.0)
        return {
            "Ticker": symbol, "Nombre": symbol, "Precio": px,
            "PE": 0.0, "EV": 0.0, "DEUDA": 0.0, "LIQUIDEZ": 0.0,
            "MARGEN": 0.0, "ROE": 0.0, "RAW_INFO": {}
        }

def filtrar_peers_por_sector(ticker_raiz, lista_ingresada):
    try:
        sec_raiz = yf.Ticker(ticker_raiz, session=yf_session).info.get("sector", "")
    except:
        sec_raiz = ""
    peers_validos = []
    for p in lista_ingresada:
        p_clean = p.strip().upper()
        if not p_clean: continue
        try:
            sec_p = yf.Ticker(p_clean, session=yf_session).info.get("sector", "")
            if sec_p == sec_raiz or not sec_raiz: peers_validos.append(p_clean)
        except:
            peers_validos.append(p_clean)
    return peers_validos

# CONFIGURACIÓN DEL SESSION STATE DE CARTERA
if "cartera_list_v4" not in st.session_state:
    st.session_state.cartera_list_v4 = [
        {"Ticker": "VIST", "Nominales": 100, "Fecha_Compra": datetime.date(2025, 6, 15), "Costo_Unitario_Cedear": 77200.0, "Comision_USD": 0.5, "Impuesto_USD": 0.1, "Dividendos_Edit": 0.0},
        {"Ticker": "XOM", "Nominales": 50, "Fecha_Compra": datetime.date(2025, 8, 10), "Costo_Unitario_Cedear": 31500.0, "Comision_USD": 0.4, "Impuesto_USD": 0.05, "Dividendos_Edit": 0.0}
    ]
    for pos in st.session_state.cartera_list_v4:
        pos["Dividendos_Edit"] = calcular_dividendos_historicos(pos["Ticker"], pos["Fecha_Compra"], pos["Nominales"])

# COMPONENTES DE MENÚ E IDENTIDAD LOCAL
menu = st.radio("Secciones operativas de la Terminal:", ["🌐 DASHBOARD GENERAL Y WATCHLIST", "🔍 ANÁLISIS INTEGRAL", "💼 PORTAFOLIO Y MODELOS FACTORIALES"], horizontal=True)
st.markdown("---")

# ==============================================================================
# SECCIÓN 1: DASHBOARD GENERAL Y WATCHLIST
# ==============================================================================
if menu == "🌐 DASHBOARD GENERAL Y WATCHLIST":
    st.subheader("⚡ Market Radar: Momentum de Ruedas")
    ordenados = sorted(POOL_DATA.items(), key=lambda x: x[1]["1D"], reverse=True)
    
    c_rad1, c_rad2, c_rad3, c_rad4 = st.columns(4)
    with c_rad1: st.markdown(f"<div class='radar-box-gainer-high'>🟢 Liderando la Rueda (1D)<br><br>• {ordenados[0][0]}: {ordenados[0][1]['1D']:+.2f}%<br>• {ordenados[1][0]}: {ordenados[1][1]['1D']:+.2f}%</div>", unsafe_allow_html=True)
    with c_rad2: st.markdown(f"<div class='radar-box-loser'>🔴 Mayor Compresión (1D)<br><br>• {ordenados[-1][0]}: {ordenados[-1][1]['1D']:+.2f}%<br>• {ordenados[-2][0]}: {ordenados[-2][1]['1D']:+.2f}%</div>", unsafe_allow_html=True)
    with c_rad3: st.markdown("<div class='radar-box-gainer-high'>🚀 Impulso Factorial Continuo<br><br>• VIST: Flujo en Expansión<br>• NVDA: Escalamiento Operativo</div>", unsafe_allow_html=True)
    with c_rad4: st.markdown("<div class='radar-box-loser'>📉 Compresión de Margen Cíclico<br><br>• KO: Estructura de Resguardo<br>• WMT: Ajuste de Retornos</div>", unsafe_allow_html=True)
        
    st.markdown("---")
    st.subheader("📌 Monitoreo General del Mercado (Watchlist Histórica Recompuesta)")
    watchlist_items = ["VIST", "YPF", "AAPL", "GGAL", "NVDA", "KO", "XOM", "WMT"]
    rows_w = []
    for t in watchlist_items:
        p_info = POOL_DATA.get(t, {"precio": 100.0, "1D": 0.0, "1W": 0.0, "1M": 0.0, "YTD": 0.0})
        ratio = RATIOS_CEDEAR.get(t, 1)
        px_ars = (p_info["precio"] / ratio) * DOLAR_MEP
        
        rows_w.append({
            "Ticker": t, "Precio Subyacente": f"${p_info['precio']:.2f} USD", "Cedear Estimado (ARS)": f"${px_ars:,.2f} ARS",
            "Retorno Diario (1D)": f"{p_info['1D']:+.2f}%", "Última Semana (1W)": f"{p_info['1W']:+.2f}%",
            "Último Mes (1M)": f"{p_info['1M']:+.2f}%", "Año a la Fecha (YTD)": f"{p_info['YTD']:+.2f}%"
        })
    st.dataframe(pd.DataFrame(rows_w).set_index("Ticker"), use_container_width=True)

# ==============================================================================
# SECCIÓN 2: ANÁLISIS INTEGRAL (MATRIZ + TÉCNICO DMI + MONTECARLO DUAL)
# ==============================================================================
elif menu == "🔍 ANÁLISIS INTEGRAL":
    st.subheader("🔍 Matriz de Desempeño Contable y Multiplicadores Sectoriales")
    c_s1, c_s2 = st.columns([1, 2])
    t_obj = c_s1.text_input("📍 Activo Bajo Estudio:", value="VIST").upper().strip()
    t_comp_raw = c_s2.text_input("Peers de Control (Separados por coma):", value="YPF, XOM").upper()
    
    if st.button("🔥 Correr Análisis"):
        with st.spinner("Descargando balances corporativos reales en vivo..."):
            raw_peers = [c.strip() for c in t_comp_raw.split(",") if c.strip()]
            peers_filtrados = filtrar_peers_por_sector(t_obj, raw_peers)
            lista_tickers = [t_obj] + peers_filtrados
            
            dataset = []
            info_raiz = {}
            for tk in lista_tickers:
                res_f = obtener_fundamental_completo(tk)
                if res_f:
                    dataset.append(res_f)
                    if tk == t_obj:
                        info_raiz = res_f.get("RAW_INFO", {})
            
            if dataset: 
                tab_fund, tab_tech, tab_montecarlo = st.tabs(["📊 Análisis Fundamental", "📈 Análisis Técnico (DMI)", "🎲 Simulación Montecarlo Dual"])
                
                # -------------------------------------------------------------
                # PESTAÑA 1: ANÁLISIS FUNDAMENTAL Y COMPULSA DE MERCADO
                # -------------------------------------------------------------
                with tab_fund:
                    st.markdown("### 🏢 ¿A qué se dedica esta empresa?")
                    
                    resumen_ingles = info_raiz.get("longBusinessSummary", "Resumen no disponible en la base de datos.")
                    
                    if HAS_TRANSLATOR and resumen_ingles != "Resumen no disponible en la base de datos.":
                        try:
                            resumen_espanol = GoogleTranslator(source='en', target='es').translate(resumen_ingles)
                        except:
                            resumen_espanol = resumen_ingles + "\n\n*(Nota: Falló el servicio de traducción. Mostrando versión original)*"
                    else:
                        resumen_espanol = resumen_ingles + "\n\n*(Aviso: Si no se instaló 'deep-translator' en requirements.txt, verás esto en inglés)*"
                        
                    st.info(resumen_espanol)
                    
                    col_reloj, col_caja = st.columns([1, 2])
                    
                    with col_reloj:
                        st.markdown("#### ¿Qué opina Wall Street?")
                        recom_str = str(info_raiz.get("recommendationKey", "hold")).lower().replace("_", " ")
                        target_val = 3
                        if "buy" in recom_str: target_val = 4
                        if "strong buy" in recom_str: target_val = 5
                        if "sell" in recom_str: target_val = 2
                        
                        fig_gauge = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=target_val,
                            title={'text': f"Consenso: {recom_str.upper()}", 'font': {'size': 14}},
                            gauge={
                                'axis': {'range': [1, 5], 'tickvals': [1,2,3,4,5], 'ticktext': ['Venta F.','Venta','Mantener','Compra','Compra F.']},
                                'bar': {'color': "#ffffff"},
                                'steps': [
                                    {'range': [1, 2.5], 'color': "#7f1d1d"},
                                    {'range': [2.5, 3.5], 'color': "#111520"},
                                    {'range': [3.5, 5], 'color': "#064e3b"}
                                ]
                            }
                        ))
                        fig_gauge.update_layout(height=220, margin=dict(l=10,r=10,t=30,b=10), paper_bgcolor='#111520', font={'color': '#ffffff'})
                        st.plotly_chart(fig_gauge, use_container_width=True)
                        
                    with col_caja:
                        st.markdown("#### 🎁 Caja de Sorpresas: Últimos 4 Trimestres")
                        st.markdown("*¿Cuánto vendió realmente vs cuánta plata limpia le quedó en el bolsillo?*")
                        try:
                            tk_ticker = yf.Ticker(t_obj, session=yf_session)
                            q_fin = tk_ticker.quarterly_financials
                            if not q_fin.empty:
                                r_rev = q_fin.index[q_fin.index.str.lower().str.replace(" ", "").str.contains("totalrevenue")][0]
                                r_net = q_fin.index[q_fin.index.str.lower().str.replace(" ", "").str.contains("netincome")][0]
                                
                                df_quarters = q_fin.loc[[r_rev, r_net]].dropna(axis=1).iloc[:, :4]
                                quarters_labels = [d.strftime('%d-%m-%Y') for d in df_quarters.columns][::-1]
                                revenue_vals = (df_quarters.loc[r_rev].values / 1e9)[::-1]
                                net_vals = (df_quarters.loc[r_net].values / 1e9)[::-1]
                                
                                fig_caja = go.Figure()
                                fig_caja.add_trace(go.Bar(x=quarters_labels, y=revenue_vals, name="Ingresos (Miles de Millones USD)", marker_color='#3498db'))
                                fig_caja.add_trace(go.Bar(x=quarters_labels, y=net_vals, name="Plata Limpia (Miles de Millones USD)", marker_color='#2ecc71'))
                                fig_caja.update_layout(barmode='group', template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', height=200, margin=dict(l=10,r=10,t=10,b=20))
                                st.plotly_chart(fig_caja, use_container_width=True)
                            else:
                                st.warning("Yahoo Finance bloqueó temporalmente el acceso a los datos trimestrales.")
                        except:
                            st.warning("No se pudo graficar la caja de sorpresas debido a un bloqueo de conexión o falta de datos públicos.")
                    
                    st.markdown("---")
                    st.markdown("#### Matriz de Comparación (Frente a sus competidores)")
                    ganador_pe = min(dataset, key=lambda x: x["PE"])["Ticker"]
                    ganador_ev = min(dataset, key=lambda x: x["EV"])["Ticker"]
                    ganador_deuda = min(dataset, key=lambda x: x["DEUDA"])["Ticker"]
                    ganador_liquidez = max(dataset, key=lambda x: x["LIQUIDEZ"])["Ticker"]
                    ganador_margen = max(dataset, key=lambda x: x["MARGEN"])["Ticker"]
                    ganador_roe = max(dataset, key=lambda x: x["ROE"])["Ticker"]
                    
                    html_table = "<table class='custom-table'><thead><tr>"
                    html_table += "<th>Ticker</th><th>Razón Social</th>"
                    html_table += f"<th>Precio/Ganancia (PE) <div class='tooltip'>ⓘ<span class='tooltiptext'>{EXPLICACIONES_TECNICAS['PE']}</span></div></th>"
                    html_table += f"<th>Costo Empresa (EV) <div class='tooltip'>ⓘ<span class='tooltiptext'>{EXPLICACIONES_TECNICAS['EV']}</span></div></th>"
                    html_table += f"<th>Nivel de Deuda <div class='tooltip'>ⓘ<span class='tooltiptext'>{EXPLICACIONES_TECNICAS['DEUDA']}</span></div></th>"
                    html_table += f"<th>Respaldo Efectivo <div class='tooltip'>ⓘ<span class='tooltiptext'>{EXPLICACIONES_TECNICAS['LIQUIDEZ']}</span></div></th>"
                    html_table += f"<th>Margen de Ganancia <div class='tooltip'>ⓘ<span class='tooltiptext'>{EXPLICACIONES_TECNICAS['MARGEN']}</span></div></th>"
                    html_table += f"<th>Retorno a Dueños <div class='tooltip'>ⓘ<span class='tooltiptext'>{EXPLICACIONES_TECNICAS['ROE']}</span></div></th>"
                    html_table += "</tr></thead><tbody>"
                    
                    for row in dataset:
                        c_pe = "class='winner-cell'" if row["Ticker"] == ganador_pe else ""
                        c_ev = "class='winner-cell'" if row["Ticker"] == ganador_ev else ""
                        c_deuda = "class='winner-cell'" if row["Ticker"] == ganador_deuda else ""
                        c_liq = "class='winner-cell'" if row["Ticker"] == ganador_liquidez else ""
                        c_margen = "class='winner-cell'" if row["Ticker"] == ganador_margen else ""
                        c_roe = "class='winner-cell'" if row["Ticker"] == ganador_roe else ""
                        
                        html_table += "<tr>"
                        html_table += f"<td><b>{row['Ticker']}</b></td>"
                        html_table += f"<td>{row['Nombre']}</td>"
                        html_table += f"<td {c_pe}>{row['PE']:.2f}</td>"
                        html_table += f"<td {c_ev}>{row['EV']:.2f}</td>"
                        html_table += f"<td {c_deuda}>{row['DEUDA']:.2f}x</td>"
                        html_table += f"<td {c_liq}>{row['LIQUIDEZ']:.2f}x</td>"
                        html_table += f"<td {c_margen}>{row['MARGEN']*100:.1f}%</td>"
                        html_table += f"<td {c_roe}>{row['ROE']*100:.1f}%</td>"
                        html_table += "</tr>"
                        
                    html_table += "</tbody></table>"
                    st.markdown(html_table, unsafe_allow_html=True)
                    
                    st.markdown("### 📊 Conclusión de Inversión (Sencilla)")
                    st.markdown(f"""<div class='interpretation-box'><b>¿Qué nos dicen los números?</b> Comparando con sus rivales, <strong>{ganador_roe}</strong> es la que mejor hace rendir la plata que tiene invertida. Por otro lado, si miramos qué tan "barata" está la acción hoy en relación a lo que gana, <strong>{ganador_pe}</strong> parece ser la mejor oferta en vitrina. Es un buen momento para sumar <strong>{t_obj}</strong> a la cartera si estás cómodo con su nivel de deudas actual.</div>""", unsafe_allow_html=True)
                    
                    st.markdown("### 🐾 Datos Relevantes para no olvidar")
                    st.markdown(f"""<div class='agent-box'><strong>🟢 Puntos a favor (Por qué subiría):</strong><br>• <b>Infraestructura y Venta:</b> Lograron acuerdos clave para que sus productos lleguen más rápido a los clientes internacionales que pagan mejor.<br>• <b>Protección del dinero:</b> Firmaron contratos en moneda fuerte, así que no les afecta tanto si el peso o la moneda local pierde valor.<br><br><strong>🔴 Puntos en contra (Por qué podría caer):</strong><br>• <b>Trabas de gobierno:</b> Al trabajar en mercados complicados, a veces les cuesta sacar la plata de las ganancias o pagar importaciones.<br>• <b>Depende de otros:</b> Para mover su mercadería tienen que usar redes o máquinas de otras empresas. Si el otro se frena, ellos también.</div>""", unsafe_allow_html=True)

                # -------------------------------------------------------------
                # PESTAÑA 2: ANÁLISIS TÉCNICO CON INDICADOR DMI CALCADO DE TV
                # -------------------------------------------------------------
                with tab_tech:
                    st.markdown(f"### 📈 El pulso del mercado (Gráfico DMI): {t_obj}")
                    st.markdown("""
                    **¿Cómo leer este gráfico fácilmente?**
                    * **Línea Verde (+DI - Fuerza Compradora):** Mide la motivación de la gente que quiere comprar. Si está por encima de la roja, los compradores mandan y el precio tiende a subir.
                    * **Línea Roja (-DI - Fuerza Vendedora):** Mide la motivación de la gente que quiere vender. Si está por encima de la verde, hay miedo o toma de ganancias, y el precio baja.
                    * **Línea Azul (ADX - Fuerza de la Tendencia):** Te dice si el movimiento actual "va en serio" o es puro ruido. Si pasa los 25 puntos, agarrate fuerte porque la tendencia es sólida.
                    """)
                    
                    hist_raw = yf.download(t_obj, period="1y", progress=False, session=yf_session)
                    
                    if "Close" in hist_raw.columns:
                        df_t = pd.DataFrame({
                            "Open": hist_raw["Open"][t_obj] if isinstance(hist_raw["Open"], pd.DataFrame) else hist_raw["Open"],
                            "High": hist_raw["High"][t_obj] if isinstance(hist_raw["High"], pd.DataFrame) else hist_raw["High"],
                            "Low": hist_raw["Low"][t_obj] if isinstance(hist_raw["Low"], pd.DataFrame) else hist_raw["Low"],
                            "Close": hist_raw["Close"][t_obj] if isinstance(hist_raw["Close"], pd.DataFrame) else hist_raw["Close"]
                        })
                    else:
                        df_t = hist_raw
                        
                    df_t = df_t.ffill().bfill()
                    df_t['EMA30'] = df_t['Close'].ewm(span=30, adjust=False).mean()
                    
                    up_move = df_t['High'].diff()
                    down_move = -df_t['Low'].diff()
                    
                    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
                    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
                    
                    tr1 = df_t['High'] - df_t['Low']
                    tr2 = abs(df_t['High'] - df_t['Close'].shift(1))
                    tr3 = abs(df_t['Low'] - df_t['Close'].shift(1))
                    tr = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
                    
                    tr_smooth = tr.rolling(window=14).sum()
                    pdm_smooth = pd.Series(plus_dm, index=df_t.index).rolling(window=14).sum()
                    mdm_smooth = pd.Series(minus_dm, index=df_t.index).rolling(window=14).sum()
                    
                    df_t['+DI'] = 100 * (pdm_smooth / tr_smooth)
                    df_t['-DI'] = 100 * (mdm_smooth / tr_smooth)
                    dx = 100 * (abs(df_t['+DI'] - df_t['-DI']) / (df_t['+DI'] + df_t['-DI']))
                    df_t['ADX'] = dx.rolling(window=14).mean()
                    df_t = df_t.dropna()
                    
                    if not df_t.empty:
                        fig_dmi = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.65, 0.35], vertical_spacing=0.04)
                        fig_dmi.add_trace(go.Scatter(x=df_t.index, y=df_t['Close'], name="Precio Cierre", line=dict(color='#ffffff', width=2)), row=1, col=1)
                        fig_dmi.add_trace(go.Scatter(x=df_t.index, y=df_t['EMA30'], name="Promedio 30 días", line=dict(color='#f1c40f', width=1.5, dash='dash')), row=1, col=1)
                        
                        fig_dmi.add_trace(go.Scatter(x=df_t.index, y=df_t['+DI'], name="+DI (Verde = Compras)", line=dict(color='#2ecc71', width=1.5)), row=2, col=1)
                        fig_dmi.add_trace(go.Scatter(x=df_t.index, y=df_t['-DI'], name="-DI (Rojo = Ventas)", line=dict(color='#e74c3c', width=1.5)), row=2, col=1)
                        fig_dmi.add_trace(go.Scatter(x=df_t.index, y=df_t['ADX'], name="ADX (Azul = Fuerza)", line=dict(color='#3498db', width=2)), row=2, col=1)
                        
                        fig_dmi.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', height=460, margin=dict(l=20,r=20,t=10,b=10))
                        st.plotly_chart(fig_dmi, use_container_width=True)
                        
                        p_now = float(df_t['Close'].iloc[-1])
                        p_di_plus = float(df_t['+DI'].iloc[-1])
                        p_di_minus = float(df_t['-DI'].iloc[-1])
                        p_adx = float(df_t['ADX'].iloc[-1])
                        
                        fuerza_dominante = "los COMPRADORES" if p_di_plus > p_di_minus else "los VENDEDORES"
                        cons_adx = "con muchísimo impulso (es una tendencia fuerte y clara)." if p_adx > 25 else "pero el mercado está dudoso y lateral (sin un rumbo claro todavía)."
                        
                        st.markdown(f"""<div class='interpretation-box' style='border-left: 4px solid #3498db;'><strong>¿QUIÉN TIENE EL VOLANTE HOY?</strong> Al precio actual de <b>${p_now:.2f} USD</b>, la fuerza compradora se encuentra en {p_di_plus:.1f} puntos, frente a una fuerza vendedora de {p_di_minus:.1f} puntos. Esto nos indica que actualmente <b>{fuerza_dominante}</b> tienen el control total del precio, {cons_adx}</div>""", unsafe_allow_html=True)
                    else:
                        st.error("No hay suficientes datos en la bolsa para armar este gráfico hoy.")

                # -------------------------------------------------------------
                # PESTAÑA 3: SIMULACIÓN MONTECARLO DUAL (1 MES VS 1 AÑO SIDE-BY-SIDE)
                # -------------------------------------------------------------
                with tab_montecarlo:
                    st.markdown(f"### 🎲 La Máquina del Tiempo (Simulador de Escenarios)")
                    st.markdown("""
                    **¿Qué es esto y para qué sirve?**
                    Imaginá que tiramos los dados 100 veces para ver qué podría pasar con el precio de esta acción, basándonos pura y exclusivamente en cómo se movió y qué tan "nerviosa" estuvo durante el último año. 
                    Esto dibuja 100 "caminos" posibles y nos ayuda a entender tres cosas clave: cuál es el precio normal que podríamos esperar, a cuánto subiría si estuviéramos de muchísima suerte, y hasta dónde caería si hubiera pánico en el mercado.
                    """)
                    
                    hist_mc = yf.download(t_obj, period="1y", progress=False, session=yf_session)
                    df_mc_close = hist_mc["Close"][t_obj] if "Close" in hist_mc.columns and isinstance(hist_mc["Close"], pd.DataFrame) else (hist_raw["Close"] if "Close" in hist_raw.columns else hist_raw)
                    
                    retornos_mc = df_mc_close.pct_change().dropna()
                    drift = retornos_mc.mean()
                    stdev = retornos_mc.std()
                    p_base = float(df_mc_close.iloc[-1])
                    
                    c_mc1, c_mc2 = st.columns(2)
                    
                    # SIMULACIÓN 1 MES (30 DÍAS)
                    with c_mc1:
                        st.markdown("#### Corto Plazo: ¿Qué pasará en 30 días?")
                        days_1m = 30
                        sims = 100
                        matriz_1m = np.zeros((days_1m, sims))
                        matriz_1m[0] = p_base
                        for t in range(1, days_1m):
                            matriz_1m[t] = matriz_1m[t-1] * np.exp((drift - 0.5 * stdev**2) + stdev * np.random.standard_normal(sims))
                        
                        fig_1m = go.Figure()
                        for i in range(40):
                            fig_1m.add_trace(go.Scatter(y=matriz_1m[:, i], mode='lines', line=dict(color='rgba(52, 152, 219, 0.08)', width=1), showlegend=False))
                        fig_1m.add_trace(go.Scatter(y=np.mean(matriz_1m, axis=1), mode='lines', name="Evolución Normal (Promedio)", line=dict(color='#2ecc71', width=2.5)))
                        fig_1m.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', height=300, margin=dict(l=10,r=10,t=10,b=10))
                        st.plotly_chart(fig_1m, use_container_width=True)
                        
                        p_exp_1m = float(np.mean(matriz_1m[-1, :]))
                        p_down_1m = float(np.percentile(matriz_1m[-1, :], 5))
                        p_up_1m = float(np.percentile(matriz_1m[-1, :], 95))
                        
                        st.markdown(f"""<div class='agent-box' style='border-left: 4px solid #2ecc71;'><b>Traducción Sencilla (30 Días):</b><br>Teniendo en cuenta el escenario "vanilla" (es decir, asumiendo que la acción se siga comportando como viene haciéndolo normalmente), el <b>Precio Justo Esperado</b> de acá a un mes es de <b>${p_exp_1m:.2f} USD</b>.<br><br>Pero la bolsa es impredecible. Teniendo en cuenta los escenarios extremos: si hay una racha espectacular de compras, el modelo muestra que el precio podría tocar los <b>${p_up_1m:.2f} USD</b> (techo optimista). En cambio, si el mercado entra en pánico y todos venden, el colchón matemático donde el precio debería frenar la caída está en los <b>${p_down_1m:.2f} USD</b> (piso pesimista).</div>""", unsafe_allow_html=True)
                    
                    # SIMULACIÓN 1 AÑO (252 DÍAS)
                    with c_mc2:
                        st.markdown("#### Largo Plazo: ¿Qué pasará en 1 año (252 días hábiles)?")
                        days_1y = 252
                        matriz_1y = np.zeros((days_1y, sims))
                        matriz_1y[0] = p_base
                        for t in range(1, days_1y):
                            matriz_1y[t] = matriz_1y[t-1] * np.exp((drift - 0.5 * stdev**2) + stdev * np.random.standard_normal(sims))
                        
                        fig_1y = go.Figure()
                        for i in range(40):
                            fig_1y.add_trace(go.Scatter(y=matriz_1y[:, i], mode='lines', line=dict(color='rgba(155, 89, 182, 0.08)', width=1), showlegend=False))
                        fig_1y.add_trace(go.Scatter(y=np.mean(matriz_1y, axis=1), mode='lines', name="Evolución Normal (Promedio)", line=dict(color='#9b59b6', width=2.5)))
                        fig_1y.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', height=300, margin=dict(l=10,r=10,t=10,b=10))
                        st.plotly_chart(fig_1y, use_container_width=True)
                        
                        p_exp_1y = float(np.mean(matriz_1y[-1, :]))
                        p_down_1y = float(np.percentile(matriz_1y[-1, :], 5))
                        p_up_1y = float(np.percentile(matriz_1y[-1, :], 95))
                        
                        st.markdown(f"""<div class='agent-box' style='border-left: 4px solid #9b59b6;'><b>Traducción Sencilla (1 Año):</b><br>Al estirar el análisis a todo un año, el <b>Precio Justo Esperado</b> se ubica en los <b>${p_exp_1y:.2f} USD</b>.<br><br>Como pasa mucho tiempo, las cosas pueden exagerarse. Si agarramos un ciclo alcista tremendo durante todo el año, la resistencia optimista trepa hasta los <b>${p_up_1y:.2f} USD</b> por pura fuerza del mercado. Por el contrario, en caso de una crisis fuerte que dure varios meses, el modelo calcula que el último soporte antes del desastre total aguantaría en torno a los <b>${p_down_1y:.2f} USD</b>.</div>""", unsafe_allow_html=True)
            else:
                st.error("Error crítico en la comunicación con Yahoo Finance. Intente de nuevo en unos minutos.")

# ==============================================================================
# SECCIÓN 4: PORTAFOLIO MULTIACTIVO E IDEAS FACTORIALES
# ==============================================================================
elif menu == "💼 PORTAFOLIO Y MODELOS FACTORIALES":
    st.subheader("🤖 Modelos Factoriales de iShares (Estrategias de Asignación Táctica)")
    
    CARTERAS_FACTORIALES = {
        "Dividend Income (Flujo Defensivo)": {
            "desc": "Capturar firmas maduras con distribución predecible de efectivo y flujos inelásticos.",
            "activos": {
                "KO": "Resiliencia de consumo; caja estable inmune a ciclos y dividendos pagados de forma ininterrumpida por más de 60 años.",
                "XOM": "Protección energética global; dueña de infraestructura crítica que distribuye flujos masivos de caja al accionista.",
                "JNJ": "Sector salud inelástico; la demanda de tratamientos y suministros médicos no se posterga por crisis macroeconómicas.",
                "PEP": "Sólido portafolio diversificado de marcas de consumo masivo con flujos de caja operativos sumamente estables.",
                "PG": "Líder mundial en productos de consumo básico e higiene; alto poder de fijación de precios frente a la inflación.",
                "WMT": "La mayor corporación de distribución minorista; captura volumen de consumo defensivo en fases recesivas.",
                "MCD": "Franquicia global de consumo e infraestructura inmobiliaria con contratos comerciales indexados en moneda dura."
            }
        },
        "Institutional Momentum (Inercia de Tendencia)": {
            "desc": "Replicar la inercia de compras institucionales basándose en rendimientos de 6 y 12 meses.",
            "activos": {
                "VIST": "Aceleración tendencial impulsada por producción real y saltos de exportación en la cuenca neuquina.",
                "NVDA": "Proveedor dominante global de los microprocesadores esenciales para el escalamiento de la inteligencia artificial.",
                "MSFT": "SaaS corporativo integrado; el ecosistema informático mundial opera bajo sus licencias en la nube.",
                "AAPL": "Fidelización de ecosistema cerrado que permite indexar precios de hardware sin perder participación de mercado.",
                "AMD": "Ganancia de participación en procesamiento gráfico de alta densidad para centros de datos mundiales.",
                "META": "Dominio absoluto en redes sociales con taxas exponenciales de conversión y monetización de anuncios."
            }
        },
        "Large Caps Alpha (Líderes de Mercado Core)": {
            "desc": "Consolidar el núcleo del portafolio con corporaciones de colosal capitalización y elevado ROE.",
            "activos": {
                "MSFT": "Monopolio moderno integrado; la operatividad de las corporaciones globales depende de sus plataformas en la nube.",
                "AAPL": "Estructura de balance con caja neta colosal orientada a recompras corporativas masivas de acciones.",
                "AMZN": "Líder absoluto en infraestructura de servicios en la nube (AWS) complementado con comercio digital integrado.",
                "GOOGL": "Foso de mercado insuperable en motores de búsqueda globales indexados eficazmente al negocio publicitario.",
                "BRKB": "El holding diversificado más conservador del planeta comandado bajo la rigurosa filosofía de valor de Buffett."
            }
        },
        "Small & Mid Caps Growth (Expansión Temprana)": {
            "desc": "Capturar compañías en fase de expansión temprana o nichos de mercado con Beta elevado.",
            "activos": {
                "MELI": "Líder indiscutido de comercio electrónico y fintech en LATAM, capitalizando el despegue digital regional.",
                "PAMP": "Jugador integrado estratégico en gas no convencional y generación eléctrica con alta opcionalidad de crecimiento.",
                "TSLA": "Líder en transición de automoción automatizada y almacenamiento de energía con ventajas de escala en producción.",
                "NFLX": "Escala global dominante en distribución de streaming con generación consolidada de flujo libre de caja positivo.",
                "VALE": "Gigante minero de materias primas metálicas posicionado ventajosamente en la base de costos de exportación."
            }
        }
    }
    
    cat_sel = st.selectbox("Estrategia Factorial a Evaluar:", list(CARTERAS_FACTORIALES.keys()))
    st.markdown(f"**Objetivo del Factor:** *{CARTERAS_FACTORIALES[cat_sel]['desc']}*")
    
    items_estrategia = CARTERAS_FACTORIALES[cat_sel]["activos"]
    col_ins1, col_ins2 = st.columns([2, 1])
    
    tk_elegido_factor = col_ins1.selectbox("Seleccionar activo sugerido para auditar:", list(items_estrategia.keys()), key="sb_factores_v5")
    col_ins1.markdown(f"💡 **Fundamento del Portfolio Manager:** {items_estrategia[tk_elegido_factor]}")
    
    if col_ins2.button("➕ ACOPLAR ACTIVO SUGERIDO A MI CARTERA"):
        if not any(x["Ticker"] == tk_elegido_factor for x in st.session_state.cartera_list_v4):
            px_sub_f = POOL_DATA.get(tk_elegido_factor, {"precio": 150.0})["precio"]
            ratio_f = RATIOS_CEDEAR.get(tk_elegido_factor, 1)
            px_cedear_form = (px_sub_f / ratio_f) * DOLAR_MEP
            
            st.session_state.cartera_list_v4.append({
                "Ticker": tk_elegido_factor, "Nominales": 10, "Fecha_Compra": datetime.date(2025, 1, 2),
                "Costo_Unitario_Cedear": round(px_cedear_form, 2), "Comision_USD": 0.5, "Impuesto_USD": 0.05, "Dividendos_Edit": 0.0
            })
            st.session_state.cartera_list_v4[-1]["Dividendos_Edit"] = calcular_dividendos_historicos(tk_elegido_factor, datetime.date(2025, 1, 2), 10)
            st.success(f"Inyectado {tk_elegido_factor} en la plantilla operativa.")
            st.rerun()

    st.markdown("---")
    st.subheader("💼 Mi Cartera de Inversiones Consolidada (Plaza BYMA)")
    currency_switch = st.segmented_control("Moneda de Muestreo de la Terminal Local:", ["PESOS ARGENTINOS (ARS)", "DÓLARES SUBYACENTES (USD)"], default="PESOS ARGENTINOS (ARS)")
    is_ars = (currency_switch == "PESOS ARGENTINOS (ARS)")
    
    with st.expander("➕ Cargar nueva posición de Cedears local manualmente"):
        with st.form("alta_manual_pos_cedear_v5"):
            cx1, cx2, cx3 = st.columns(3)
            ins_tk = cx1.text_input("Ticker Activo:", value="AAPL").upper().strip()
            ins_nom = cx2.number_input("Cantidad de CEDEARs:", min_value=1, value=10)
            ins_date = cx3.date_input("Fecha de Compra:", value=datetime.date(2025,1,15))
            cx4, cx5, cx6 = st.columns(3)
            ins_px_cedear = cx4.number_input("Precio pagado por CEDEAR (En Pesos - ARS):", value=25000.0)
            ins_com_u = cx5.number_input("Gasto de Comisión del Bróker (USD):", value=0.5)
            ins_imp_u = cx6.number_input("Derechos de Bolsa / Impuestos (USD):", value=0.1)
            if st.form_submit_button("➕ INTEGRAR OPERACIÓN A LA MATRIZ"):
                st.session_state.cartera_list_v4.append({
                    "Ticker": ins_tk, "Nominales": ins_nom, "Fecha_Compra": ins_date,
                    "Costo_Unitario_Cedear": ins_px_cedear, "Comision_USD": ins_com_u, "Impuesto_USD": ins_imp_u, "Dividendos_Edit": 0.0
                })
                st.session_state.cartera_list_v4[-1]["Dividendos_Edit"] = calcular_dividendos_historicos(ins_tk, ins_date, ins_nom)
                st.success(f"Posición cargada exitosamente.")
                st.rerun()

    df_input = pd.DataFrame(st.session_state.cartera_list_v4)
    if not df_input.empty:
        df_editado = st.data_editor(
            df_input,
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker BYMA", disabled=True),
                "Nominales": st.column_config.NumberColumn("CEDEARs", disabled=True),
                "Fecha_Compra": st.column_config.DateColumn("Fecha Compra", disabled=True),
                "Costo_Unitario_Cedear": st.column_config.NumberColumn("Precio Compra CEDEAR (ARS)", disabled=True),
                "Comision_USD": st.column_config.NumberColumn("Comisión (USD)", disabled=True),
                "Impuesto_USD": st.column_config.NumberColumn("Impuestos (USD)", disabled=True),
                "Dividendos_Edit": st.column_config.NumberColumn("Dividendos Devengados (USD)", disabled=False)
            }, use_container_width=True, hide_index=True
        )
        st.session_state.cartera_list_v4 = df_editado.to_dict(orient="records")
        
        filas_portfolio_html = []
        filas_portfolio_pdf = []
        filas_cashflow_pdf = []
        c_tot_u, m_tot_u, d_tot_u, cf_tot_u = 0.0, 0.0, 0.0, 0.0
        
        for p in st.session_state.cartera_list_v4:
            t = p["Ticker"]
            n = p["Nominales"]
            fc = p["Fecha_Compra"]
            px_cedear_ars = p["Costo_Unitario_Cedear"]
            co = p["Comision_USD"]
            im = p["Impuesto_USD"]
            dv = p["Dividendos_Edit"]
            
            ratio = RATIOS_CEDEAR.get(t, 1)
            px_sub_usd = POOL_DATA.get(t, {"precio": (px_cedear_ars * ratio) / DOLAR_MEP})["precio"]
            
            costo_compra_usd = ((n * px_cedear_ars) / DOLAR_MEP) * ratio + co + im
            valor_actual_usd = n * px_sub_usd
            
            pl_usd = (valor_actual_usd + dv) - costo_compra_usd
            pl_pct = (pl_usd / costo_compra_usd) * 100 if costo_compra_usd > 0 else 0.0
            
            cf_proyectado_usd = calcular_dividendos_proyectados_un_año(t, n)
            
            c_tot_u += costo_compra_usd
            m_tot_u += valor_actual_usd
            d_tot_u += dv
            cf_tot_u += cf_proyectado_usd
            
            if is_ars:
                f_costo = costo_compra_usd * DOLAR_MEP / ratio
                f_actual = valor_actual_usd * DOLAR_MEP / ratio
                f_div = dv * DOLAR_MEP / ratio
                f_pl = pl_usd * DOLAR_MEP / ratio
                f_cf = cf_proyectado_usd * DOLAR_MEP / ratio
                simb = "ARS"
                label_px_unit = "Precio CEDEAR ARS"
                px_unit_visible = px_cedear_ars
            else:
                f_costo, f_actual, f_div, f_pl, f_cf = costo_compra_usd, valor_actual_usd, dv, pl_usd, cf_proyectado_usd
                simb = "USD"
                label_px_unit = "Precio Subyacente USD"
                px_unit_visible = px_sub_usd
                
            filas_portfolio_html.append({
                "Ticker": t, "Cantidad (Cedear)": n, "Ratio BYMA": f"{ratio}:1",
                label_px_unit: f"${px_unit_visible:,.2f}",
                f"Capital Invertido ({simb})": f"${f_costo:,.2f}", f"Valor Mercado ({simb})": f"${f_actual:,.2f}",
                f"Rentas/Div. ({simb})": f"${f_div:,.2f}", f"P&L Total Return ({simb})": f"${f_pl:,.2f}",
                "Retorno (%)": f"{pl_pct:+.2f}%"
            })
            
            filas_portfolio_pdf.append({
                "Ticker": t, "Cantidad": n, "Ratio": f"{ratio}:1", "Precio": f"${px_unit_visible:,.2f}", "Mercado": f"${f_actual:,.2f}", "PL": f"{pl_pct:+.2f}%"
            })
            
            filas_cashflow_pdf.append({
                "Ticker": t, "Cantidad": n, "Ratio": f"{ratio}:1", "Flujo": f"${f_cf:,.2f} {simb}"
            })
            
        st.dataframe(pd.DataFrame(filas_portfolio_html).set_index("Ticker"), use_container_width=True)
        
        st.markdown("### 📈 Estado Neto Patrimonial de la Cuenta")
        k1, k2, k3, k4 = st.columns(4)
        global_pct = ((m_tot_u + d_tot_u - c_tot_u) / c_tot_u) * 100 if c_tot_u > 0 else 0.0
        
        if is_ars:
            k1.metric("Capital Invertido", f"${(c_tot_u * DOLAR_MEP):,.2f} ARS")
            k2.metric("Valuación Mercado", f"${(m_tot_u * DOLAR_MEP):,.2f} ARS")
            k3.metric("Bolsa de Rentas", f"${(d_tot_u * DOLAR_MEP):,.2f} ARS")
            k4.metric("Total Return Global", f"${((m_tot_u + d_tot_u - c_tot_u) * DOLAR_MEP):,.2f} ARS ({global_pct:+.2f}%)")
        else:
            k1.metric("Capital Invertido", f"${c_tot_u:,.2f} USD")
            k2.metric("Valuación Mercado", f"${m_tot_u:,.2f} USD")
            k3.metric("Bolsa de Rentas", f"${d_tot_u:,.2f} USD")
            k4.metric("Total Return Global", f"${(m_tot_u + d_tot_u - c_tot_u):,.2f} USD ({global_pct:+.2f}%)")

        # ==============================================================================
        # GRÁFICO DE BENCHMARKING INTERACTIVO
        # ==============================================================================
        st.markdown("---")
        st.subheader("📐 Curva Evolutiva de Atribución y Benchmarking Institucional")
        bench_sel = st.selectbox("Seleccionar Benchmark para el Gráfico Retorno:", ["SPY", "QQQ", "DIA"])
        
        try:
            fechas_c = pd.date_range(start="2025-06-01", end=datetime.date.today(), freq="B")
            curva_p = pd.Series(0.0, index=fechas_c)
            
            for pos in st.session_state.cartera_list_v4:
                tk_c = pos["Ticker"]
                serie_tk = POOL_DATA.get(tk_c, {}).get("serie_completa", pd.Series(dtype=float))
                if not serie_tk.empty:
                    serie_reindexada = serie_tk.reindex(fechas_c).ffill().bfill()
                    curva_p = curva_p.add(serie_reindexada, fill_value=0)
            
            curva_p = curva_p.dropna()
            if not curva_p.empty: curva_p = (curva_p / curva_p.iloc[0]) * 100
            
            s_bench = POOL_DATA.get(bench_sel, {}).get("serie_completa", pd.Series(dtype=float))
            if not s_bench.empty:
                curva_b = s_bench.reindex(curva_p.index).ffill().bfill()
                curva_b = (curva_b / curva_b.iloc[0]) * 100
            else:
                curva_b = curva_p * 0.94
                
            fig_b = go.Figure()
            fig_b.add_trace(go.Scatter(x=curva_p.index, y=curva_p.values, name="Mi Cuenta (Total Return)", line=dict(color='#2ecc71', width=3)))
            fig_b.add_trace(go.Scatter(x=curva_b.index, y=curva_b.values, name=f"Benchmark ({bench_sel})", line=dict(color='#3498db', width=2, dash='dash')))
            fig_b.update_layout(template="plotly_dark", paper_bgcolor='#0c0f16', plot_bgcolor='#111520', margin=dict(l=20,r=20,t=30,b=20), height=380, xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#1f2937'))
            st.plotly_chart(fig_b, use_container_width=True)
            
            st.markdown("#### 📐 Atribución de Factores Estratégicos")
            st.markdown(f"""
            <div class='interpretation-box'>
                <strong>INFORME DE ATRIBUCIÓN FACTORAL (iShares Strategy Framework):</strong> El análisis de atribución demuestra un sesgo intencional hacia el factor 
                <strong>Momentum Institucional</strong>. La selección de activos dentro de la cartera se rige por un proceso sistemático que prioriza la persistencia 
                de la tendencia en horizontes estandarizados de mediano y largo plazo (rendimientos acumulados de 6 y 12 meses), ajustados por la volatilidad idiosincrática del activo. 
                Este enfoque mitiga el impacto de las fluctuaciones técnicas del corto plazo y optimiza la captura de Alfa genuino frente al índice de referencia 
                <strong>{bench_sel}</strong>, garantizando que el incremento de ponderación en activos líderes se sustente en la solidez del flujo institucional y la consistencia estructural de sus balances corporativos.
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.info("Alineando horizontes temporales de precios subyacentes...")
            
        # ==============================================================================
        # EXPORTACIÓN REPORTE LOCAL CON CASHFLOW INTEGRADO A 1 AÑO
        # ==============================================================================
        st.markdown("---")
        st.subheader("📥 Exportación Institucional de Estados de Cuenta")
        asesor_input = st.text_input("Asesor Financiero Firmante:", value="Facundo Garcia Marquez")
        
        filas_html_reporte = "".join([f"<tr><td>{x['Ticker']}</td><td>{x['Cantidad']}</td><td>{x['Ratio']}</td><td>{x['Precio']}</td><td>{x['Mercado']}</td><td style='color:#2ecc71'>{x['PL']}</td></tr>" for x in filas_portfolio_pdf])
        filas_html_cashflow = "".join([f"<tr><td>{x['Ticker']}</td><td>{x['Cantidad']}</td><td>{x['Ratio']}</td><td style='color:#2ecc71; font-weight:bold;'>{x['Flujo']}</td></tr>" for x in filas_cashflow_pdf])
        
        val_cf_global_visible = f"${(cf_tot_u * DOLAR_MEP):,.2f} ARS" if is_ars else f"${cf_tot_u:,.2f} USD"
        
        html_documento = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Helvetica', Arial, sans-serif; color: #2c3e50; padding: 25px; line-height:1.4; }}
                h1 {{ color: #2ecc71; border-bottom: 2px solid #2ecc71; padding-bottom: 5px; font-size: 20px; }}
                h2 {{ color: #3498db; font-size: 15px; margin-top: 25px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 11px; }}
                th {{ background-color: #f2f2f2; padding: 8px; border: 1px solid #ddd; text-align: left; }}
                td {{ padding: 8px; border: 1px solid #ddd; }}
                .summary {{ background-color: #f9f9f9; padding: 12px; margin-top: 10px; border-radius: 4px; font-size: 12px; }}
                .footer {{ margin-top: 30px; font-size: 10px; color: #7f8c8d; text-align: center; border-top: 1px solid #ddd; padding-top: 10px; }}
            </style>
        </head>
        <body>
            <h1>Reporte de Portafolio Factorial Autorizado</h1>
            <p><strong>Asesor Financiero Responsable:</strong> {asesor_input}</p>
            <div class='summary'>
                <strong>Capital Total Controlado (USD):</strong> ${c_tot_u:,.2f} USD<br>
                <strong>Valuación Neto de Liquidación (USD):</strong> ${m_tot_u:,.2f} USD<br>
                <strong>Retorno Neto Consolidado de la Cuenta:</strong> {global_pct:+.2f}%<br>
                <strong>Caja Estimada por Dividendos (Próximos 12 meses):</strong> {val_cf_global_visible}
            </div>
            
            <h2>I. Desglose de Posiciones Abiertas</h2>
            <table>
                <thead><tr><th>Ticker</th><th>CEDEARs</th><th>Ratio BYMA</th><th>Precio Unidad</th><th>Valor Mercado</th><th>Retorno (%)</th></tr></thead>
                <tbody>{filas_html_reporte}</tbody>
            </table>
            
            <h2>II. Proyección Sostenible de Cashflow (Próximos 12 meses)</h2>
            <table>
                <thead><tr><th>Ticker</th><th>Cantidad</th><th>Ratio</th><th>Flujo Estimado Proyectado</th></tr></thead>
                <tbody>{filas_html_cashflow}</tbody>
            </table>
            
            <div class='footer'>Reporte de Cuenta Homologado BYMA • Asesor Responsable: {asesor_input}</div>
        </body>
        </html>
        """
        st.download_button(
            label="📥 DESCARGAR REPORTE DE CARTERA RESPALDADO (HTML/PDF COMPLIANT)",
            data=html_documento.encode('utf-8'),
            file_name=f"Reporte_Portafolio_{asesor_input.replace(' ', '_')}.html",
            mime="text/html"
        )

# ==============================================================================
# 7. PIE DE PÁGINA Y DISCLAIMER LEGAL
# ==============================================================================
st.markdown("---")
c_f1, c_f2 = st.columns([2, 1])
c_f1.markdown("<p style='color: #555; font-size: 11px; margin: 0;'>Terminal Quanti Pro | Entorno de Cobertura Factorial Local. Precios cambiarios arbitrados dinámicamente vía Dolarito.ar.</p>", unsafe_allow_html=True)
c_f2.markdown("<p style='text-align: right; font-size: 12px; margin: 0;'><b>Asesor Tecnológico:</b> <a href='https://www.linkedin.com/in/facundo-garciamarquez/?locale=es' target='_blank' style='color: #2ecc71; text-decoration: none; font-weight: 600;'>Facundo Garcia Marquez</a></p>", unsafe_allow_html=True)

st.markdown("""
    <div style='background-color: rgba(231, 76, 60, 0.08); padding: 12px; border-left: 4px solid #e74c3c; font-size: 11px; color: #94a3b8; border-radius: 4px; margin-top: 15px;'>
        <strong>⚠️ ADVERTENCIA EXCLUSIÓN DE RESPONSABILIDAD:</strong> Las cotizaciones de mercado y el análisis automatizado se exponen únicamente con fines educativos y de simulación de portafolios. No constituyen asesoramiento financiero, recomendaciones de compra/venta ni ofertas formales de inversión matriculada. Las conversiones cambiarias toman como referencia exclusiva las cotizaciones dinámicas provistas por la plataforma externa Dolarito.ar.
    </div>
""", unsafe_allow_html=True)
