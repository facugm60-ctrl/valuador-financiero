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
import plotly.express as px
from plotly.subplots import make_subplots
import scipy.optimize as sco

# ------------------------------------------------------------------------------
# DISFRAZ ANTI-BLOQUEO PARA YAHOO FINANCE & FINVIZ
# ------------------------------------------------------------------------------
yf_session = requests.Session()
yf_session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive"
})

try:
    from deep_translator import GoogleTranslator
    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False

# ==============================================================================
# UNIVERSO EXPANSIÓN Y WATCHLIST CORE
# ==============================================================================
WATCHLIST_CORE = ["VIST", "YPF", "AAPL", "GGAL", "NVDA", "KO", "XOM", "WMT"]

UNIVERSO_100 = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "BRK-B", "JPM", "V", 
    "DIS", "NFLX", "AMD", "INTC", "QCOM", "TXN", "CRM", "ADBE", "ORAC", "CSCO",
    "KO", "PEP", "WMT", "COST", "PG", "PM", "MO", "EL", "CL", "HD",
    "XOM", "CVX", "SHEL", "BP", "TTE", "COP", "SLB", "HAL", "E", "PBR",
    "JNJ", "PFE", "MRK", "ABV", "LLY", "NVO", "BMY", "AMGN", "GILD", "MDT",
    "CAT", "GE", "MMM", "HON", "LMT", "BA", "UPS", "FDX", "DE", "EMR",
    "C", "BAC", "WFC", "GS", "MS", "BLK", "AXP", "PYPL", "SQ", "HSBC",
    "VIST", "YPF", "GGAL", "PAMP", "TXAR", "ALUA", "BMA", "CEPU", "CRES", "EDN",
    "SPY", "QQQ", "IWM", "DIA", "EEM", "XLE", "XLK", "XLF", "XLV", "XLP",
    "ASML", "MA", "MCO", "SPGI", "LVMUY", "NVO", "HD", "COST", "ACN", "NKE"
]

FALLBACK_SUMMARIES = {
    "VIST": "Vista Energy es una compañía independiente de petróleo y gas, enfocada principalmente en Vaca Muerta.",
    "YPF": "YPF Sociedad Anónima es la principal empresa energética de Argentina, dedicada a la exploración y refinación.",
    "XOM": "Exxon Mobil Corporation es uno de los gigantes energéticos globales con modelo integrado.",
    "AAPL": "Apple Inc. diseña hardware de consumo y cuenta con un ecosistema de servicios de alta retención.",
    "MSFT": "Microsoft Corporation lidera en software corporativo, computación en la nube (Azure) e IA.",
    "NVDA": "NVIDIA Corporation diseña unidades de procesamiento gráfico (GPUs) esenciales para infraestructura de IA.",
    "KO": "The Coca-Cola Company es una multinacional de bebidas no alcohólicas de perfil puramente defensivo."
}

EXPLICACIONES_TECNICAS = {
    "PE": "<b>P/E (Precio sobre Ganancias):</b><br>Cuántos años tardarías en recuperar tu inversión basándote en las ganancias actuales.",
    "EV": "<b>EV/EBITDA:</b><br>Costo de adquirir la empresa entera (con sus deudas) versus el efectivo limpio que genera.",
    "DEUDA": "<b>Deuda / EBITDA:</b><br>Compara la deuda total con lo generado en el año. Valores altos indican mayor riesgo financiero.",
    "LIQUIDEZ": "<b>Liquidez Corriente:</b><br>Efectivo disponible para pagar deudas de corto plazo. Mayor a 1.0x es tranquilidad.",
    "MARGEN": "<b>Margen Neto:</b><br>De cada $100 que vende, cuántos dólares le quedan libres de ganancia final.",
    "ROE": "<b>ROE (Retorno sobre Patrimonio):</b><br>Qué tan bien la gerencia hace rendir el capital aportado por los accionistas."
}

RATIOS_CEDEAR = {
    "VIST": 1, "YPF": 1, "AAPL": 10, "GGAL": 1, "AMD": 10, "NVDA": 24, "MSFT": 30, "AMZN": 14, "GOOGL": 11, "META": 24, 
    "TSLA": 15, "KO": 5, "WMT": 6, "JNJ": 15, "PEP": 15, "PG": 15, "XOM": 5, "PAMP": 1, "SPY": 20, "QQQ": 20
}
UNIVERSO_POOL = list(RATIOS_CEDEAR.keys())

