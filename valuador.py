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
# CONFIGURACIÓN DE PÁGINA Y ESTÉTICA INSTITUCIONAL (OBSIDIAN & BRASS)
# ------------------------------------------------------------------------------
st.set_page_config(page_title="Apex Financial Terminal", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"], [data-testid="stAppViewContainer"], [data-testid="stHeader"] { 
    background-color: #06080d !important; 
    color: #e2e8f0 !important; 
    font-family: 'Plus Jakarta Sans', sans-serif !important; 
}

/* Tipografía monoespaciada para todo dato contable, números y cotizaciones */
.tabular-nums, td, div[data-testid="stMetricValue"] > div {
    font-family: 'JetBrains Mono', monospace !important;
    font-variant-numeric: tabular-nums !important;
}

.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
h1 { font-weight: 800; color: #ffffff !important; font-size: 26px !important; letter-spacing: -0.02em; }
h2 { font-weight: 700; color: #f8fafc !important; font-size: 19px !important; }
h3 { font-weight: 600; color: #cbd5e1 !important; font-size: 15px !important; }

/* Radio Selector Minimalista */
div[data-testid="stRadio"] > div { 
    background: #0d111a !important; 
    padding: 5px !important; 
    border-radius: 8px !important; 
    border: 1px solid rgba(255, 255, 255, 0.08) !important; 
    display: flex !important;
    gap: 6px !important; 
    margin-bottom: 15px !important; 
}
div[data-testid="stRadio"] label[data-baseweb="radio"] { 
    padding: 6px 14px !important; 
    border-radius: 6px !important; 
    color: #94a3b8 !important; 
    font-weight: 600 !important; 
    font-size: 12px !important;
}
div[data-testid="stRadio"] label[data-baseweb="radio"]:hover {
    color: #f8fafc !important;
}

/* Métricas estilo Terminal Quant */
div[data-testid="stMetric"] { 
    background-color: #0d111a !important; 
    border: 1px solid rgba(255, 255, 255, 0.06) !important; 
    border-radius: 6px !important; 
    padding: 12px 14px !important; 
}
div[data-testid="stMetricLabel"] > div { 
    font-size: 11px !important; 
    text-transform: uppercase !important; 
    letter-spacing: 0.08em !important; 
    color: #64748b !important; 
    font-weight: 600 !important; 
}
div[data-testid="stMetricValue"] > div { 
    font-size: 18px !important; 
    color: #f8fafc !important; 
    font-weight: 600 !important; 
}

/* Botones institucionales en Brass / Oro viejo */
.stButton>button { 
    width: 100%; 
    background: linear-gradient(180deg, #d4a34b, #b8862d) !important; 
    color: #06080d !important; 
    font-weight: 700; 
    border-radius: 6px; 
    border: none; 
    padding: 0.55rem; 
    font-size: 12px !important; 
    letter-spacing: 0.03em;
}

/* Contenedores de Información */
.terminal-card {
    background-color: #0d111a;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 6px;
    padding: 14px;
    margin: 10px 0;
    font-size: 13px;
    line-height: 1.55;
}
.gold-card { border-left: 3px solid #d4a34b; }
.blue-card { border-left: 3px solid #0284c7; }
.green-card { border-left: 3px solid #10b981; }

/* Tablas Quant limpias sin recortes */
.table-viewport { 
    overflow: visible !important; 
    position: relative; 
    margin: 10px 0; 
}
.terminal-table { 
    width: 100%; 
    border-collapse: collapse; 
    font-size: 12px; 
    background-color: #0d111a; 
    border: 1px solid rgba(255, 255, 255, 0.07); 
    border-radius: 6px; 
}
.terminal-table th { 
    background-color: #121824; 
    color: #94a3b8; 
    padding: 8px 12px; 
    text-align: left; 
    font-weight: 600; 
    border-bottom: 1px solid rgba(255, 255, 255, 0.08); 
    font-size: 11px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.terminal-table td { 
    padding: 8px 12px; 
    border-bottom: 1px solid rgba(255, 255, 255, 0.04); 
    color: #e2e8f0; 
}
.terminal-table tr:hover td { 
    background-color: rgba(255, 255, 255, 0.02); 
}
.winner-cell { 
    background-color: rgba(212, 163, 75, 0.12) !important; 
    color: #e5a93c !important; 
    font-weight: 700; 
}

/* Tooltips */
.th-tooltip {
    position: relative;
    display: inline-block;
    cursor: pointer;
    color: #38bdf8;
    margin-left: 4px;
    font-weight: 700;
}
.th-tooltip .th-tooltiptext {
    visibility: hidden;
    width: 230px;
    background-color: #121824;
    color: #f1f5f9;
    text-align: left;
    padding: 8px 10px;
    border-radius: 5px;
    position: absolute;
    z-index: 9999;
    bottom: 130%;
    left: 50%;
    transform: translateX(-50%);
    opacity: 0;
    transition: opacity 0.2s ease-in-out;
    font-size: 11px;
    font-weight: 400;
    line-height: 1.4;
    border: 1px solid rgba(56, 189, 248, 0.4);
    box-shadow: 0 8px 20px rgba(0,0,0,0.8);
    pointer-events: none;
}
.th-tooltip:hover .th-tooltiptext { visibility: visible; opacity: 1; }

/* Badges semáforo táctico */
.badge-state {
    display: inline-block;
    padding: 2px 7px;
    border-radius: 4px;
    font-weight: 700;
    font-size: 10.5px;
    letter-spacing: 0.03em;
}
.badge-buy { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); }
.badge-hold { background: rgba(212, 163, 75, 0.15); color: #fbbf24; border: 1px solid rgba(212, 163, 75, 0.4); }
.badge-sell { background: rgba(244, 63, 94, 0.15); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.4); }
</style>""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# CONECTIVIDAD GEMINI AI (DUAL SOURCE + FALLBACKS)
# ------------------------------------------------------------------------------
try:
    import google.generativeai as genai
    HAS_GEMINI_LIB = True
except ImportError:
    HAS_GEMINI_LIB = False

st.sidebar.markdown("### 🔑 Parámetros de Conectividad")
secrets_key = st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, "secrets") else ""
gemini_input_key = st.sidebar.text_input("Gemini API Key:", value=secrets_key, type="password", help="Key de Google AI Studio")

GEMINI_KEY = gemini_input_key.strip() if gemini_input_key else None
if HAS_GEMINI_LIB and GEMINI_KEY:
    try:
        genai.configure(api_key=GEMINI_KEY)
    except:
        pass

def ia_sintesis_empresa(ticker, nombre, info_dict):
    deuda = info_dict.get('deuda', 0.0)
    margen = info_dict.get('margen', 0.0)
    roe = info_dict.get('roe', 0.0)
    
    if HAS_GEMINI_LIB and GEMINI_KEY:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = f"""
            Actúa como Equity Research Analyst institucional. Redacta un informe para {nombre} ({ticker}) en un MÁXIMO DE 5 RENGLONES:
            - Renglones 1-2: Core business, ventajas competitivas (Moat) y drivers directos de facturación.
            - Renglones 3-4: Guidance corporativo reciente (metas operativas de producción, CapEx o inversión).
            - Renglón 5: Situación de solvencia (Deuda Neta/EBITDA: {deuda:.2f}x, Margen Neto: {margen*100:.1f}%, ROE: {roe*100:.1f}%).
            Sin títulos ni cortes de línea vacíos.
            """
            res = model.generate_content(prompt)
            if res and res.text: return res.text.strip()
        except: pass
        
    return f"{nombre} ({ticker}) sostiene su modelo en activos estratégicos con ventajas de escala en su industria.\nLa gerencia enfoca su guidance en optimización de CapEx para sostener la expansión de márgenes operativos.\nEstructura patrimonial: Deuda Neta/EBITDA de {deuda:.2f}x, Margen Neto de {margen*100:.1f}% y ROE de {roe*100:.1f}%."

def ia_reverse_dcf_check(ticker, implied_g, roic, pe):
    """Evalúa la viabilidad del crecimiento implícito que descuenta el mercado."""
    if HAS_GEMINI_LIB and GEMINI_KEY:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = f"""
            Actúa como Senior Fund Manager. El precio actual de mercado de {ticker} (P/E de {pe:.1f}x) descuenta matemáticamente un crecimiento anual sostenido de Flujo de Caja Libre (FCF) del {implied_g*100:.1f}% durante los próximos 5 años.
            El ROE/ROIC actual de la empresa es del {roic*100:.1f}%.
            En 3 líneas concisas:
            1. Diagnostica si esa tasa de crecimiento exigida es conservadora, razonable o sumamente exigente respecto a su retorno sobre capital.
            2. Veredicto del trade: ¿El mercado está pagando de más o existe margen de seguridad?
            """
            res = model.generate_content(prompt)
            if res and res.text: return res.text.strip()
        except: pass
    
    status = "exigente" if implied_g > 0.12 else "razonable" if implied_g >= 0.04 else "conservador"
    return f"El mercado exige un crecimiento anual de FCF del {implied_g*100:.1f}%, lo que resulta {status} frente a su retorno de capital actual ({roic*100:.1f}%). Valuación actual con múltiplo de {pe:.1f}x."

def ia_tesis_ejecutiva(ticker, nombre, precio, pe, roe, deuda, margen, dcf_valor):
    upside = ((dcf_valor - precio) / precio) * 100 if precio > 0 else 0
    if HAS_GEMINI_LIB and GEMINI_KEY:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = f"""
            Portfolio Manager Memo para {nombre} ({ticker}):
            - Precio: ${precio:.2f} USD | DCF Mediano: ${dcf_valor:.2f} USD (Divergencia: {upside:+.1f}%)
            - P/E: {pe:.2f}x | ROE: {roe*100:.1f}% | Margen Neto: {margen*100:.1f}% | Deuda Neta/EBITDA: {deuda:.2f}x

            Formato estricto (3 puntos breves):
            1. Calidad Operativa y Apalancamiento.
            2. Rango de Valuación vs DCF.
            3. Recomendación Final (Compra / Mantener / Venta) con riesgo primario.
            """
            res = model.generate_content(prompt)
            if res and res.text: return res.text
        except: pass
        
    return f"**1. Calidad y Deuda:** ROE al {roe*100:.1f}% con apalancamiento neto de {deuda:.2f}x EBITDA.\n**2. Valuación:** Divergencia del {upside:+.1f}% frente a la estimación DCF (${dcf_valor:.2f} USD).\n**3. Dictamen:** {'Compra Acumulativa' if upside > 12 else 'Mantener'} | Riesgo: Volatilidad de tasas globales."

# ------------------------------------------------------------------------------
# CONEXIÓN A MERCADO
# ------------------------------------------------------------------------------
yf_session = requests.Session()
yf_session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

WATCHLIST_CORE = ["VIST", "YPF", "AAPL", "GGAL", "NVDA", "KO", "XOM", "WMT"]
RATIOS_CEDEAR = {
    "VIST": 1, "YPF": 1, "AAPL": 10, "GGAL": 1, "AMD": 10, "NVDA": 24, "MSFT": 30, "AMZN": 14, "GOOGL": 11, "META": 24, 
    "TSLA": 15, "KO": 5, "WMT": 6, "JNJ": 15, "PEP": 15, "PG": 15, "XOM": 5, "PAMP": 1, "SPY": 20, "QQQ": 20
}
UNIVERSO_POOL = list(RATIOS_CEDEAR.keys())

def safe_float(val):
    try: return float(val)
    except: return 0.0

@st.cache_data(ttl=600)
def obtener_dolar_mep_real():
    try:
        r = requests.get("https://www.dolarito.ar/", headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for el in soup.find_all(['div', 'span', 'p']):
            txt = el.get_text().lower()
            if 'mep' in txt and '$' in txt:
                for t in txt.split():
                    if '$' in t:
                        try:
                            v = float(t.replace('$', '').replace('.', '').replace(',', '.').strip())
                            if 1000 < v < 2500: return round(v, 2)
                        except: pass
        return 1420.0
    except: return 1420.0

DOLAR_MEP = obtener_dolar_mep_real()

@st.cache_data(ttl=900)
def descargar_datos_mercado(tickers):
    try:
        data = yf.download(tickers, period="1y", progress=False, session=yf_session)
        close = data['Close'].ffill().bfill() if isinstance(data.columns, pd.MultiIndex) else data['Close'].to_frame() if 'Close' in data.columns else data.ffill().bfill()
        res = {}
        f_ytd = datetime.date(datetime.date.today().year, 1, 1)
        for tk in tickers:
            s = close[tk].dropna() if tk in close.columns else pd.Series(dtype=float)
            if len(s) >= 2:
                p = float(s.iloc[-1])
                r1d = ((p / float(s.iloc[-2])) - 1) * 100
                r1m = ((p / float(s.iloc[-21])) - 1) * 100 if len(s) >= 21 else r1d
                r6m = ((p / float(s.iloc[-126])) - 1) * 100 if len(s) >= 126 else r1m
                r1y = ((p / float(s.iloc[0])) - 1) * 100
                s_ytd = s[s.index.date >= f_ytd]
                rytd = ((p / float(s_ytd.iloc[0])) - 1) * 100 if len(s_ytd) > 0 else r1d
                res[tk] = {"precio": p, "1D": r1d, "1M": r1m, "6M": r6m, "1Y": r1y, "YTD": rytd}
        return res, close
    except: return {}, pd.DataFrame()

DATOS_RADAR, DF_CLOSE_GLOBAL = descargar_datos_mercado(UNIVERSO_POOL)

@st.cache_data(ttl=600)
def descargar_activo_individual_historico(ticker):
    try:
        tk_b = ticker + ".BA" if ticker in ["GGAL", "PAMP", "YPF", "TXAR", "ALUA", "BMA", "CEPU"] else ticker
        df = yf.download(tk_b, period="2y", progress=False, session=yf_session)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.loc[:, ~df.columns.duplicated()]
        df_c = df['Close'].ffill().bfill()
        if isinstance(df_c, pd.DataFrame): df_c = df_c.iloc[:, 0]
        return df_c.dropna(), df
    except: return pd.Series(dtype=float), pd.DataFrame()

def obtener_fundamental_completo(symbol):
    try:
        t = yf.Ticker(symbol, session=yf_session)
        inf = t.info or {}
        px = DATOS_RADAR.get(symbol, {}).get("precio", safe_float(inf.get("currentPrice", 50.0)))
        pe = safe_float(inf.get("trailingPE", inf.get("forwardPE", 0.0)))
        eb = safe_float(inf.get("ebitda", 1.0))
        td = safe_float(inf.get("totalDebt", 0.0))
        caj = safe_float(inf.get("totalCash", 0.0))
        deuda = (td - caj) / eb if eb > 0 else 0.0
        return {
            "Ticker": symbol, "Nombre": inf.get("longName", symbol), "Precio": px,
            "PE": pe, "EV": safe_float(inf.get("enterpriseToEbitda", 0.0)),
            "DEUDA": deuda, "LIQUIDEZ": safe_float(inf.get("currentRatio", 0.0)),
            "MARGEN": safe_float(inf.get("profitMargins", 0.0)), "ROE": safe_float(inf.get("returnOnEquity", 0.0)),
            "RAW": inf
        }
    except:
        return {"Ticker": symbol, "Nombre": symbol, "Precio": 50.0, "PE": 0.0, "EV": 0.0, "DEUDA": 0.0, "LIQUIDEZ": 0.0, "MARGEN": 0.0, "ROE": 0.0, "RAW": {}}

# Session State para cartera
if "cartera_ops" not in st.session_state:
    st.session_state.cartera_ops = [
        {"Ticker": "VIST", "Nominales": 100, "PPC_ARS": 77200.0, "Dividendos_USD": 15.0},
        {"Ticker": "XOM", "Nominales": 50, "PPC_ARS": 31500.0, "Dividendos_USD": 25.5}
    ]

if "activo_analizado" not in st.session_state: st.session_state.activo_analizado = "VIST"
if "peers_analizados" not in st.session_state: st.session_state.peers_analizados = "YPF, XOM"

menu = st.radio("Secciones operativas:", ["🌐 DASHBOARD & WATCHLIST", "🔍 ANÁLISIS INTEGRAL & REVERSE DCF", "💼 CARTERA & ALLOCATION"], horizontal=True)
st.markdown("---")

# ==============================================================================
# 1. DASHBOARD & WATCHLIST
# ==============================================================================
if menu == "🌐 DASHBOARD & WATCHLIST":
    st.subheader("⚡ Monitor de Ruedas y Retornos Periódicos")
    if not DATOS_RADAR:
        st.warning("Sincronizando feed de mercado... Por favor recargar si persiste.")
    else:
        ordenados = sorted(DATOS_RADAR.items(), key=lambda x: x[1]["1D"], reverse=True)
        g1, g2 = st.columns(2)
        with g1:
            st.markdown(f"<div class='terminal-card green-card'>🟢 <b>Top Ganadores (1D):</b> 1. {ordenados[0][0]} ({ordenados[0][1]['1D']:+.2f}%) | 2. {ordenados[1][0]} ({ordenados[1][1]['1D']:+.2f}%) | 3. {ordenados[2][0]} ({ordenados[2][1]['1D']:+.2f}%)</div>", unsafe_allow_html=True)
        with g2:
            st.markdown(f"<div class='terminal-card' style='border-left: 3px solid #f43f5e;'>🔴 <b>Top Rezagados (1D):</b> 1. {ordenados[-1][0]} ({ordenados[-1][1]['1D']:+.2f}%) | 2. {ordenados[-2][0]} ({ordenados[-2][1]['1D']:+.2f}%) | 3. {ordenados[-3][0]} ({ordenados[-3][1]['1D']:+.2f}%)</div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📌 Watchlist Core (Performance Multitemporal)")
        filas_w = []
        for t in WATCHLIST_CORE:
            d = DATOS_RADAR.get(t, {"precio": 0.0, "1D": 0.0, "1M": 0.0, "6M": 0.0, "1Y": 0.0, "YTD": 0.0})
            px_ars = (d["precio"] / RATIOS_CEDEAR.get(t, 1)) * DOLAR_MEP
            filas_w.append({
                "Ticker": t, "Precio USD": f"${d['precio']:.2f}", "Cedear ARS": f"${px_ars:,.2f}",
                "1D": f"{d['1D']:+.2f}%", "1M": f"{d['1M']:+.2f}%", "6M": f"{d['6M']:+.2f}%",
                "1Y": f"{d['1Y']:+.2f}%", "YTD": f"{d['YTD']:+.2f}%"
            })
        st.dataframe(pd.DataFrame(filas_w).set_index("Ticker"), use_container_width=True)

# ==============================================================================
# 2. ANÁLISIS INTEGRAL (CON REVERSE DCF DE IA)
# ==============================================================================
elif menu == "🔍 ANÁLISIS INTEGRAL & REVERSE DCF":
    c_s1, c_s2 = st.columns([1, 2])
    t_obj = c_s1.selectbox("Activo Analizado:", UNIVERSO_POOL, index=UNIVERSO_POOL.index(st.session_state.activo_analizado)).upper().strip()
    t_comp_raw = c_s2.text_input("Peers de Referencia (Separados por coma):", value=st.session_state.peers_analizados).upper()
    
    if st.button("Ejecutar Análisis Cuantitativo"):
        st.session_state.activo_analizado = t_obj
        st.session_state.peers_analizados = t_comp_raw
        st.rerun()

    t_obj = st.session_state.activo_analizado
    peers = [c.strip() for c in st.session_state.peers_analizados.split(",") if c.strip()]
    lista_tickers = [t_obj] + peers
    dataset = [obtener_fundamental_completo(tk) for tk in lista_tickers]
    d_obj = dataset[0]
    info_raiz = d_obj["RAW"]
    serie_mc, df_raw = descargar_activo_individual_historico(t_obj)

    # Parámetros DCF Base
    shares = safe_float(info_raiz.get("sharesOutstanding", 0.20 * 1e9))
    ingresos = safe_float(info_raiz.get("totalRevenue", 10.0 * 1e9)) / 1e9
    wacc_base, g_terminal = 0.115, 0.02
    margen_base = d_obj["MARGEN"] if d_obj["MARGEN"] > 0 else 0.15
    precio_mkt = d_obj["Precio"]

    # Cálculo DCF Estocástico
    sims = 4000
    crec_sim = np.random.normal(0.07, 0.04, sims)
    mg_sim = np.random.normal(margen_base, 0.03, sims)
    vals_dcf = []
    for s in range(sims):
        ing = ingresos
        flujos = []
        for y in range(1, 6):
            ing *= (1 + crec_sim[s])
            flujos.append((ing * mg_sim[s] * 0.65) / ((1 + wacc_base)**y))
        vt = (ing * mg_sim[s] * 0.65 * (1 + g_terminal)) / (wacc_base - g_terminal)
        vals_dcf.append((sum(flujos) + (vt / ((1 + wacc_base)**5))) * 1e9 / shares)
    dcf_mediano = float(np.median([v for v in vals_dcf if v > 0])) if vals_dcf else precio_mkt

    # Cálculo Reverse DCF: ¿Qué 'g' implícito exige el precio de hoy?
    def obj_reverse_dcf(g_implied):
        ing = ingresos
        flujos = []
        for y in range(1, 6):
            ing *= (1 + g_implied)
            flujos.append((ing * margen_base * 0.65) / ((1 + wacc_base)**y))
        vt = (ing * margen_base * 0.65 * (1 + g_terminal)) / (wacc_base - g_terminal)
        eq_val = (sum(flujos) + (vt / ((1 + wacc_base)**5))) * 1e9 / shares
        return abs(eq_val - precio_mkt)

    res_opt = sco.minimize(obj_reverse_dcf, [0.06], bounds=[(-0.15, 0.50)], method='Nelder-Mead')
    g_implicito = float(res_opt.x[0])

    tab_fund, tab_rev_dcf, tab_tech, tab_mc = st.tabs(["📊 Balances & Ratios", "🎯 Reverse DCF (IA)", "📈 Técnico (DMI)", "🎲 Montecarlo Precios"])

    # --- PESTAÑA 1: FUNDAMENTAL ---
    with tab_fund:
        st.markdown(f"### 🏢 Perfil Corporativo: {d_obj['Nombre']}")
        resumen_empresa = ia_sintesis_empresa(t_obj, d_obj["Nombre"], {"deuda": d_obj["DEUDA"], "margen": d_obj["MARGEN"], "roe": d_obj["ROE"]})
        st.markdown(f"<div class='terminal-card blue-card'>{resumen_empresa.replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)

        c_w1, c_w2 = st.columns([1, 2])
        with c_w1:
            st.markdown("#### Consenso Analistas Sell-Side")
            recom = str(info_raiz.get("recommendationKey", "hold")).lower()
            val_gauge = 5 if "strong_buy" in recom or "strong buy" in recom else 4 if "buy" in recom else 2 if "sell" in recom else 3
            fig_g = go.Figure(go.Indicator(
                mode="gauge+number", value=val_gauge,
                title={'text': "Consenso (1 Venta a 5 Compra)", 'font': {'size': 11, 'color': '#94a3b8'}},
                gauge={'axis': {'range': [1, 5], 'tickvals': [1, 2, 3, 4, 5], 'ticktext': ['Venta F.', 'Venta', 'Mantener', 'Compra', 'Compra F.']},
                       'bar': {'color': "#d4a34b"},
                       'steps': [{'range': [1, 2.5], 'color': "rgba(244, 63, 94, 0.2)"}, {'range': [2.5, 3.5], 'color': "rgba(255, 255, 255, 0.05)"}, {'range': [3.5, 5], 'color': "rgba(16, 185, 129, 0.2)"}]}
            ))
            fig_g.update_layout(height=190, margin=dict(l=10, r=10, t=20, b=10), paper_bgcolor='#0d111a', font={'color': '#ffffff'})
            st.plotly_chart(fig_g, use_container_width=True)
            st.caption("ℹ️ *Fuente: Relevamiento institucional vía Yahoo Finance / LSEG.*")

        with c_w2:
            st.markdown("#### Calidad de Balances (TTM vs Estimación)")
            eps_trail = safe_float(info_raiz.get("trailingEps", 0.0))
            eps_fwd = safe_float(info_raiz.get("forwardEps", eps_trail))
            rev_tot = safe_float(info_raiz.get("totalRevenue", 0.0)) / 1e9
            gross_prof = safe_float(info_raiz.get("grossProfits", rev_tot * 0.4 * 1e9)) / 1e9

            # Tabla construida sin indentaciones accidentales
            filas_bal = [
                f"<tr><td><b>EPS (Ganancia por Acción)</b></td><td>${eps_trail:.2f}</td><td>${eps_fwd:.2f}</td><td style='color: {'#34d399' if eps_fwd >= eps_trail else '#f43f5e'}; font-weight:bold;'>{(((eps_fwd/eps_trail)-1)*100 if eps_trail > 0 else 0.0):+.2f}%</td></tr>",
                f"<tr><td><b>Ingresos (Revenue)</b></td><td>${rev_tot:.2f} B</td><td>${gross_prof:.2f} B (Gross Profit)</td><td style='color: #34d399; font-weight:bold;'>{(gross_prof/rev_tot*100 if rev_tot>0 else 0):.1f}% Margen Bruto</td></tr>"
            ]
            tabla_bal_html = "<div class='table-viewport'><table class='terminal-table'><thead><tr><th>Métrica Contable</th><th>Últimos 12M</th><th>Consenso Siguiente Ejercicio</th><th>Variación</th></tr></thead><tbody>" + "".join(filas_bal) + "</tbody></table></div>"
            st.markdown(tabla_bal_html, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### Matriz Comparativa Relativa vs Peers")
        
        t_pe = "P/E: Cuántas veces ganancias descuenta la cotización actual."
        t_ev = "EV/EBITDA: Valuación total del negocio sobre su flujo antes de intereses e impuestos."
        t_deuda = "Deuda Neta/EBITDA: Cobertura del pasivo financiero exigible frente a la caja anual."
        t_liq = "Liquidez Corriente: Respaldo de corto plazo activo/pasivo (>1.0x deseable)."
        t_mg = "Margen Neto: Utilidad líquida final resultante por cada $100 facturados."
        t_roe = "ROE: Retorno generado sobre el patrimonio contable de los accionistas."

        validos_pe = [d for d in dataset if d["PE"] > 0]
        g_pe = min(validos_pe, key=lambda x: x["PE"])["Ticker"] if validos_pe else ""
        g_roe = max(dataset, key=lambda x: x["ROE"])["Ticker"] if dataset else ""

        filas_peers = []
        for r in dataset:
            c_pe = "class='winner-cell'" if r["Ticker"] == g_pe and g_pe != "" else ""
            c_roe = "class='winner-cell'" if r["Ticker"] == g_roe and g_roe != "" else ""
            filas_peers.append(f"<tr><td><b>{r['Ticker']}</b></td><td>{r['Nombre']}</td><td {c_pe}>{r['PE']:.2f}x</td><td>{r['EV']:.2f}x</td><td>{r['DEUDA']:.2f}x</td><td>{r['LIQUIDEZ']:.2f}x</td><td>{r['MARGEN']*100:.1f}%</td><td {c_roe}>{r['ROE']*100:.1f}%</td></tr>")

        matriz_html = f"<div class='table-viewport'><table class='terminal-table'><thead><tr><th>Ticker</th><th>Razón Social</th><th>P/E <span class='th-tooltip'>ⓘ<span class='th-tooltiptext'>{t_pe}</span></span></th><th>EV/EBITDA <span class='th-tooltip'>ⓘ<span class='th-tooltiptext'>{t_ev}</span></span></th><th>Deuda <span class='th-tooltip'>ⓘ<span class='th-tooltiptext'>{t_deuda}</span></span></th><th>Liquidez <span class='th-tooltip'>ⓘ<span class='th-tooltiptext'>{t_liq}</span></span></th><th>Margen <span class='th-tooltip'>ⓘ<span class='th-tooltiptext'>{t_mg}</span></span></th><th>ROE <span class='th-tooltip'>ⓘ<span class='th-tooltiptext'>{t_roe}</span></span></th></tr></thead><tbody>" + "".join(filas_peers) + "</tbody></table></div>"
        st.markdown(matriz_html, unsafe_allow_html=True)

        if g_pe == g_roe and g_pe != "":
            diag = f"<b>{g_pe}</b> exhibe liderazgo dual en el lote analizado: combina el mayor retorno de capital contable (ROE) con la valuación más atractiva por ratio P/E, ofreciendo margen de seguridad relativo."
        else:
            diag = f"<b>{g_roe}</b> encabeza el grupo en eficiencia y retorno de patrimonio (ROE), mientras que <b>{g_pe}</b> otorga el menor múltiplo P/E para entradas a múltiplos comprimidos."
        st.markdown(f"<div class='terminal-card gold-card'><b>Conclusión de Múltiplos:</b> {diag}</div>", unsafe_allow_html=True)

        # Botón de Tesis Automatizada
        st.markdown("---")
        if st.button(f"✨ Emitir Dictamen Ejecutivo de Inversión ({t_obj})"):
            st.session_state[f"tesis_{t_obj}"] = ia_tesis_ejecutiva(
                t_obj, d_obj["Nombre"], d_obj["Precio"], d_obj["PE"],
                d_obj["ROE"], d_obj["DEUDA"], d_obj["MARGEN"], dcf_mediano
            )
        if f"tesis_{t_obj}" in st.session_state:
            st.markdown(f"<div class='terminal-card blue-card'>{st.session_state[f'tesis_{t_obj}']}</div>", unsafe_allow_html=True)

    # --- PESTAÑA 2: REVERSE DCF (FEATURE DIFERENCIAL) ---
    with tab_rev_dcf:
        st.markdown(f"### 🎯 Reverse DCF & Market Expectations: {t_obj}")
        st.markdown("""<div class='terminal-card'>
        <b>Enfoque de Expectativas Implícitas (Michael Mauboussin):</b> En lugar de predecir el futuro, este modelo invierte la fórmula del DCF para responder: <i>¿Qué tasa anual de crecimiento de Flujo Libre ($g$) descuenta el precio actual de mercado ($""" + f"{precio_mkt:.2f}" + """ USD)?</i> Luego, la IA evalúa la probabilidad real de que la empresa logre esa meta.
        </div>""", unsafe_allow_html=True)

        col_r1, col_r2 = st.columns(2)
        col_r1.metric("Crecimiento de FCF Anual Exigido por el Mercado (5A)", f"{g_implicito*100:+.1f}%")
        col_r2.metric("Retorno sobre Capital Actual (ROE)", f"{d_obj['ROE']*100:.1f}%")

        diagnostico_ia_rdcf = ia_reverse_dcf_check(t_obj, g_implicito, d_obj["ROE"], d_obj["PE"])
        st.markdown(f"<div class='terminal-card gold-card'><b>Evaluación de Viabilidad Cuantitativa:</b><br>{diagnostico_ia_rdcf}</div>", unsafe_allow_html=True)

    # --- PESTAÑA 3: ANÁLISIS TÉCNICO DMI ---
    with tab_tech:
        st.markdown(f"### 📈 Fuerza Tendencial y Timing (DMI / ADX): {t_obj}")
        if not df_raw.empty and 'High' in df_raw.columns:
            df_t = df_raw.copy()
            df_t['EMA30'] = df_t['Close'].ewm(span=30, adjust=False).mean()
            up, down = df_t['High'].diff(), -df_t['Low'].diff()
            pdm = np.where((up > down) & (up > 0), up, 0.0)
            mdm = np.where((down > up) & (down > 0), down, 0.0)
            tr = pd.DataFrame({'tr1': df_t['High']-df_t['Low'], 'tr2': abs(df_t['High']-df_t['Close'].shift(1)), 'tr3': abs(df_t['Low']-df_t['Close'].shift(1))}).max(axis=1)
            trs = tr.rolling(14).sum()
            df_t['+DI'] = 100 * (pd.Series(pdm, index=df_t.index).rolling(14).sum() / trs)
            df_t['-DI'] = 100 * (pd.Series(mdm, index=df_t.index).rolling(14).sum() / trs)
            df_t['ADX'] = (100 * abs(df_t['+DI'] - df_t['-DI']) / (df_t['+DI'] + df_t['-DI'])).rolling(14).mean()
            df_t = df_t.dropna()

            fig_d = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.65, 0.35], vertical_spacing=0.04)
            fig_d.add_trace(go.Scatter(x=df_t.index, y=df_t['Close'], name="Precio", line=dict(color='#ffffff', width=1.5)), row=1, col=1)
            fig_d.add_trace(go.Scatter(x=df_t.index, y=df_t['EMA30'], name="EMA 30", line=dict(color='#d4a34b', dash='dash', width=1.2)), row=1, col=1)
            fig_d.add_trace(go.Scatter(x=df_t.index, y=df_t['+DI'], name="+DI", line=dict(color='#10b981', width=1.2)), row=2, col=1)
            fig_d.add_trace(go.Scatter(x=df_t.index, y=df_t['-DI'], name="-DI", line=dict(color='#f43f5e', width=1.2)), row=2, col=1)
            fig_d.add_trace(go.Scatter(x=df_t.index, y=df_t['ADX'], name="ADX", line=dict(color='#0284c7', width=1.5)), row=2, col=1)
            fig_d.update_layout(template="plotly_dark", paper_bgcolor='#0d111a', plot_bgcolor='#06080d', height=380, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_d, use_container_width=True)

            di_p, di_m, adx_val = df_t['+DI'].iloc[-1], df_t['-DI'].iloc[-1], df_t['ADX'].iloc[-1]
            soporte = df_t['Low'].tail(30).min()
            resistencia = df_t['High'].tail(30).max()
            
            l1 = f"• <b>Dinámica y Momentum:</b> {'Presión compradora activa (+DI > -DI)' if di_p > di_m else 'Presión vendedora activa (-DI > +DI)'}, con un ADX en {adx_val:.1f} pts que ratifica {'fuerza direccional institucional activa (>25)' if adx_val > 25 else 'movimiento lateral o falta de inercia tendencial (<25)'}."
            l2 = f"• <b>Comportamiento vs Tendencia:</b> Cotiza {'por sobre su media exponencial de 30 ruedas, conservando estructura favorable' if df_t['Close'].iloc[-1] >= df_t['EMA30'].iloc[-1] else 'por debajo de la media de 30 ruedas, exigiendo cautela táctica en entradas largas'}."
            l3 = f"• <b>Niveles de Referencia:</b> Soporte crítico en <b>${soporte:.2f} USD</b> para control de drawdown y resistencia inmediata en <b>${resistencia:.2f} USD</b>."
            st.markdown(f"<div class='terminal-card'><b>Lectura Técnica (3 Renglones):</b><br>{l1}<br>{l2}<br>{l3}</div>", unsafe_allow_html=True)

    # --- PESTAÑA 4: MONTECARLO ---
    with tab_mc:
        st.markdown("### 🎲 Simulación Estocástica de Cotización (GBM)")
        if not serie_mc.empty:
            ret = serie_mc.pct_change().dropna()
            sigma, mu_d = ret.std(), ret.mean() - 0.5 * (ret.std() ** 2)
            px_0 = float(serie_mc.iloc[-1])
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### Cono de Dispersión: 30 Ruedas")
                m_30 = np.zeros((30, 800))
                m_30[0] = px_0
                z_30 = np.random.standard_normal((29, 800))
                for t in range(1, 30): m_30[t] = m_30[t-1] * np.exp(mu_d + sigma * z_30[t-1])
                f30 = go.Figure()
                for i in range(25): f30.add_trace(go.Scatter(y=m_30[:, i], mode='lines', line=dict(color='rgba(2, 132, 199, 0.07)'), showlegend=False))
                f30.add_trace(go.Scatter(y=np.median(m_30, axis=1), mode='lines', line=dict(color='#d4a34b', width=2), name="Mediana"))
                f30.update_layout(template="plotly_dark", paper_bgcolor='#0d111a', plot_bgcolor='#06080d', height=250, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(f30, use_container_width=True)
            with c2:
                st.markdown("#### Cono de Dispersión: 1 Año (252 Ruedas)")
                m_252 = np.zeros((252, 800))
                m_252[0] = px_0
                z_252 = np.random.standard_normal((251, 800))
                for t in range(1, 252): m_252[t] = m_252[t-1] * np.exp(mu_d + sigma * z_252[t-1])
                f252 = go.Figure()
                for i in range(25): f252.add_trace(go.Scatter(y=m_252[:, i], mode='lines', line=dict(color='rgba(212, 163, 75, 0.07)'), showlegend=False))
                f252.add_trace(go.Scatter(y=np.median(m_252, axis=1), mode='lines', line=dict(color='#10b981', width=2), name="Mediana"))
                f252.update_layout(template="plotly_dark", paper_bgcolor='#0d111a', plot_bgcolor='#06080d', height=250, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(f252, use_container_width=True)

# ==============================================================================
# 3. CARTERA, SEGUIMIENTO Y ASIGNACIÓN ÓPTIMA
# ==============================================================================
elif menu == "💼 CARTERA & ALLOCATION":
    st.subheader("💼 Gestión de Portafolio Consolidado (Tracking y PPC)")

    with st.expander("➕ Registrar Nueva Operación / Promediar Activo (PPC)"):
        f1, f2, f3, f4 = st.columns(4)
        n_tk = f1.selectbox("Ticker:", UNIVERSO_POOL, index=0)
        n_cant = f2.number_input("Nominales:", min_value=1, value=50, step=10)
        n_moneda = f3.selectbox("Moneda de Compra:", ["ARS (Cedear)", "USD (Acción Original)"])
        n_precio = f4.number_input("Precio Unitario Pagado:", min_value=1.0, value=75000.0 if "ARS" in n_moneda else 50.0, step=100.0)
        
        if st.button("Guardar Operación"):
            ratio_tk = RATIOS_CEDEAR.get(n_tk, 1)
            px_ars = n_precio if "ARS" in n_moneda else ((n_precio * DOLAR_MEP) / ratio_tk)
            pos_existente = next((p for p in st.session_state.cartera_ops if p["Ticker"] == n_tk), None)
            if pos_existente:
                c_ant, p_ant = pos_existente["Nominales"], pos_existente["PPC_ARS"]
                c_nueva = c_ant + n_cant
                pos_existente["Nominales"] = c_nueva
                pos_existente["PPC_ARS"] = ((c_ant * p_ant) + (n_cant * px_ars)) / c_nueva
                st.success(f"PPC actualizado para {n_tk}: ${pos_existente['PPC_ARS']:,.2f} ARS ({c_nueva} nominales).")
            else:
                st.session_state.cartera_ops.append({"Ticker": n_tk, "Nominales": n_cant, "PPC_ARS": px_ars, "Dividendos_USD": 0.0})
                st.success(f"Posición {n_tk} dada de alta exitosamente.")
            st.rerun()

    is_ars = st.radio("Moneda de visualización:", ["ARS", "USD"], horizontal=True) == "ARS"
    
    # Procesamiento y construcción segura de la tabla de cartera
    c_tot_usd, v_tot_usd, div_tot_usd = 0.0, 0.0, 0.0
    filas_html_cartera = []

    for pos in st.session_state.cartera_ops:
        tk, nom, ppc_ars, divs = pos["Ticker"], pos["Nominales"], pos["PPC_ARS"], pos.get("Dividendos_USD", 0.0)
        ratio = RATIOS_CEDEAR.get(tk, 1)
        px_actual_usd = DATOS_RADAR.get(tk, {}).get("precio", (ppc_ars * ratio / DOLAR_MEP))
        
        costo_usd = ((nom * ppc_ars) / DOLAR_MEP) * ratio
        val_usd = nom * px_actual_usd
        pl_usd = (val_usd + divs) - costo_usd
        ret_pct = (pl_usd / costo_usd) * 100 if costo_usd > 0 else 0.0
        
        c_tot_usd += costo_usd
        v_tot_usd += val_usd
        div_tot_usd += divs
        
        ppc_view = ppc_ars if is_ars else (ppc_ars * ratio / DOLAR_MEP)
        px_view = (px_actual_usd * DOLAR_MEP / ratio) if is_ars else px_actual_usd
        costo_view = costo_usd * (DOLAR_MEP if is_ars else 1.0)
        val_view = val_usd * (DOLAR_MEP if is_ars else 1.0)
        pl_view = pl_usd * (DOLAR_MEP if is_ars else 1.0)
        
        if ret_pct >= 20.0:
            badge = "<span class='badge-state badge-hold'>🟡 MANTENER / RENTABILIZAR</span>"
            tip_txt = f"Ganancia superior al +20% ({ret_pct:+.1f}%). Sostener posición con trailing stop o toma parcial."
        elif ret_pct <= -12.0:
            badge = "<span class='badge-state badge-sell'>🔴 REVISAR / STOP LOSS</span>"
            tip_txt = f"Pérdida acumulada del {ret_pct:+.1f}%. Precio perforó umbrales de tolerancia frente al PPC."
        else:
            badge = "<span class='badge-state badge-buy'>🟢 COMPRA / ACUMULAR</span>"
            tip_txt = f"Desempeño equilibrado ({ret_pct:+.1f}%). Rango apto para promediar o añadir nominales."
            
        badge_html = f"<div class='th-tooltip'>{badge}<span class='th-tooltiptext'>{tip_txt}</span></div>"
        
        # Inyección directa de fila sin sangrías de 4 espacios
        fila = f"<tr><td><b>{tk}</b></td><td>{nom}</td><td>${ppc_view:,.2f}</td><td>${px_view:,.2f}</td><td>${costo_view:,.2f}</td><td>${val_view:,.2f}</td><td style='color: {'#34d399' if pl_usd >= 0 else '#f43f5e'}; font-weight:bold;'>${pl_view:,.2f}</td><td style='color: {'#34d399' if ret_pct >= 0 else '#f43f5e'}; font-weight:bold;'>{ret_pct:+.2f}%</td><td>{badge_html}</td></tr>"
        filas_html_cartera.append(fila)

    # Render limpio de tabla
    tabla_cartera_completa = "<div class='table-viewport'><table class='terminal-table'><thead><tr><th>Ticker</th><th>Nominales</th><th>PPC</th><th>Precio Actual</th><th>Invertido</th><th>Valuación</th><th>P&L Neto</th><th>Total Return</th><th>Semáforo Táctico</th></tr></thead><tbody>" + "".join(filas_html_cartera) + "</tbody></table></div>"
    st.markdown(tabla_cartera_completa, unsafe_allow_html=True)

    # Métricas Consolidadas
    st.markdown("#### Métricas Consolidadas")
    k1, k2, k3, k4, k5 = st.columns(5)
    ret_total_cartera = ((v_tot_usd + div_tot_usd - c_tot_usd) / c_tot_usd) * 100 if c_tot_usd > 0 else 0.0
    mon_lbl = "ARS" if is_ars else "USD"
    conv_f = DOLAR_MEP if is_ars else 1.0
    spy_ret = DATOS_RADAR.get("SPY", {}).get("YTD", 0.0)
    alpha_spy = ret_total_cartera - spy_ret

    k1.metric("Capital Invertido", f"${(c_tot_usd*conv_f):,.0f} {mon_lbl}")
    k2.metric("Valuación Actual", f"${(v_tot_usd*conv_f):,.0f} {mon_lbl}")
    k3.metric("Rentas/Divs", f"${(div_tot_usd*conv_f):,.0f} {mon_lbl}")
    k4.metric("Total Return", f"{ret_total_cartera:+.2f}%")
    k5.metric("Alpha vs SPY", f"{alpha_spy:+.2f}%", delta_color="normal" if alpha_spy >= 0 else "inverse")

    # Benchmark Curva
    st.markdown("---")
    st.markdown("#### Curva de Desempeño: Cartera vs. SPY vs. QQQ (Base 100)")
    try:
        tks_bench = list(set([p["Ticker"] for p in st.session_state.cartera_ops] + ["SPY", "QQQ"]))
        _, df_b = descargar_datos_mercado(tks_bench)
        if not df_b.empty and 'SPY' in df_b.columns and 'QQQ' in df_b.columns:
            weights = {p["Ticker"]: (p["Nominales"] * DATOS_RADAR.get(p["Ticker"], {}).get("precio", 100)) for p in st.session_state.cartera_ops}
            w_sum = sum(weights.values())
            weights = {k: v / w_sum for k, v in weights.items()}
            
            df_norm = pd.DataFrame(index=df_b.index)
            cartera_serie = sum(df_b[tk] / df_b[tk].iloc[0] * weights[tk] for tk in weights if tk in df_b.columns)
            
            df_norm["Mi Cartera"] = (cartera_serie - 1) * 100
            df_norm["S&P 500 (SPY)"] = ((df_b["SPY"] / df_b["SPY"].iloc[0]) - 1) * 100
            df_norm["Nasdaq 100 (QQQ)"] = ((df_b["QQQ"] / df_b["QQQ"].iloc[0]) - 1) * 100
            
            fig_bench = px.line(df_norm, y=["Mi Cartera", "S&P 500 (SPY)", "Nasdaq 100 (QQQ)"],
                                color_discrete_map={"Mi Cartera": "#10b981", "S&P 500 (SPY)": "#0284c7", "Nasdaq 100 (QQQ)": "#d4a34b"})
            fig_bench.update_layout(template="plotly_dark", paper_bgcolor='#0d111a', plot_bgcolor='#06080d', height=340, yaxis_title="Retorno Acumulado (%)")
            st.plotly_chart(fig_bench, use_container_width=True)
    except Exception as e:
        st.caption(f"Curva en actualización: {e}")

    # Markowitz
    st.markdown("---")
    st.subheader("🧠 Asignación Óptima de Portafolio (Markowitz - Max Sharpe)")
    if st.button("Calcular Frontera Eficiente"):
        tks_port = list(set([p["Ticker"] for p in st.session_state.cartera_ops]))
        if len(tks_port) < 2:
            st.error("Se requieren al menos 2 activos distintos para computar la covarianza.")
        else:
            _, df_opt = descargar_datos_mercado(tks_port)
            rets = df_opt[tks_port].pct_change().dropna()
            mean_ret = rets.mean() * 252
            cov_mat = rets.cov() * 252
            
            def min_sharpe(w):
                p_r = np.sum(mean_ret * w)
                p_v = np.sqrt(np.dot(w.T, np.dot(cov_mat, w)))
                return -(p_r - 0.04) / p_v
                
            n = len(tks_port)
            res = sco.minimize(min_sharpe, n * [1./n], method='SLSQP', bounds=tuple((0, 1) for _ in range(n)), constraints=({'type': 'eq', 'fun': lambda x: np.sum(x) - 1}))
            
            fig_pie = px.pie(values=res.x, names=tks_port, title="Ponderaciones Sugeridas", hole=0.45,
                             color_discrete_sequence=['#d4a34b', '#0284c7', '#10b981', '#f43f5e', '#a855f7'])
            fig_pie.update_layout(template="plotly_dark", paper_bgcolor='#0d111a', plot_bgcolor='#06080d')
            st.plotly_chart(fig_pie, use_container_width=True)

# ==============================================================================
# FOOTER INSTITUCIONAL
# ==============================================================================
st.markdown("---")
st.markdown("<p style='text-align: right; font-size: 11px; color: #64748b;'>Terminal Institucional Cuantitativa | Desarrollado por <a href='https://www.linkedin.com/in/facundo-garciamarquez/?locale=es' target='_blank' style='color: #d4a34b; text-decoration: none; font-weight: 600;'>Facundo Garcia Marquez</a></p>", unsafe_allow_html=True)
st.markdown("""<div style='background-color: rgba(244, 63, 94, 0.05); padding: 8px 12px; border-left: 2px solid #f43f5e; font-size: 10.5px; color: #64748b;'>
<strong>Aviso Legal:</strong> Este software es una herramienta de simulación analítica y valuación financiera estocástica. No constituye asesoramiento de inversión ni oferta pública.
</div>""", unsafe_allow_html=True)