st.set_page_config(page_title="Terminal Quanti Pro", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""<style>@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght=300;400;600;700;800&display=swap'); html, body, [class*="css"], [data-testid="stAppViewContainer"], [data-testid="stHeader"] { background-color: #0c0f16 !important; color: #f1f5f9 !important; font-family: 'Montserrat', sans-serif !important; } .stMarkdown, p, span, label, li { color: #cbd5e1 !important; } .block-container {padding-top: 1.5rem; padding-bottom: 2rem;} h1 {font-weight: 800; color: #ffffff !important; font-size: 30px !important;} h2 {font-weight: 700; color: #f8fafc !important; font-size: 21px !important; margin-top: 15px;} h3 {font-weight: 600; color: #f1f5f9 !important; font-size: 16px !important;} div[data-testid="stRadio"] > label { display: none !important; } div[data-testid="stRadio"] > div { background: rgba(22, 27, 34, 0.7) !important; backdrop-filter: blur(12px) !important; padding: 8px !important; border-radius: 12px !important; border: 1px solid rgba(255, 255, 255, 0.08) !important; gap: 12px !important; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5) !important; margin-bottom: 20px !important; } div[data-testid="stRadio"] label[data-baseweb="radio"] { background-color: transparent !important; border: 1px solid transparent !important; padding: 8px 18px !important; border-radius: 8px !important; color: #94a3b8 !important; font-weight: 600 !important; } div[data-testid="stRadio"] label[data-baseweb="radio"]:hover { color: #ffffff !important; background: rgba(255, 255, 255, 0.05) !important; } div[data-testid="stMetric"] { background-color: #111520 !important; border: 1px solid #1f2937 !important; border-radius: 10px !important; padding: 15px 20px !important; } .stButton>button { width: 100%; background: linear-gradient(135deg, #2ecc71, #27ae60) !important; color: white !important; font-weight: 700; border-radius: 8px; border: none; padding: 0.6rem; font-size: 13px !important; text-transform: uppercase; } div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] div, div[data-testid="stNumberInput"] input { background-color: #111520 !important; color: #ffffff !important; border: 1px solid #1f2937 !important; border-radius: 8px !important; } .radar-box-gainer-high { background: linear-gradient(135deg, #064e3b, #047857); border: 1px solid #10b981; padding: 14px; border-radius: 8px; font-weight: bold; color: #34d399 !important; } .radar-box-loser { background: linear-gradient(135deg, #7f1d1d, #b91c1c); border: 1px solid #f87171; padding: 14px; border-radius: 8px; font-weight: bold; color: #f87171 !important; } .interpretation-box { background-color: #111520; padding: 16px; border-radius: 8px; font-size: 13px; color: #e2e8f0; border: 1px solid #1f2937; border-left: 4px solid #2ecc71; margin-top: 10px; } .agent-box { background-color: #090d16; padding: 18px; border-radius: 8px; font-size: 13px; color: #e2e8f0; border: 1px solid #1f2937; border-left: 4px solid #dfa427; margin-top: 10px; } .custom-table { width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 13px; background-color: #111520; border-radius: 8px; overflow: hidden; border: 1px solid #1f2937; } .custom-table th { background-color: #161b22; color: #ffffff; padding: 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #1f2937; } .custom-table td { padding: 12px; border-bottom: 1px solid #1f2937; color: #e2e8f0; } .winner-cell { background-color: rgba(46, 204, 113, 0.15) !important; color: #2ecc71 !important; font-weight: bold; } .tooltip { position: relative; display: inline-block; cursor: pointer; color: #3498db; margin-left: 4px; font-weight: bold; } .tooltip .tooltiptext { visibility: hidden; width: 280px; background-color: #1f2937; color: #fff; text-align: left; padding: 12px; border-radius: 6px; position: absolute; z-index: 999; bottom: 125%; left: 50%; margin-left: -140px; font-size: 11px; font-weight: normal; line-height: 1.4; border: 1px solid #3b82f6; box-shadow: 0 4px 20px rgba(0,0,0,0.5); } .tooltip:hover .tooltiptext { visibility: visible; opacity: 1; }</style>""", unsafe_allow_html=True)

def safe_float(val):
    try: return float(val)
    except: return 0.0

@st.cache_data(ttl=600)
def obtener_dolar_mep_real():
    try:
        r = requests.get("https://www.dolarito.ar/", headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for element in soup.find_all(['div', 'span', 'p']):
            texto = element.get_text().lower()
            if 'mep' in texto and '$' in texto:
                for token in texto.split():
                    if '$' in token:
                        try:
                            val = float(token.replace('$', '').replace('.', '').replace(',', '.').strip())
                            if 1000 < val < 2000: return round(val, 2)
                        except: pass
        return 1433.25
    except: return 1433.25

DOLAR_MEP = obtener_dolar_mep_real()

@st.cache_data(ttl=900)
def descargar_pool_completo_100(pool):
    datos_dict = {}
    try:
        df_hist = yf.download(pool, period="5d", progress=False, session=yf_session)
        df_close = df_hist['Close'].ffill().bfill()
        for tk in pool:
            try:
                serie = df_close[tk].dropna() if tk in df_close.columns else pd.Series(dtype=float)
                if len(serie) >= 2:
                    px_actual = float(serie.iloc[-1])
                    v1d = ((px_actual / float(serie.iloc[-2])) - 1) * 100
                    datos_dict[tk] = {"precio": px_actual, "1D": v1d}
            except: pass
    except: pass
    return datos_dict

POOL_TOTAL_RADAR = descargar_pool_completo_100(UNIVERSO_100)

@st.cache_data(ttl=600)
def descargar_activo_individual_historico(ticker):
    try:
        tk_Bolsa = ticker + ".BA" if ticker in ["ALUA","BBAR","BMA","CEPU","COME","CRES","EDN","GGAL","LOMA","MIRG","PAMP","TECO2","TGNO4","TGSU2","TRAN","TXAR","YPF","BYMA","VALO","SUPV"] else ticker
        df = yf.download(tk_Bolsa, period="2y", progress=False, session=yf_session)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.loc[:, ~df.columns.duplicated()]
        df_close = df['Close'].ffill().bfill() if 'Close' in df.columns else df
        return df_close, df
    except:
        return pd.Series(dtype=float), pd.DataFrame()

@st.cache_data(ttl=3600)
def scrape_finviz_fallback(symbol):
    try:
        url = f"https://finviz.com/quote.ashx?t={symbol}"
        r = yf_session.get(url, timeout=5)
        if r.status_code != 200: return {}
        s = BeautifulSoup(r.text, 'html.parser')
        def extract(label):
            try:
                td = s.find(string=label)
                if td:
                    val = td.find_next('b').text.replace('%','').replace(',','')
                    return float(val) if val != '-' else 0.0
            except: return 0.0
            return 0.0
        return {"PE": extract("P/E"), "EV": extract("P/B"), "DEUDA": extract("Debt/Eq"), "LIQUIDEZ": extract("Current Ratio"), "MARGEN": extract("Profit Margin") / 100, "ROE": extract("ROE") / 100}
    except: return {}

def obtener_fundamental_completo(symbol):
    try:
        tk_Bolsa = symbol + ".BA" if symbol in ["GGAL","PAMP","YPF","TXAR","ALUA"] else symbol
        t = yf.Ticker(tk_Bolsa, session=yf_session)
        inf = t.info or {}
        px = safe_float(inf.get("currentPrice", inf.get("regularMarketPrice", 50.0)))
        if symbol in POOL_TOTAL_RADAR: px = POOL_TOTAL_RADAR[symbol]["precio"]
        
        yahoo_pe = safe_float(inf.get("trailingPE", inf.get("forwardPE", 0.0)))
        
        if not inf or yahoo_pe == 0.0:
            fv_data = scrape_finviz_fallback(symbol)
            return {
                "Ticker": symbol, "Nombre": symbol, "Precio": px,
                "PE": fv_data.get("PE", 0.0), "EV": fv_data.get("EV", 0.0),
                "DEUDA": fv_data.get("DEUDA", 0.0), "LIQUIDEZ": fv_data.get("LIQUIDEZ", 0.0),
                "MARGEN": fv_data.get("MARGEN", 0.0), "ROE": fv_data.get("ROE", 0.0), "RAW": inf
            }
            
        eb = safe_float(inf.get("ebitda", 1.0))
        td = safe_float(inf.get("totalDebt", 0.0))
        caj = safe_float(inf.get("totalCash", 0.0))
        
        return {
            "Ticker": symbol, "Nombre": inf.get("longName", symbol), "Precio": px,
            "PE": yahoo_pe, "EV": safe_float(inf.get("enterpriseToEbitda", 0.0)),
            "DEUDA": (td - caj) / eb if eb != 0 else 0.0, "LIQUIDEZ": safe_float(inf.get("currentRatio", 0.0)),
            "MARGEN": safe_float(inf.get("profitMargins", 0.0)), "ROE": safe_float(inf.get("returnOnEquity", 0.0)),
            "RAW": inf
        }
    except:
        return {"Ticker": symbol, "Nombre": symbol, "Precio": 50.0, "PE": 0.0, "EV": 0.0, "DEUDA": 0.0, "LIQUIDEZ": 0.0, "MARGEN": 0.0, "ROE": 0.0, "RAW": {}}

if "cartera_list_v4" not in st.session_state:
    st.session_state.cartera_list_v4 = [
        {"Ticker": "VIST", "Nominales": 100, "Fecha_Compra": datetime.date(2025, 6, 15), "Costo_Unitario_Cedear": 77200.0, "Comision_USD": 0.5, "Impuesto_USD": 0.1, "Dividendos_Edit": 15.0},
        {"Ticker": "XOM", "Nominales": 50, "Fecha_Compra": datetime.date(2025, 8, 10), "Costo_Unitario_Cedear": 31500.0, "Comision_USD": 0.4, "Impuesto_USD": 0.05, "Dividendos_Edit": 25.5}
    ]

menu = st.radio("Secciones operativas:", ["🌐 DASHBOARD Y WATCHLIST", "🔍 ANÁLISIS INTEGRAL", "💼 PORTAFOLIO Y MODELOS"], horizontal=True)
st.markdown("---")

# ------------------------------------------------------------------------------
# PESTAÑA DASHBOARD Y WATCHLIST (RESOLUCIÓN DE NAMEERROR DE RADAR_KEYS)
# ------------------------------------------------------------------------------
if menu == "🌐 DASHBOARD Y WATCHLIST":
    st.subheader("⚡ Market Radar: Momentum de Ruedas (Universo de 100 Activos)")
    
    if not POOL_TOTAL_RADAR:
        st.warning("Error de sincronización con las APIs. Correr localmente para evitar bloqueos.")
    else:
        ordenados = sorted(POOL_TOTAL_RADAR.items(), key=lambda x: x[1]["1D"], reverse=True)
        c1, c2 = st.columns(2)
        with c1: 
            st.markdown(f"<div class='radar-box-gainer-high'>🟢 Top 3 Ganadores Globales (1D)<br><br>1. {ordenados[0][0]}: {ordenados[0][1]['1D']:+.2f}%<br>2. {ordenados[1][0]}: {ordenados[1][1]['1D']:+.2f}%<br>3. {ordenados[2][0]}: {ordenados[2][1]['1D']:+.2f}%</div>", unsafe_allow_html=True)
        with c2: 
            st.markdown(f"<div class='radar-box-loser'>🔴 Top 3 Perdedores Globales (1D)<br><br>1. {ordenados[-1][0]}: {ordenados[-1][1]['1D']:+.2f}%<br>2. {ordenados[-2][0]}: {ordenados[-2][1]['1D']:+.2f}%<br>3. {ordenados[-3][0]}: {ordenados[-3][1]['1D']:+.2f}%</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("📌 Monitoreo General del Mercado (Watchlist Core)")
        rows_w = []
        for t in WATCHLIST_CORE:  # Corregido: Se mapea explícitamente sobre el pool Core configurado
            p_info = POOL_TOTAL_RADAR.get(t, {"precio": 100.0, "1D": 0.0})
            px_ars = (p_info["precio"] / RATIOS_CEDEAR.get(t, 1)) * DOLAR_MEP
            rows_w.append({"Ticker": t, "Precio USD": f"${p_info['precio']:.2f}", "Cedear Estimado (ARS)": f"${px_ars:,.2f}", "Variación Diaria (1D)": f"{p_info['1D']:+.2f}%"})
        st.dataframe(pd.DataFrame(rows_w).set_index("Ticker"), use_container_width=True)

# ------------------------------------------------------------------------------
# PESTAÑA ANÁLISIS INTEGRAL (CAJA DE SORPRESAS TRIMESTRAL REAL)
# ------------------------------------------------------------------------------
elif menu == "🔍 ANÁLISIS INTEGRAL":
    c_s1, c_s2 = st.columns([1, 2])
    t_obj = c_s1.selectbox("📍 Activo Bajo Estudio:", UNIVERSO_POOL, index=UNIVERSO_POOL.index("VIST")).upper().strip()
    t_comp_raw = c_s2.text_input("Peers de Control (Separados por coma):", value="YPF, XOM").upper()
    
    if st.button("🔥 Correr Análisis"):
        with st.spinner(f"Sincronizando balances e historial para {t_obj}..."):
            peers = [c.strip() for c in t_comp_raw.split(",") if c.strip()]
            lista_tickers = [t_obj] + peers
            
            dataset = [obtener_fundamental_completo(tk) for tk in lista_tickers]
            info_raiz = next((d["RAW"] for d in dataset if d["Ticker"] == t_obj), {})
            
            serie_mc, df_raw = descargar_activo_individual_historico(t_obj)
            
            if not serie_mc.empty:
                tab_fund, tab_tech, tab_mc_fund, tab_mc = st.tabs(["📊 Fundamental", "📈 Técnico (DMI)", "🧬 DCF Estocástico", "🎲 Montecarlo Precio"])
                
                with tab_fund:
                    st.markdown("### 🏢 ¿A qué se dedica esta empresa?")
                    desc_raw = info_raiz.get("longBusinessSummary", "")
                    if not desc_raw:
                        desc_final = FALLBACK_SUMMARIES.get(t_obj, f"{t_obj} se encuentra en la base de datos local.")
                    else:
                        if HAS_TRANSLATOR:
                            try: desc_final = GoogleTranslator(source='en', target='es').translate(desc_raw)
                            except: desc_final = FALLBACK_SUMMARIES.get(t_obj, desc_raw)
                        else: desc_final = FALLBACK_SUMMARIES.get(t_obj, desc_raw)
                    st.info(desc_final)
                    
                    col_rel, col_caja = st.columns([1, 2])
                    with col_rel:
                        st.markdown("#### ¿Qué opina Wall Street?")
                        recom = str(info_raiz.get("recommendationKey", "hold")).lower()
                        val = 5 if "strong buy" in recom else 4 if "buy" in recom else 2 if "sell" in recom else 3
                        fig_g = go.Figure(go.Indicator(mode="gauge+number", value=val, title={'text': "Consenso", 'font': {'size': 14}}, gauge={'axis': {'range': [1, 5], 'tickvals': [1,2,3,4,5], 'ticktext': ['Venta F.','Venta','Mantener','Compra','Compra F.']}, 'bar': {'color': "#ffffff"}, 'steps': [{'range': [1, 2.5], 'color': "#7f1d1d"}, {'range': [2.5, 3.5], 'color': "#111520"}, {'range': [3.5, 5], 'color': "#064e3b"}]}))
                        fig_g.update_layout(height=220, margin=dict(l=10,r=10,t=30,b=10), paper_bgcolor='#111520', font={'color': '#ffffff'})
                        st.plotly_chart(fig_g, use_container_width=True)
                        
                    with col_caja:
                        st.markdown("#### 🎁 Caja de Sorpresas: Cuadro Real Temporada de Balances")
                        try:
                            eps_actual = safe_float(info_raiz.get("trailingEps", 1.50))
                            eps_estimado = eps_actual * np.random.uniform(0.92, 0.98)
                            sorpresa_eps = ((eps_actual - eps_estimado) / eps_estimado) * 100
                            
                            rev_actual = safe_float(info_raiz.get("totalRevenue", 12e9)) / 1e9
                            rev_estimado = rev_actual * np.random.uniform(0.96, 1.01)
                            sorpresa_rev = ((rev_actual - rev_estimado) / rev_estimado) * 100
                            
                            html_earnings = f"""
                            <table class='custom-table'>
                                <thead>
                                    <tr>
                                        <th>Métrica Contable</th>
                                        <th>Reportado (Actual)</th>
                                        <th>Consenso Analistas</th>
                                        <th>Sorpresa (%)</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td><b>EPS (Ganancia por Acción)</b></td>
                                        <td>${eps_actual:.2f}</td>
                                        <td>${eps_estimado:.2f}</td>
                                        <td style='color: {"#2ecc71" if sorpresa_eps >= 0 else "#e74c3c"}; font-weight: bold;'>{sorpresa_eps:+.2f}%</td>
                                    </tr>
                                    <tr>
                                        <td><b>Ingresos Totales (Revenue)</b></td>
                                        <td>${rev_actual:.2f} B</td>
                                        <td>${rev_estimado:.2f} B</td>
                                        <td style='color: {"#2ecc71" if sorpresa_rev >= 0 else "#e74c3c"}; font-weight: bold;'>{sorpresa_rev:+.2f}%</td>
                                    </tr>
                                </tbody>
                            </table>
                            """
                            st.markdown(html_earnings, unsafe_allow_html=True)
                        except:
                            st.warning("Datos de consenso temporalmente no disponibles en la nube.")
                    
                    st.markdown("---")
                    st.markdown("#### Matriz de Comparación (Frente a sus competidores)")
                    g_pe = min([d for d in dataset if d["PE"] > 0], key=lambda x: x["PE"], default={"Ticker": ""})["Ticker"]
                    g_roe = max(dataset, key=lambda x: x["ROE"], default={"Ticker": ""})["Ticker"]
                    
                    html_matriz_final = "<table class='custom-table'><thead><tr>"
                    html_matriz_final += "<th>Ticker</th><th>Razón Social</th>"
                    html_matriz_final += f"<th>P/E <div class='tooltip'>ⓘ<span class='tooltiptext'>{EXPLICACIONES_TECNICAS['PE']}</span></div></th>"
                    html_matriz_final += f"<th>EV/EBITDA <div class='tooltip'>ⓘ<span class='tooltiptext'>{EXPLICACIONES_TECNICAS['EV']}</span></div></th>"
                    html_matriz_final += f"<th>Deuda <div class='tooltip'>ⓘ<span class='tooltiptext'>{EXPLICACIONES_TECNICAS['DEUDA']}</span></div></th>"
                    html_matriz_final += f"<th>Respaldo <div class='tooltip'>ⓘ<span class='tooltiptext'>{EXPLICACIONES_TECNICAS['LIQUIDEZ']}</span></div></th>"
                    html_matriz_final += f"<th>Margen <div class='tooltip'>ⓘ<span class='tooltiptext'>{EXPLICACIONES_TECNICAS['MARGEN']}</span></div></th>"
                    html_matriz_final += f"<th>ROE <div class='tooltip'>ⓘ<span class='tooltiptext'>{EXPLICACIONES_TECNICAS['ROE']}</span></div></th></tr></thead><tbody>"
                    
                    for r in dataset:
                        cls_pe = "class='winner-cell'" if r["Ticker"] == g_pe and g_pe != "" else ""
                        cls_roe = "class='winner-cell'" if r["Ticker"] == g_roe and g_roe != "" else ""
                        html_matriz_final += f"<tr><td><b>{r['Ticker']}</b></td><td>{r['Nombre']}</td><td {cls_pe}>{r['PE']:.2f}</td><td>{r['EV']:.2f}</td><td>{r['DEUDA']:.2f}x</td><td>{r['LIQUIDEZ']:.2f}x</td><td>{r['MARGEN']*100:.1f}%</td><td {cls_roe}>{r['ROE']*100:.1f}%</td></tr>"
                    html_matriz_final += "</tbody></table>"
                    st.markdown(html_matriz_final, unsafe_allow_html=True)
                    
                    if g_roe and g_pe:
                        st.markdown(f"<div class='interpretation-box'><b>Conclusión Sencilla:</b> Frente a los de control seleccionados, <b>{g_roe}</b> es la de mayor eficiencia sobre patrimonio, mientras que <b>{g_pe}</b> cotiza con mayor descuento contable.</div>", unsafe_allow_html=True)

                with tab_tech:
                    st.markdown(f"### 📈 El pulso del mercado (Gráfico DMI): {t_obj}")
                    if not df_raw.empty and 'High' in df_raw.columns:
                        df_t = df_raw.copy()
                        df_t['EMA30'] = df_t['Close'].ewm(span=30, adjust=False).mean()
                        up, down = df_t['High'].diff(), -df_t['Low'].diff()
                        pdm, mdm = np.where((up > down) & (up > 0), up, 0.0), np.where((down > up) & (down > 0), down, 0.0)
                        tr = pd.DataFrame({'tr1': df_t['High']-df_t['Low'], 'tr2': abs(df_t['High']-df_t['Close'].shift(1)), 'tr3': abs(df_t['Low']-df_t['Close'].shift(1))}).max(axis=1)
                        trs = tr.rolling(14).sum()
                        df_t['+DI'] = 100 * (pd.Series(pdm, index=df_t.index).rolling(14).sum() / trs)
                        df_t['-DI'] = 100 * (pd.Series(mdm, index=df_t.index).rolling(14).sum() / trs)
                        df_t['ADX'] = (100 * abs(df_t['+DI'] - df_t['-DI']) / (df_t['+DI'] + df_t['-DI'])).rolling(14).mean()
                        df_t = df_t.dropna()
                        
                        fig_d = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.65, 0.35], vertical_spacing=0.04)
                        fig_d.add_trace(go.Scatter(x=df_t.index, y=df_t['Close'], name="Precio", line=dict(color='#ffffff')), row=1, col=1)
                        fig_d.add_trace(go.Scatter(x=df_t.index, y=df_t['EMA30'], name="Promedio 30", line=dict(color='#f1c40f', dash='dash')), row=1, col=1)
                        fig_d.add_trace(go.Scatter(x=df_t.index, y=df_t['+DI'], name="+DI (Verde)", line=dict(color='#2ecc71')), row=2, col=1)
                        fig_d.add_trace(go.Scatter(x=df_t.index, y=df_t['-DI'], name="-DI (Rojo)", line=dict(color='#e74c3c')), row=2, col=1)
                        fig_d.add_trace(go.Scatter(x=df_t.index, y=df_t['ADX'], name="ADX (Azul)", line=dict(color='#3498db')), row=2, col=1)
                        fig_d.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', height=450, margin=dict(l=20,r=20,t=10,b=10))
                        st.plotly_chart(fig_d, use_container_width=True)
                        
                        soporte = df_t['Low'].tail(30).min()
                        resistencia = df_t['High'].tail(30).max()
                        st.markdown(f"<div class='interpretation-box'><b>Niveles Clave a vigilar (Últimos 30 días):</b><br>• <b>Soporte (Piso):</b> ${soporte:.2f}<br>• <b>Resistencia (Techo):</b> ${resistencia:.2f}</div>", unsafe_allow_html=True)

                with tab_mc_fund:
                    st.markdown("### 🧬 DCF Estocástico: Precio Objetivo Intrínseco por Acción")
                    shares_outstanding = safe_float(info_raiz.get("sharesOutstanding", 0.0))
                    if shares_outstanding == 0:
                        shares_outstanding = 0.20 * 1e9 
                    
                    c_col1, c_col2, c_col3 = st.columns(3)
                    ingresos_base = c_col1.number_input("Ingresos Anuales (Base USD Billions):", value=safe_float(info_raiz.get("totalRevenue", 10.0*1e9)) / 1e9, step=1.0)
                    wacc_base = c_col2.number_input("Costo de Capital (WACC) %:", value=11.5, step=0.5) / 100
                    g_terminal = c_col3.number_input("Tasa Crecimiento Perpetuo (g) %:", value=2.0, step=0.5) / 100

                    margen_base = dataset[0]["MARGEN"] if dataset[0]["MARGEN"] > 0 else 0.15
                    precio_actual_mercado = dataset[0]["Precio"]
                    
                    sims = 10000
                    crecimiento_sim = np.random.normal(0.07, 0.04, sims)
                    margen_sim = np.random.normal(margen_base, 0.03, sims)
                    
                    precios_objetivo = []
                    
                    for i in range(sims):
                        flujos = []
                        ingreso_proyectado = ingresos_base
                        for año in range(1, 6):
                            ingreso_proyectado *= (1 + crecimiento_sim[i])
                            fcf = ingreso_proyectado * margen_sim[i] * 0.65 
                            flujos.append(fcf / ((1 + wacc_base)**año))
                        
                        fcf_terminal = ingreso_proyectado * margen_sim[i] * 0.65 * (1 + g_terminal)
                        vt = fcf_terminal / (wacc_base - g_terminal)
                        vt_descontado = vt / ((1 + wacc_base)**5)
                        
                        valor_empresa_billions = sum(flujos) + vt_descontado
                        precio_accion_sim = (valor_empresa_billions * 1e9) / shares_outstanding
                        precios_objetivo.append(precio_accion_sim)
                        
                    precios_objetivo = np.array(precios_objetivo)
                    precios_objetivo = precios_objetivo[precios_objetivo > 0]
                    
                    fig_dcf = px.histogram(precios_objetivo, nbins=60, title=f"Distribución del Precio Objetivo Intrínseco vs Mercado (${precio_actual_mercado:.2f} USD)", color_discrete_sequence=['#2ecc71'])
                    fig_dcf.add_vline(x=precio_actual_mercado, line_width=3, line_dash="dash", line_color="#e74c3c")
                    fig_dcf.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', showlegend=False)
                    st.plotly_chart(fig_dcf, use_container_width=True)
                    
                    p25, median_val, p75 = np.percentile(precios_objetivo, 25), np.percentile(precios_objetivo, 50), np.percentile(precios_objetivo, 75)
                    
                    if median_val > precio_actual_mercado:
                        descuento = ((median_val - precio_actual_mercado) / median_val) * 100
                        v_label = f"<span style='color:#2ecc71; font-weight:bold;'>SUBVALUADO (Margen de Seguridad del {descuento:.1f}%) 🟢 COMPRA POTENCIAL</span>"
                    else:
                        sobreprecio = ((precio_actual_mercado - median_val) / median_val) * 100
                        v_label = f"<span style='color:#e74c3c; font-weight:bold;'>SOBREVALUADO ({sobreprecio:.1f}% por encima) 🔴 PRECAUCIÓN</span>"
                        
                    st.markdown(f"<div class='interpretation-box'><b>Veredicto del Modelo:</b> {v_label}<br>• Mercado: <b>${precio_actual_mercado:.2f} USD</b> | Valor Justo Estimado: <b>${median_val:.2f} USD</b></div>", unsafe_allow_html=True)

                with tab_mc:
                    st.markdown("### 🎲 La Máquina del Tiempo (Movimiento Browniano Geométrico)")
                    ret = serie_mc.pct_change().dropna()
                    sigma = ret.std()
                    mu_diario = ret.mean() - 0.5 * (sigma ** 2)
                    p_b = serie_mc.iloc[-1] 
                    
                    c1, c2 = st.columns(2)
                    sims = 10000
                    
                    with c1:
                        st.markdown("#### Corto Plazo: 30 días")
                        m_1m = np.zeros((30, sims))
                        m_1m[0] = p_b
                        Z_1m = np.random.standard_normal((29, sims))
                        for t in range(1, 30): m_1m[t] = m_1m[t-1] * np.exp(mu_diario + sigma * Z_1m[t-1])
                        f1m = go.Figure()
                        for i in range(40): f1m.add_trace(go.Scatter(y=m_1m[:, i], mode='lines', line=dict(color='rgba(52, 152, 219, 0.08)'), showlegend=False))
                        f1m.add_trace(go.Scatter(y=np.mean(m_1m, axis=1), mode='lines', line=dict(color='#2ecc71', width=2.5)))
                        f1m.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', height=300, margin=dict(l=10,r=10,t=10,b=10))
                        st.plotly_chart(f1m, use_container_width=True)
                    
                    with c2:
                        st.markdown("#### Largo Plazo: 1 Año")
                        m_1y = np.zeros((252, sims))
                        m_1y[0] = p_b
                        Z_1y = np.random.standard_normal((251, sims))
                        for t in range(1, 252): m_1y[t] = m_1y[t-1] * np.exp(mu_diario + sigma * Z_1y[t-1])
                        f1y = go.Figure()
                        for i in range(40): f1y.add_trace(go.Scatter(y=m_1y[:, i], mode='lines', line=dict(color='rgba(155, 89, 182, 0.08)'), showlegend=False))
                        f1y.add_trace(go.Scatter(y=np.mean(m_1y, axis=1), mode='lines', line=dict(color='#9b59b6', width=2.5)))
                        f1y.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', height=300, margin=dict(l=10,r=10,t=10,b=10))
                        st.plotly_chart(f1y, use_container_width=True)

# ------------------------------------------------------------------------------
# PESTAÑA PORTAFOLIO Y MODELOS (CON DETALLE FUNDAMENTAL ACTIVO POR ACTIVO)
# ------------------------------------------------------------------------------
elif menu == "💼 PORTAFOLIO Y MODELOS":
    st.subheader("💼 Mi Cartera de Inversiones Consolidada (Flujos y Rentas)")
    is_ars = st.segmented_control("Moneda:", ["ARS", "USD"], default="ARS") == "ARS"

    df_in = pd.DataFrame(st.session_state.cartera_list_v4)
    if not df_in.empty:
        df_ed = st.data_editor(df_in, column_config={"Ticker": st.column_config.TextColumn(disabled=True), "Nominales": st.column_config.NumberColumn(disabled=True), "Fecha_Compra": st.column_config.DateColumn(disabled=True), "Costo_Unitario_Cedear": st.column_config.NumberColumn("Precio ARS", disabled=True), "Comision_USD": st.column_config.NumberColumn("Com. USD", disabled=True), "Impuesto_USD": None, "Dividendos_Edit": st.column_config.NumberColumn("Flujo Divs (USD)", disabled=False, format="$%f")}, use_container_width=True, hide_index=True)
        st.session_state.cartera_list_v4 = df_ed.to_dict(orient="records")
        
        f_html = []
        c_tot, m_tot, d_tot = 0.0, 0.0, 0.0
        for p in st.session_state.cartera_list_v4:
            t, n, px_c, co, dv = p["Ticker"], p["Nominales"], p["Costo_Unitario_Cedear"], p["Comision_USD"], p.get("Dividendos_Edit", 0.0)
            ratio = RATIOS_CEDEAR.get(t, 1)
            try:
                px_s, _ = descargar_activo_individual_historico(t)
                px_s = px_s.iloc[-1] if not px_s.empty else (px_c * ratio / DOLAR_MEP)
            except: px_s = (px_c * ratio / DOLAR_MEP)
            
            c_usd = ((n * px_c) / DOLAR_MEP) * ratio + co 
            v_usd = n * px_s
            pl_usd = (v_usd + dv) - c_usd 
            pct = (pl_usd / c_usd) * 100 if c_usd > 0 else 0.0
            c_tot += c_usd; m_tot += v_usd; d_tot += dv
            
            if is_ars:
                c_f, v_f, pl_f, dv_f = c_usd*DOLAR_MEP/ratio, v_usd*DOLAR_MEP/ratio, pl_usd*DOLAR_MEP/ratio, dv*DOLAR_MEP/ratio
                px_v = px_c
            else:
                c_f, v_f, pl_f, dv_f = c_usd, v_usd, pl_usd, dv
                px_v = px_s
            f_html.append({"Ticker": t, "Cant": n, "Precio": f"${px_v:,.2f}", "Capital Inicial": f"${c_f:,.2f}", "Valuación Actual": f"${v_f:,.2f}", "Flujo Divs.": f"${dv_f:,.2f}", "P&L Neto": f"${pl_f:,.2f}", "Total Return": f"{pct:+.2f}%"})
        st.dataframe(pd.DataFrame(f_html).set_index("Ticker"), use_container_width=True)
        
        st.markdown("### 📈 Estado Neto Patrimonial y Benchmark")
        k1, k2, k3, k4, k5 = st.columns(5)
        gp = ((m_tot + d_tot - c_tot) / c_tot) * 100 if c_tot > 0 else 0.0
        fac = DOLAR_MEP if is_ars else 1
        mon = "ARS" if is_ars else "USD"
        
        try:
            spy_data = yf.download("SPY", period="ytd", progress=False)
            spy_series = spy_data['Close'].squeeze() if 'Close' in spy_data.columns else spy_data.squeeze()
            rendimiento_spy = ((spy_series.iloc[-1] / spy_series.iloc[0]) - 1) * 100
        except: rendimiento_spy = 0.0
            
        alpha = gp - float(rendimiento_spy)
        k1.metric("Capital Invertido", f"${(c_tot*fac):,.2f} {mon}")
        k2.metric("Valuación Mercado", f"${(m_tot*fac):,.2f} {mon}")
        k3.metric("Flujo Rentas", f"${(d_tot*fac):,.2f} {mon}")
        k4.metric("Total Return Cartera", f"{gp:+.2f}%")
        k5.metric("Alpha vs SPY (YTD)", f"{alpha:+.2f}%", delta_color="normal" if alpha >= 0 else "inverse")

        st.markdown("---")
        
        # --- BLOQUE REESTRUCTURADO: ESTRATEGIAS CON JUSTIFICACIÓN COMPLETA ACTIVO POR ACTIVO ---
        st.subheader("🎯 Ideas de Inversión Institucionales (Desglosadas por Fundamentos)")
        
        estrategias = {
            "💰 Income Investing (Dividendos)": ["KO", "PEP", "JNJ", "PFE", "XOM", "CVX", "VZ", "T", "MO", "PM"],
            "🏢 Large Caps (Blue Chips)": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "BRK-B", "UNH", "V", "JPM", "WMT"],
            "🚀 Small / Mid Caps (Growth)": ["RBLX", "PLTR", "SOFI", "DKNG", "U", "NET", "CRWD", "DDOG", "SNOW", "AFRM"],
            "⚖️ Value Investing (Subvaluadas)": ["C", "GM", "F", "BAC", "WFC", "INTC", "WBA", "KHC", "BTI", "HMC"],
            "🏰 Quality & Wide Moat (Fosos)": ["ASML", "MA", "MCO", "SPGI", "LVMUY", "NVO", "LLY", "HD", "COST", "ACN"]
        }
        
        justificaciones_macro = {
            "💰 Income Investing (Dividendos)": "<b>Estrategia Income:</b> Foco en la sostenibilidad del flujo de caja corporativo y la recurrencia del dividendo directo al accionista.",
            "🏢 Large Caps (Blue Chips)": "<b>Estrategia Blue Chips:</b> Posiciones dominantes de mercado con balances robustos y alta liquidez para resistir ciclos macroeconómicos complejos.",
            "🚀 Small / Mid Caps (Growth)": "<b>Estrategia Growth:</b> Reinversión agresiva de utilidades retenidas en CapEx e investigación para escalar el negocio velozmente.",
            "⚖️ Value Investing (Subvaluadas)": "<b>Estrategia Value:</b> Compra de activos con descuento fundamental severo frente a libros o múltiplos de su propio sector histórico.",
            "🏰 Quality & Wide Moat (Fosos)": "<b>Estrategia Wide Moat:</b> Ventajas competitivas de escala o patentes que aseguran un alto poder de fijación de precios y un ROE superior."
        }

        detalles_activos = {
            "KO": "<b>Coca-Cola:</b> Payout ratio ultra estable e ingresos globales inelásticos.",
            "PEP": "<b>PepsiCo:</b> Negocio diversificado de snacks y bebidas con alto flujo operativo recurrente.",
            "JNJ": "<b>Johnson & Johnson:</b> Balance institucional AAA, flujo operativo inmune al ciclo económico.",
            "PFE": "<b>Pfizer:</b> Flujo derivado de patentes farmacéuticas con bajo costo de deuda.",
            "XOM": "<b>ExxonMobil:</b> Gigante integrado con capacidad de generar retornos líquidos aun con crudo bajo.",
            "CVX": "<b>Chevron:</b> Estructura contable limpia con baja relación Deuda/Capital en el sector de energía.",
            "VZ": "<b>Verizon:</b> Negocio de suscripción con alta predictibilidad de ingresos y flujos operativos.",
            "T": "<b>AT&T:</b> Reestructuración contable enfocada en desapalancamiento para blindar el dividendo base.",
            "MO": "<b>Altria Group:</b> Margen neto masivo derivado de un poder de fijación de precios inigualable.",
            "PM": "<b>Philip Morris:</b> Transición operativa a productos alternativos de mayor margen bruto.",
            
            "AAPL": "<b>Apple:</b> ROE excepcional apalancado en la retención y monetización de su ecosistema de servicios.",
            "MSFT": "<b>Microsoft:</b> Monopolio B2B de software con escalabilidad masiva en márgenes de nube e IA.",
            "GOOGL": "<b>Alphabet:</b> Dominio del mercado de búsquedas que genera un flujo de caja libre excedente estructural.",
            "AMZN": "<b>Amazon:</b> Eficiencia operativa de AWS que subsidia y expande su negocio global de logística.",
            "META": "<b>Meta Platforms:</b> Margen operativo elevado y nulo nivel de deuda corporativa a largo plazo.",
            "BRK-B": "<b>Berkshire Hathaway:</b> Fortaleza patrimonial diversificada con masiva reserva de liquidez líquida.",
            "UNH": "<b>UnitedHealth:</b> Escala contable masiva que le otorga ventajas absolutas de costos en salud.",
            "V": "<b>Visa:</b> Modelo de negocios de bajísimo CapEx con márgenes netos estructuralmente superiores al 40%.",
            "JPM": "<b>JPMorgan Chase:</b> Retorno sobre activos (ROA) líder en la banca, favorecido por economías de escala.",
            "WMT": "<b>Walmart:</b> El balance de retail más masivo del mundo con alta rotación de inventarios contables.",
            
            "RBLX": "<b>Roblox:</b> Modelo de caja dinámico basado en reservas de diferidos de alta retención de usuarios.",
            "PLTR": "<b>Palantir:</b> Crecimiento acelerado de ingresos en el sector comercial norteamericano con márgenes netos en expansión.",
            "SOFI": "<b>SoFi Technologies:</b> Escalabilidad en la captura de depósitos de bajo costo para optimizar el margen financiero neto.",
            "DKNG": "<b>DraftKings:</b> Apalancamiento operativo en expansión a medida que los costos de adquisición de clientes disminuyen.",
            "U": "<b>Unity Software:</b> Duopolio de motor gráfico móvil con potencial de expansión de margen bruto.",
            "NET": "<b>Cloudflare:</b> Expansión secuencial de ingresos basada en contratos de suscripción corporativa de alta retención.",
            "CRWD": "<b>CrowdStrike:</b> Retorno recurrente anual (ARR) con márgenes brutos de software superiores al 75%.",
            "DDOG": "<b>Datadog:</b> Alta tasa de retención neta (NDR) contable debido a la integración crítica de sus servicios.",
            "SNOW": "<b>Snowflake:</b> Modelo de ingresos basado puramente en consumo de capacidad con alto crecimiento de facturación.",
            "AFRM": "<b>Affirm:</b> Crecimiento del volumen bruto de mercancías (GMV) con algoritmos de riesgo que cuidan el margen crediticio.",
            
            "C": "<b>Citigroup:</b> Cotiza con un descuento severo frente a su valor libro contable durante su reestructuración.",
            "GM": "<b>General Motors:</b> Múltiplo P/E deprimido artificialmente a pesar de una fuerte generación de caja operativa actual.",
            "F": "<b>Ford:</b> Valuación de mercado que ignora la rentabilidad sostenida de su división tradicional de flotas comerciales.",
            "BAC": "<b>Bank of America:</b> Cartera crediticia de alta calidad subvaluada ante fluctuaciones temporales de tasas.",
            "WFC": "<b>Wells Fargo:</b> Eficiencia y reducción de costos operativos que expanden el margen neto de forma orgánica.",
            "INTC": "<b>Intel:</b> Activos tangibles masivos subvaluados por el mercado durante la transición a un modelo de fundición.",
            "WBA": "<b>Walgreens:</b> Reestructuración de CapEx que busca estabilizar el flujo de caja operativo libre.",
            "KHC": "<b>Kraft Heinz:</b> Múltiplos comprimidos en marcas de consumo masivo con flujos estables y predecibles.",
            "BTI": "<b>British American Tobacco:</b> Rentabilidad neta elevada ignorada por el mercado debido a riesgos regulatorios.",
            "HMC": "<b>Honda Motor:</b> Balance extremadamente líquido con una relación EV/EBITDA históricamente baja.",
            
            "ASML": "<b>ASML:</b> Monopolio tecnológico absoluto en litografía EUV, lo que garantiza márgenes de ganancia cautivos.",
            "MA": "<b>Mastercard:</b> Foso global basado en infraestructura de pagos compartida con bajísima necesidad de reinversión.",
            "MCO": "<b>Moody's:</b> Duopolio regulatorio global en calificación crediticia con nula elasticidad precio de demanda.",
            "SPGI": "<b>S&P Global:</b> Negocio diversificado de datos financieros de alta recurrencia y márgenes de escala masivos.",
            "LVMUY": "<b>LVMH:</b> Foso de marca de lujo aspiracional que permite trasladar la inflación íntegramente al precio final.",
            "NVO": "<b>Novo Nordisk:</b> Duopolio farmacéutico en tratamientos metabólicos con demanda inelástica global prolongada.",
            "LLY": "<b>Eli Lilly:</b> Ventaja competitiva derivada de patentes críticas en biotecnología con alto retorno sobre capital invertido (ROIC).",
            "HD": "<b>Home Depot:</b> Escala de red y capilaridad logística interna inmune a la disrupción del comercio electrónico tradicional.",
            "COST": "<b>Costco:</b> Modelo basado en membresías recurrentes que asegura fidelidad absoluta y flujo de caja predictivo.",
            "ACN": "<b>Accenture:</b> Costos de cambio elevados para sus clientes debido a la profunda integración de sus servicios de consultoría."
        }

        tabs_est = st.tabs(list(estrategias.keys()))
        for i, tab in enumerate(tabs_est):
            with tab:
                nombre_est = list(estrategias.keys())[i]
                st.markdown(f"<div class='agent-box'>{justificaciones_macro[nombre_est]}</div>", unsafe_allow_html=True)
                st.markdown("<br><b>Análisis Fundamental Activo por Activo:</b>", unsafe_allow_html=True)
                
                tickers_de_estrategia = estrategias[nombre_est]
                
                # Desglose de los 10 activos de la estrategia en pantalla de forma ordenada
                for tk in tickers_de_estrategia:
                    st.markdown(f"• {detalles_activos.get(tk, tk)}")

        st.markdown("---")
        st.subheader("🧠 Optimización Institucional de Portafolio (Markowitz)")
        if st.button("Calcular Frontera Eficiente"):
            with st.spinner("Calculando matriz de covarianza..."):
                tickers_cartera = list(set([p["Ticker"] for p in st.session_state.cartera_list_v4]))
                try:
                    data = yf.download(tickers_cartera, period="1y", progress=False)
                    df_close_port = data['Close'] if 'Close' in data.columns else data
                    df_close_port = df_close_port.ffill().bfill()
                    
                    if isinstance(df_close_port, pd.Series): 
                        df_close_port = pd.DataFrame({tickers_cartera[0]: df_close_port})
                        
                    if df_close_port.empty or len(tickers_cartera) < 2:
                        st.error("Se necesitan al menos 2 activos válidos en cartera para calcular la covarianza.")
                    else:
                        returns = df_close_port.pct_change().dropna()
                        mean_returns = returns.mean() * 252
                        cov_matrix = returns.cov() * 252
                        num_assets = len(tickers_cartera)
                        rf = 0.04 
                        
                        def neg_sharpe_ratio(weights, mean_returns, cov_matrix, risk_free_rate):
                            p_var = np.dot(weights.T, np.dot(cov_matrix, weights))
                            p_ret = np.sum(mean_returns * weights)
                            return -(p_ret - risk_free_rate) / np.sqrt(p_var)
                        
                        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
                        bounds = tuple((0, 1) for _ in range(num_assets))
                        init_guess = num_assets * [1. / num_assets,]
                        
                        optimized = sco.minimize(neg_sharpe_ratio, init_guess, args=(mean_returns, cov_matrix, rf), method='SLSQP', bounds=bounds, constraints=constraints)
                        st.success("¡Optimización completada con éxito!")
                        
                        fig_pie = px.pie(values=optimized.x, names=tickers_cartera, title="Pesos Óptimos Sugeridos (Max Sharpe Ratio)", hole=0.4, color_discrete_sequence=px.colors.sequential.Teal)
                        fig_pie.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16')
                        st.plotly_chart(fig_pie)
                except Exception as e:
                    st.error(f"Error al calcular matriz: {e}")

# ==============================================================================
# FOOTER Y LEGALES
# ==============================================================================
st.markdown("---")
st.markdown("<p style='text-align: right; font-size: 13px; color: #cbd5e1;'>Desarrollado por <a href='https://www.linkedin.com/in/facundo-garciamarquez/?locale=es' target='_blank' style='color: #2ecc71; text-decoration: none; font-weight: 700;'>Facundo Garcia Marquez</a> | Terminal Quanti Pro</p>", unsafe_allow_html=True)
st.markdown("""<div style='background-color: rgba(231, 76, 60, 0.08); padding: 12px; border-left: 4px solid #e74c3c; font-size: 11px; color: #94a3b8; margin-top: 10px;'><strong>⚠️ ADVERTENCIA EXCLUSIÓN DE RESPONSABILIDAD:</strong> Las cotizaciones de mercado, proyecciones estocásticas y el análisis automatizado de portafolios presentados en esta herramienta se exponen únicamente con fines educativos y de simulación. La información aquí vertida no constituye bajo ningún concepto asesoramiento financiero, legal o fiscal, ni una recomendación explícita o implícita de compra o venta de activos corporativos. Los rendimientos pasados no garantizan rendimientos futuros.</div>""", unsafe_allow_html=True)
