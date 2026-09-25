# -*- coding: utf-8 -*-
import warnings
warnings.filterwarnings("ignore")

import io
import datetime
import requests
from bs4 import BeautifulSoup

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import scipy.optimize as sco

# Librería para exportación institucional en PDF
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

# ------------------------------------------------------------------------------
# CONFIGURACIÓN GENERAL Y ESTILO OBSIDIAN & BRASS
# ------------------------------------------------------------------------------
st.set_page_config(page_title="Apex Financial Terminal", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"], [data-testid="stAppViewContainer"], [data-testid="stHeader"] { 
    background-color: #06080d !important; 
    color: #e2e8f0 !important; 
    font-family: 'Plus Jakarta Sans', sans-serif !important; 
}

.tabular-nums, td, div[data-testid="stMetricValue"] > div {
    font-family: 'JetBrains Mono', monospace !important;
    font-variant-numeric: tabular-nums !important;
}

.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
h1 { font-weight: 800; color: #ffffff !important; font-size: 26px !important; letter-spacing: -0.02em; }
h2 { font-weight: 700; color: #f8fafc !important; font-size: 19px !important; }
h3 { font-weight: 600; color: #cbd5e1 !important; font-size: 15px !important; }

div[data-testid="stRadio"] > div { 
    background: #0d111a !important; 
    padding: 6px !important; 
    border-radius: 8px !important; 
    border: 1px solid rgba(255, 255, 255, 0.08) !important; 
    display: flex !important;
    gap: 8px !important; 
    margin-bottom: 18px !important; 
}
div[data-testid="stRadio"] label[data-baseweb="radio"] { 
    padding: 6px 16px !important; 
    border-radius: 6px !important; 
    color: #94a3b8 !important; 
    font-weight: 600 !important; 
    font-size: 12px !important;
}
div[data-testid="stRadio"] label[data-baseweb="radio"]:hover { color: #f8fafc !important; }

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

.table-viewport { overflow: visible !important; position: relative; margin: 10px 0; }
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
    padding: 10px 12px; 
    text-align: left; 
    font-weight: 600; 
    border-bottom: 1px solid rgba(255, 255, 255, 0.08); 
    font-size: 11px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.terminal-table td { 
    padding: 10px 12px; 
    border-bottom: 1px solid rgba(255, 255, 255, 0.04); 
    color: #e2e8f0; 
}
.terminal-table tr:hover td { background-color: rgba(255, 255, 255, 0.02); }
.winner-cell { background-color: rgba(212, 163, 75, 0.12) !important; color: #e5a93c !important; font-weight: 700; }

.th-tooltip { position: relative; display: inline-block; cursor: pointer; color: #38bdf8; margin-left: 4px; font-weight: 700; }
.th-tooltip .th-tooltiptext {
    visibility: hidden; width: 240px; background-color: #121824; color: #f1f5f9; text-align: left;
    padding: 8px 10px; border-radius: 5px; position: absolute; z-index: 9999; bottom: 130%; left: 50%;
    transform: translateX(-50%); opacity: 0; transition: opacity 0.2s; font-size: 11px; font-weight: 400;
    line-height: 1.4; border: 1px solid rgba(56, 189, 248, 0.4); box-shadow: 0 8px 20px rgba(0,0,0,0.8); pointer-events: none;
}
.th-tooltip:hover .th-tooltiptext { visibility: visible; opacity: 1; }

.badge-state { display: inline-block; padding: 2px 7px; border-radius: 4px; font-weight: 700; font-size: 10.5px; }
.badge-buy { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); }
.badge-hold { background: rgba(212, 163, 75, 0.15); color: #fbbf24; border: 1px solid rgba(212, 163, 75, 0.4); }
.badge-sell { background: rgba(244, 63, 94, 0.15); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.4); }

.radar-card-item {
    background-color: #121824;
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 6px;
    padding: 12px 16px;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
</style>""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# CONEXIÓN GEMINI AI
# ------------------------------------------------------------------------------
try:
    import google.generativeai as genai
    HAS_GEMINI_LIB = True
except ImportError:
    HAS_GEMINI_LIB = False

st.sidebar.markdown("### 🔑 Conexión AI")
secrets_key = st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, "secrets") else ""
gemini_input_key = st.sidebar.text_input("Gemini API Key:", value=secrets_key, type="password")

GEMINI_KEY = gemini_input_key.strip() if gemini_input_key else None
if HAS_GEMINI_LIB and GEMINI_KEY:
    try:
        genai.configure(api_key=GEMINI_KEY)
    except:
        pass

def ia_perfil_analista_senior(ticker, nombre, info_dict):
    """Genera perfil con tono y profundidad de Research Buy-Side (Máx 5 líneas compactas)."""
    deuda = info_dict.get('deuda', 0.0)
    margen = info_dict.get('margen', 0.0)
    roe = info_dict.get('roe', 0.0)
    
    if HAS_GEMINI_LIB and GEMINI_KEY:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = f"""
            Actúa como un Senior Equity Research Analyst y Portfolio Manager de Wall Street.
            Elabora una radiografía operativa profunda y profesional de {nombre} ({ticker}) en exactamente 5 renglones corridos:
            - Renglones 1-2: Core business, economía unitaria, poder de fijación de precios y barreras de entrada (Economic Moat).
            - Renglones 3-4: Asignación de capital, ciclo de CapEx y metas operativas de su guidance directivo.
            - Renglón 5: Salud del balance frente al ciclo (Deuda Neta/EBITDA de {deuda:.2f}x, Margen Neto del {margen*100:.1f}% y ROE del {roe*100:.1f}%).
            Sé riguroso, usa terminología financiera institucional y no uses introducciones vacías.
            """
            res = model.generate_content(prompt)
            if res and res.text: return res.text.strip()
        except: pass
        
    return (
        f"{nombre} ({ticker}) sostiene su modelo en activos estratégicos con ventajas de escala y capacidad de fijación de precios en su segmento.\n"
        f"La asignación de capital prioriza proyectos de alta tasa interna de retorno (TIR), disciplinando el CapEx hacia eficiencias operativas.\n"
        f"Su balance exhibe una solvencia con ratio Deuda Neta/EBITDA de {deuda:.2f}x, respaldado por un margen neto del {margen*100:.1f}% y un ROE del {roe*100:.1f}%."
    )

def ia_analisis_multiplos_profundo(d_obj, dataset):
    """Genera una interpretación de múltiplos fundada en DuPont, estructura de capital y calidad de ganancias."""
    if HAS_GEMINI_LIB and GEMINI_KEY:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = f"""
            Actúa como Portfolio Manager. Analiza la valuación de {d_obj['Ticker']} frente a sus comparables ({', '.join([d['Ticker'] for d in dataset if d['Ticker'] != d_obj['Ticker']])}):
            Métricas de {d_obj['Ticker']}: P/E {d_obj['PE']:.2f}x, EV/EBITDA {d_obj['EV']:.2f}x, Deuda Neta/EBITDA {d_obj['DEUDA']:.2f}x, Margen Neto {d_obj['MARGEN']*100:.1f}%, ROE {d_obj['ROE']*100:.1f}%.
            Datos de los peers: {[{d['Ticker']: {'PE': d['PE'], 'EV': d['EV'], 'ROE': d['ROE'], 'Deuda': d['DEUDA']}} for d in dataset if d['Ticker'] != d_obj['Ticker']]}
            
            Redacta en un único párrafo de 4 renglones un razonamiento que no se limite a leer los números:
            - Explica si el P/E refleja una oportunidad genuina de descalce o un 'Value Trap' por deterioro estructural.
            - Evalúa si el ROE proviene de eficiencia de margen o de apalancamiento financiero excesivo (Lógica DuPont).
            - Concluye si la dispersión de múltiplos otorga un punto de entrada con margen de seguridad.
            """
            res = model.generate_content(prompt)
            if res and res.text: return res.text.strip()
        except: pass
        
    return (
        f"La valuación de {d_obj['Ticker']} a {d_obj['PE']:.2f}x utilidades frente al promedio del grupo refleja un descuento relativo justificado "
        f"por su perfil de riesgo. Su ROE del {d_obj['ROE']*100:.1f}%, contrastado con una carga de deuda neta de {d_obj['DEUDA']:.2f}x EBITDA, confirma "
        f"que la rentabilidad sobre capital deriva de productividad operativa y márgenes sostenibles ({d_obj['MARGEN']*100:.1f}%), minimizando "
        f"el riesgo de value trap y ofreciendo un punto de entrada con margen de seguridad razonable."
    )

def ia_tesis_macro_coyuntura(ticker, nombre, precio, pe, roe, deuda, margen, dcf_valor):
    """Párrafo cohesionado que conecta el valor del activo con la coyuntura macro global y local."""
    upside = ((dcf_valor - precio) / precio) * 100 if precio > 0 else 0
    if HAS_GEMINI_LIB and GEMINI_KEY:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = f"""
            Actúa como Chief Investment Officer (CIO). Redacta una tesis ejecutiva en UN SOLO PÁRRAFO FLUIDO (5 renglones) para {nombre} ({ticker}):
            - Precio actual: ${precio:.2f} USD vs Fair Value DCF: ${dcf_valor:.2f} USD (Upside: {upside:+.1f}%).
            - Fundamentales: P/E {pe:.1f}x, ROE {roe*100:.1f}%, Margen {margen*100:.1f}%, Deuda Neta/EBITDA {deuda:.2f}x.
            
            Integra la coyuntura macroeconómica actual (ciclo de tasas de la Reserva Federal, dinámicas de inflación global y sensibilidad al riesgo soberano/cambiario de la región). 
            Emite una conclusión taxativa sobre si es momento de Acumular, Mantener o Liquidar la posición.
            """
            res = model.generate_content(prompt)
            if res and res.text: return res.text.strip()
        except: pass
        
    sentido = "Acumular con horizonte táctico" if upside > 15 else "Mantener en cartera core" if upside >= -10 else "Reducir exposición"
    return (
        f"Frente al actual ciclo monetario restrictivo y la volatilidad en las primas de riesgo emergentes, {ticker} cotiza con un descalce del {upside:+.1f}% "
        f"frente a su valor intrínseco estimado por flujos (${dcf_valor:.2f} USD). Su margen neto del {margen*100:.1f}% y el apalancamiento contenido en {deuda:.2f}x EBITDA "
        f"le permiten navegar entornos de financiamiento exigente sin deteriorar su capacidad de reinversión. En consecuencia, el balance de riesgo/retorno "
        f"recomienda {sentido}, condicionando la estrategia a la estabilidad de los flujos de exportación y la disciplina de gasto operativo."
    )

# ------------------------------------------------------------------------------
# UNIVERSO DE 100 ACTIVOS LÍDERES EN ARGENTINA (MERVAL + CEDEARS)
# ------------------------------------------------------------------------------
TOP_100_ARG = [
    # Merval Líderes y General
    "GGAL", "YPF", "PAMP", "TXAR", "ALUA", "BMA", "CEPU", "CRES", "EDN", "BYMA",
    "VALO", "COME", "BBAR", "TECO2", "LOMA", "TGSU2", "TGNO4", "TRAN", "MIRG", "SUPV",
    "IRSA", "CVH", "METR", "AUSO", "HARG", "MOLI", "LEDE", "SEMI", "INVJ", "BOLT",
    # CEDEARs Top Volumen Acciones
    "VIST", "AAPL", "NVDA", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "KO", "XOM",
    "PBR", "MELI", "GLOB", "DESP", "NU", "BBD", "ITUB", "AMD", "QCOM", "INTC",
    "TSM", "ASML", "JNJ", "PFE", "MRK", "ABBV", "LLY", "UNH", "WMT", "COST",
    "PG", "PEP", "PM", "MO", "CVX", "SLB", "HAL", "BP", "SHEL", "TTE",
    "JPM", "BAC", "WFC", "C", "GS", "MS", "V", "MA", "AXP", "BLK",
    "CAT", "DE", "BA", "LMT", "GE", "HON", "MMM", "UPS", "FDX", "DIS",
    "NFLX", "CRM", "ADBE", "ORCL", "CSCO", "PYPL", "SQ", "BABA", "JD", "BIDU",
    # ETFs Líderes
    "SPY", "QQQ", "DIA", "IWM", "EEM", "XLE", "XLK", "XLF", "XLV", "XLP"
]

RATIOS_CEDEAR = {
    "VIST": 1, "YPF": 1, "GGAL": 1, "PAMP": 1, "TXAR": 1, "ALUA": 1, "BMA": 1, "CEPU": 1, "CRES": 1, "EDN": 1,
    "BYMA": 1, "VALO": 1, "COME": 1, "BBAR": 1, "TECO2": 1, "LOMA": 1, "TGSU2": 1, "TGNO4": 1, "TRAN": 1, "MIRG": 1,
    "SUPV": 1, "IRSA": 1, "CVH": 1, "METR": 1, "AUSO": 1, "HARG": 1, "MOLI": 1, "LEDE": 1, "SEMI": 1, "INVJ": 1, "BOLT": 1,
    "AAPL": 10, "NVDA": 24, "MSFT": 30, "AMZN": 14, "GOOGL": 11, "META": 24, "TSLA": 15, "KO": 5, "XOM": 5,
    "PBR": 1, "MELI": 60, "GLOB": 18, "DESP": 1, "NU": 3, "BBD": 1, "ITUB": 1, "AMD": 10, "QCOM": 11, "INTC": 5,
    "TSM": 9, "ASML": 30, "JNJ": 15, "PFE": 4, "MRK": 10, "ABBV": 10, "LLY": 32, "UNH": 33, "WMT": 6, "COST": 48,
    "PG": 15, "PEP": 15, "PM": 12, "MO": 4, "CVX": 8, "SLB": 3, "HAL": 2, "BP": 5, "SHEL": 4, "TTE": 4,
    "JPM": 15, "BAC": 4, "WFC": 5, "C": 3, "GS": 20, "MS": 10, "V": 18, "MA": 33, "AXP": 15, "BLK": 40,
    "CAT": 20, "DE": 20, "BA": 6, "LMT": 20, "GE": 10, "HON": 10, "MMM": 10, "UPS": 10, "FDX": 10, "DIS": 12,
    "NFLX": 48, "CRM": 16, "ADBE": 22, "ORCL": 10, "CSCO": 5, "PYPL": 8, "SQ": 6, "BABA": 9, "JD": 4, "BIDU": 11,
    "SPY": 20, "QQQ": 20, "DIA": 20, "IWM": 10, "EEM": 5, "XLE": 5, "XLK": 10, "XLF": 5, "XLV": 5, "XLP": 5
}

DATOS_FUNDAMENTALES_BASE = {
    "VIST": {"Nombre": "Vista Energy S.A.B.", "PE": 8.45, "EV": 5.12, "DEUDA": 0.85, "LIQUIDEZ": 1.25, "MARGEN": 0.32, "ROE": 0.285, "Rev": 1.45, "Gross": 0.98, "EpsT": 5.40, "EpsF": 6.85},
    "YPF": {"Nombre": "YPF Sociedad Anónima", "PE": 6.20, "EV": 4.10, "DEUDA": 1.65, "LIQUIDEZ": 1.10, "MARGEN": 0.11, "ROE": 0.162, "Rev": 18.2, "Gross": 5.40, "EpsT": 4.15, "EpsF": 5.20},
    "XOM": {"Nombre": "Exxon Mobil Corp", "PE": 14.1, "EV": 7.30, "DEUDA": 0.45, "LIQUIDEZ": 1.40, "MARGEN": 0.125, "ROE": 0.180, "Rev": 345.0, "Gross": 112.0, "EpsT": 8.10, "EpsF": 8.65},
    "AAPL": {"Nombre": "Apple Inc.", "PE": 31.5, "EV": 24.2, "DEUDA": 0.95, "LIQUIDEZ": 1.05, "MARGEN": 0.263, "ROE": 1.54, "Rev": 385.0, "Gross": 170.0, "EpsT": 6.60, "EpsF": 7.45},
    "NVDA": {"Nombre": "NVIDIA Corporation", "PE": 42.0, "EV": 36.5, "DEUDA": 0.10, "LIQUIDEZ": 3.80, "MARGEN": 0.550, "ROE": 1.15, "Rev": 96.0, "Gross": 72.0, "EpsT": 2.80, "EpsF": 4.10},
    "GGAL": {"Nombre": "Grupo Financiero Galicia", "PE": 7.80, "EV": 5.50, "DEUDA": 0.60, "LIQUIDEZ": 1.30, "MARGEN": 0.220, "ROE": 0.240, "Rev": 3.20, "Gross": 1.80, "EpsT": 3.20, "EpsF": 3.90},
    "KO": {"Nombre": "Coca-Cola Co.", "PE": 24.5, "EV": 18.2, "DEUDA": 2.10, "LIQUIDEZ": 1.15, "MARGEN": 0.235, "ROE": 0.420, "Rev": 46.0, "Gross": 27.5, "EpsT": 2.70, "EpsF": 2.95},
    "WMT": {"Nombre": "Walmart Inc.", "PE": 29.0, "EV": 14.0, "DEUDA": 1.10, "LIQUIDEZ": 0.85, "MARGEN": 0.024, "ROE": 0.210, "Rev": 665.0, "Gross": 160.0, "EpsT": 2.45, "EpsF": 2.75}
}

yf_session = requests.Session()
yf_session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

def safe_float(val):
    try: return float(val)
    except: return 0.0

@st.cache_data(ttl=600)
def obtener_dolar_mep():
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

DOLAR_MEP = obtener_dolar_mep()

@st.cache_data(ttl=900)
def descargar_mercado_pool(tickers):
    try:
        data = yf.download(tickers, period="2y", progress=False, session=yf_session)
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
                r1y = ((p / float(s.iloc[-252])) - 1) * 100 if len(s) >= 252 else ((p / float(s.iloc[0])) - 1) * 100
                s_ytd = s[s.index.date >= f_ytd]
                rytd = ((p / float(s_ytd.iloc[0])) - 1) * 100 if len(s_ytd) > 0 else r1d
                res[tk] = {"precio": p, "1D": r1d, "1M": r1m, "6M": r6m, "1Y": r1y, "YTD": rytd}
        return res, close
    except: return {}, pd.DataFrame()

DATOS_RADAR, DF_HIST_GLOBAL = descargar_mercado_pool(TOP_100_ARG)

def obtener_fundamental_robusto(symbol):
    base = DATOS_FUNDAMENTALES_BASE.get(symbol, {
        "Nombre": symbol, "PE": 14.5, "EV": 8.0, "DEUDA": 1.1, "LIQUIDEZ": 1.25,
        "MARGEN": 0.14, "ROE": 0.17, "Rev": 10.0, "Gross": 4.0, "EpsT": 2.5, "EpsF": 3.0
    })
    px = DATOS_RADAR.get(symbol, {}).get("precio", 50.0)
    try:
        t = yf.Ticker(symbol, session=yf_session)
        inf = t.info or {}
        pe = safe_float(inf.get("trailingPE", inf.get("forwardPE", 0.0)))
        eb = safe_float(inf.get("ebitda", 0.0))
        td = safe_float(inf.get("totalDebt", 0.0))
        caj = safe_float(inf.get("totalCash", 0.0))
        ev = safe_float(inf.get("enterpriseToEbitda", 0.0))
        deuda = (td - caj) / eb if eb > 0 else base["DEUDA"]
        liq = safe_float(inf.get("currentRatio", 0.0))
        margen = safe_float(inf.get("profitMargins", 0.0))
        roe = safe_float(inf.get("returnOnEquity", 0.0))
        rev = safe_float(inf.get("totalRevenue", 0.0)) / 1e9
        gross = safe_float(inf.get("grossProfits", 0.0)) / 1e9
        epst = safe_float(inf.get("trailingEps", 0.0))
        epsf = safe_float(inf.get("forwardEps", 0.0))
        return {
            "Ticker": symbol, "Nombre": inf.get("longName", base["Nombre"]), "Precio": px,
            "PE": pe if pe > 0 else base["PE"], "EV": ev if ev > 0 else base["EV"],
            "DEUDA": deuda if deuda > 0 else base["DEUDA"], "LIQUIDEZ": liq if liq > 0 else base["LIQUIDEZ"],
            "MARGEN": margen if margen > 0 else base["MARGEN"], "ROE": roe if roe > 0 else base["ROE"],
            "Rev": rev if rev > 0 else base["Rev"], "Gross": gross if gross > 0 else base["Gross"],
            "EpsT": epst if epst > 0 else base["EpsT"], "EpsF": epsf if epsf > 0 else base["EpsF"],
            "RAW": inf
        }
    except:
        return {
            "Ticker": symbol, "Nombre": base["Nombre"], "Precio": px,
            "PE": base["PE"], "EV": base["EV"], "DEUDA": base["DEUDA"],
            "LIQUIDEZ": base["LIQUIDEZ"], "MARGEN": base["MARGEN"], "ROE": base["ROE"],
            "Rev": base["Rev"], "Gross": base["Gross"], "EpsT": base["EpsT"], "EpsF": base["EpsF"], "RAW": {}
        }

# Estado de Cartera con Fechas Reales y Ventas
if "cartera_operaciones" not in st.session_state:
    st.session_state.cartera_operaciones = [
        {"Ticker": "VIST", "Nominales": 100, "PPC_ARS": 77200.0, "Fecha_Compra": datetime.date(2025, 6, 15), "Dividendos_USD": 15.0, "Yield_Est": 0.018},
        {"Ticker": "XOM", "Nominales": 50, "PPC_ARS": 31500.0, "Fecha_Compra": datetime.date(2025, 8, 10), "Dividendos_USD": 25.5, "Yield_Est": 0.034}
    ]

if "ventas_realizadas" not in st.session_state:
    st.session_state.ventas_realizadas = []

if "watchlist_tickers" not in st.session_state:
    st.session_state.watchlist_tickers = ["VIST", "YPF", "AAPL", "GGAL", "NVDA", "KO", "XOM", "WMT", "MELI", "SPY"]

if "activo_analizado" not in st.session_state: st.session_state.activo_analizado = "VIST"
if "peers_analizados" not in st.session_state: st.session_state.peers_analizados = "YPF, XOM"

menu = st.radio("Secciones:", ["🌐 DASHBOARD & WATCHLIST", "🔍 ANÁLISIS INTEGRAL", "💼 PORTAFOLIO Y MODELOS"], horizontal=True)
st.markdown("---")

# ==============================================================================
# 1. DASHBOARD & WATCHLIST (100 ACTIVOS + HEATMAP)
# ==============================================================================
if menu == "🌐 DASHBOARD & WATCHLIST":
    st.subheader("⚡ Monitor de Ruedas: Ganadores y Rezagados (1D)")
    
    if not DATOS_RADAR:
        st.warning("Sincronizando feed de mercado...")
    else:
        ordenados = sorted(DATOS_RADAR.items(), key=lambda x: x[1]["1D"], reverse=True)
        top_gainers = ordenados[:3]
        top_losers = ordenados[-3:]
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<p style='font-size:12px; font-weight:700; color:#34d399; margin-bottom:8px;'>🟢 TOP GANADORES DE LA RUEDA</p>", unsafe_allow_html=True)
            for tk, val in top_gainers:
                st.markdown(f"""
                <div class='radar-card-item'>
                    <div><b style='color:#f8fafc; font-size:14px;'>{tk}</b> <span style='font-size:11px; color:#64748b; margin-left:8px;'>USD ${val['precio']:.2f}</span></div>
                    <span style='color:#34d399; font-weight:700; font-family:JetBrains Mono; font-size:13px;'>{val['1D']:+.2f}%</span>
                </div>
                """, unsafe_allow_html=True)
                
        with c2:
            st.markdown("<p style='font-size:12px; font-weight:700; color:#fb7185; margin-bottom:8px;'>🔴 TOP REZAGADOS DE LA RUEDA</p>", unsafe_allow_html=True)
            for tk, val in top_losers:
                st.markdown(f"""
                <div class='radar-card-item'>
                    <div><b style='color:#f8fafc; font-size:14px;'>{tk}</b> <span style='font-size:11px; color:#64748b; margin-left:8px;'>USD ${val['precio']:.2f}</span></div>
                    <span style='color:#fb7185; font-weight:700; font-family:JetBrains Mono; font-size:13px;'>{val['1D']:+.2f}%</span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📌 Watchlist Core (Mapa de Calor de Retornos Periódicos)")

        seleccion_wl = st.multiselect(
            "Seleccionar activos a monitorear (Pool de 100 activos más operados en Argentina):",
            options=TOP_100_ARG,
            default=st.session_state.watchlist_tickers
        )
        if seleccion_wl != st.session_state.watchlist_tickers:
            st.session_state.watchlist_tickers = seleccion_wl
            st.rerun()

        def get_heat_style(val):
            if val > 0:
                alpha = min(0.35, max(0.08, (val / 40.0)))
                return f"style='background: rgba(16, 185, 129, {alpha:.2f}); color: #34d399; font-weight: 600; text-align: right;'"
            elif val < 0:
                alpha = min(0.35, max(0.08, (abs(val) / 40.0)))
                return f"style='background: rgba(244, 63, 94, {alpha:.2f}); color: #fb7185; font-weight: 600; text-align: right;'"
            return "style='text-align: right; color: #94a3b8;'"

        filas_wl_html = []
        for t in st.session_state.watchlist_tickers:
            d = DATOS_RADAR.get(t, {"precio": 0.0, "1D": 0.0, "1M": 0.0, "6M": 0.0, "1Y": 0.0, "YTD": 0.0})
            px_ars = (d["precio"] / RATIOS_CEDEAR.get(t, 1)) * DOLAR_MEP
            fila = f"""<tr>
                <td><b>{t}</b></td>
                <td style='font-family:JetBrains Mono;'>${d['precio']:.2f}</td>
                <td style='font-family:JetBrains Mono;'>${px_ars:,.2f}</td>
                <td {get_heat_style(d['1D'])}>{d['1D']:+.2f}%</td>
                <td {get_heat_style(d['1M'])}>{d['1M']:+.2f}%</td>
                <td {get_heat_style(d['6M'])}>{d['6M']:+.2f}%</td>
                <td {get_heat_style(d['1Y'])}>{d['1Y']:+.2f}%</td>
                <td {get_heat_style(d['YTD'])}>{d['YTD']:+.2f}%</td>
            </tr>"""
            filas_wl_html.append(fila)

        tabla_wl_html = f"""<div class='table-viewport'><table class='terminal-table'>
            <thead><tr>
                <th>Ticker</th><th>Precio USD</th><th>Cedear ARS</th>
                <th style='text-align:right;'>1D</th><th style='text-align:right;'>1M</th>
                <th style='text-align:right;'>6M</th><th style='text-align:right;'>1Y</th>
                <th style='text-align:right;'>YTD</th>
            </tr></thead>
            <tbody>{"".join(filas_wl_html)}</tbody>
        </table></div>"""
        st.markdown(tabla_wl_html, unsafe_allow_html=True)

# ==============================================================================
# 2. ANÁLISIS INTEGRAL (FLUJO INSTITUCIONAL)
# ==============================================================================
elif menu == "🔍 ANÁLISIS INTEGRAL":
    c_s1, c_s2 = st.columns([1, 2])
    t_obj = c_s1.selectbox("Activo a Analizar:", TOP_100_ARG, index=TOP_100_ARG.index(st.session_state.activo_analizado)).upper().strip()
    t_comp_raw = c_s2.text_input("Peers de Referencia (Separados por coma):", value=st.session_state.peers_analizados).upper()
    
    if st.button("Ejecutar Análisis Cuantitativo"):
        st.session_state.activo_analizado = t_obj
        st.session_state.peers_analizados = t_comp_raw
        st.rerun()

    t_obj = st.session_state.activo_analizado
    peers = [c.strip() for c in st.session_state.peers_analizados.split(",") if c.strip()]
    lista_tickers = [t_obj] + peers
    dataset = [obtener_fundamental_robusto(tk) for tk in lista_tickers]
    d_obj = dataset[0]
    
    serie_mc = DF_HIST_GLOBAL[t_obj].dropna() if t_obj in DF_HIST_GLOBAL.columns else pd.Series(dtype=float)

    # Parámetros DCF y Reverse DCF
    ingresos = d_obj["Rev"]
    wacc_base, g_terminal = 0.115, 0.02
    margen_base = d_obj["MARGEN"]
    precio_mkt = d_obj["Precio"]
    shares = 0.20 * 1e9

    sims = 3000
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

    # Reverse DCF: Crecimiento implícito
    def obj_reverse_dcf(g_imp):
        ing = ingresos
        flujos = []
        for y in range(1, 6):
            ing *= (1 + g_imp)
            flujos.append((ing * margen_base * 0.65) / ((1 + wacc_base)**y))
        vt = (ing * margen_base * 0.65 * (1 + g_terminal)) / (wacc_base - g_terminal)
        eq_val = (sum(flujos) + (vt / ((1 + wacc_base)**5))) * 1e9 / shares
        return abs(eq_val - precio_mkt)

    res_opt = sco.minimize(obj_reverse_dcf, [0.06], bounds=[(-0.20, 0.50)], method='Nelder-Mead')
    g_implicito = float(res_opt.x[0])

    tab_fund, tab_tech, tab_val, tab_mc = st.tabs([
        "📊 Balances & Ratios", 
        "📈 Análisis Técnico (DMI)", 
        "🎯 Valuación Intrínseca (DCF + Reverse)", 
        "🎲 Simulación Monte Carlo"
    ])

    # --- PESTAÑA 1: BALANCES Y RATIOS FUNDAMENTALES ---
    with tab_fund:
        st.markdown(f"### 🏢 Perfil y Calidad Operativa: {d_obj['Nombre']}")
        resumen_empresa = ia_perfil_analista_senior(t_obj, d_obj["Nombre"], {"deuda": d_obj["DEUDA"], "margen": d_obj["MARGEN"], "roe": d_obj["ROE"]})
        st.markdown(f"<div class='terminal-card blue-card'>{resumen_empresa.replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)

        c_w1, c_w2 = st.columns([1, 2])
        with c_w1:
            st.markdown("#### Consenso Analistas Sell-Side")
            recom = str(d_obj["RAW"].get("recommendationKey", "hold")).lower()
            val_gauge = 5 if "strong_buy" in recom or "strong buy" in recom else 4 if "buy" in recom else 2 if "sell" in recom else 3
            fig_g = go.Figure(go.Indicator(
                mode="gauge+number", value=val_gauge,
                title={'text': "Escala 1 (Venta) a 5 (Compra)", 'font': {'size': 11, 'color': '#94a3b8'}},
                gauge={'axis': {'range': [1, 5], 'tickvals': [1, 2, 3, 4, 5], 'ticktext': ['Venta F.', 'Venta', 'Mantener', 'Compra', 'Compra F.']},
                       'bar': {'color': "#d4a34b"},
                       'steps': [{'range': [1, 2.5], 'color': "rgba(244, 63, 94, 0.2)"}, {'range': [2.5, 3.5], 'color': "rgba(255, 255, 255, 0.05)"}, {'range': [3.5, 5], 'color': "rgba(16, 185, 129, 0.2)"}]}
            ))
            fig_g.update_layout(height=190, margin=dict(l=10, r=10, t=20, b=10), paper_bgcolor='#0d111a', font={'color': '#ffffff'})
            st.plotly_chart(fig_g, use_container_width=True)
            st.caption("ℹ️ *Fuente: Consenso estandarizado de bancos de inversión vía LSEG / Yahoo Finance.*")

        with c_w2:
            st.markdown("#### Calidad de Ganancias y Flujos (TTM vs Estimación)")
            eps_trail = d_obj["EpsT"]
            eps_fwd = d_obj["EpsF"]
            rev_tot = d_obj["Rev"]
            gross_prof = d_obj["Gross"]

            filas_bal = [
                f"<tr><td><b>EPS (Ganancia Neta por Acción)</b></td><td>${eps_trail:.2f}</td><td>${eps_fwd:.2f}</td><td style='color: {'#34d399' if eps_fwd >= eps_trail else '#f43f5e'}; font-weight:bold;'>{(((eps_fwd/eps_trail)-1)*100 if eps_trail > 0 else 0.0):+.2f}%</td></tr>",
                f"<tr><td><b>Ingresos Totales (Revenue)</b></td><td>${rev_tot:.2f} B</td><td>${gross_prof:.2f} B (Gross Profit)</td><td style='color: #34d399; font-weight:bold;'>{(gross_prof/rev_tot*100 if rev_tot>0 else 0):.1f}% Margen Bruto</td></tr>"
            ]
            tabla_bal_html = "<div class='table-viewport'><table class='terminal-table'><thead><tr><th>Métrica Contable</th><th>Últimos 12M</th><th>Consenso Siguiente Ejercicio</th><th>Variación</th></tr></thead><tbody>" + "".join(filas_bal) + "</tbody></table></div>"
            st.markdown(tabla_bal_html, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### Matriz Comparativa Relativa vs Peers")
        
        t_pe = "P/E: Cuántas veces beneficios netos descuenta el precio de cotización."
        t_ev = "EV/EBITDA: Valuación global de la firma sobre su flujo de caja operativo limpio."
        t_deuda = "Deuda Neta/EBITDA: Años necesarios para cancelar el pasivo exigible con el EBITDA actual."
        t_liq = "Liquidez Corriente: Capacidad de cubrir pasivos de corto plazo con activo corriente."
        t_mg = "Margen Neto: Porcentaje de utilidad líquida resultante por cada $100 vendidos."
        t_roe = "ROE: Tasa de retorno generada sobre el patrimonio neto contable de los accionistas."

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

        # Diagnóstico profundo de múltiplos
        diagnostico_multiplos = ia_analisis_multiplos_profundo(d_obj, dataset)
        st.markdown(f"<div class='terminal-card gold-card'><b>Diagnóstico de Múltiplos y Calidad de Retorno:</b><br>{diagnostico_multiplos}</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 🎯 Tesis Ejecutiva e Implicancias de Coyuntura")
        if st.button(f"Emitir Tesis de Inversión Macro ({t_obj})"):
            st.session_state[f"tesis_{t_obj}"] = ia_tesis_macro_coyuntura(
                t_obj, d_obj["Nombre"], d_obj["Precio"], d_obj["PE"],
                d_obj["ROE"], d_obj["DEUDA"], d_obj["MARGEN"], dcf_mediano
            )
        if f"tesis_{t_obj}" in st.session_state:
            st.markdown(f"<div class='terminal-card blue-card'>{st.session_state[f'tesis_{t_obj}']}</div>", unsafe_allow_html=True)

    # --- PESTAÑA 2: ANÁLISIS TÉCNICO DMI ---
    with tab_tech:
        st.markdown(f"### 📈 Fuerza Tendencial y Timing Operativo (DMI / ADX): {t_obj}")
        
        df_ind, df_raw = yf.download(t_obj, period="1y", progress=False, session=yf_session), pd.DataFrame()
        if not df_ind.empty and 'High' in df_ind.columns:
            df_t = df_ind.copy()
            if isinstance(df_t.columns, pd.MultiIndex): df_t.columns = df_t.columns.get_level_values(0)
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
            fig_d.add_trace(go.Scatter(x=df_t.index, y=df_t['+DI'], name="+DI (Compradores)", line=dict(color='#10b981', width=1.2)), row=2, col=1)
            fig_d.add_trace(go.Scatter(x=df_t.index, y=df_t['-DI'], name="-DI (Vendedores)", line=dict(color='#f43f5e', width=1.2)), row=2, col=1)
            fig_d.add_trace(go.Scatter(x=df_t.index, y=df_t['ADX'], name="ADX (Fuerza)", line=dict(color='#0284c7', width=1.5)), row=2, col=1)
            fig_d.update_layout(template="plotly_dark", paper_bgcolor='#0d111a', plot_bgcolor='#06080d', height=380, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_d, use_container_width=True)

            di_p, di_m, adx_val = df_t['+DI'].iloc[-1], df_t['-DI'].iloc[-1], df_t['ADX'].iloc[-1]
            soporte = df_t['Low'].tail(30).min()
            resistencia = df_t['High'].tail(30).max()
            
            l1 = f"• <b>Dinámica y Momentum:</b> {'Presión compradora dominante (+DI > -DI)' if di_p > di_m else 'Presión vendedora dominante (-DI > +DI)'}, con un ADX en {adx_val:.1f} pts que ratifica {'inercia tendencial institucional activa (>25)' if adx_val > 25 else 'movimiento lateral o indecisión operativa (<25)'}."
            l2 = f"• <b>Comportamiento vs Tendencia:</b> Cotiza {'por sobre su media de 30 ruedas, conservando estructura favorable' if df_t['Close'].iloc[-1] >= df_t['EMA30'].iloc[-1] else 'por debajo de la media de 30 ruedas, advirtiendo cautela en entradas largas'}."
            l3 = f"• <b>Zonas Relevantes:</b> Soporte táctico en <b>${soporte:.2f} USD</b> para control de drawdown y resistencia inmediata en <b>${resistencia:.2f} USD</b>."
            st.markdown(f"<div class='terminal-card'><b>Lectura Técnica Ejecutiva:</b><br>{l1}<br>{l2}<br>{l3}</div>", unsafe_allow_html=True)

    # --- PESTAÑA 3: VALUACIÓN INTRÍNSECA (DCF Y REVERSE DCF) ---
    with tab_val:
        st.markdown(f"### 🎯 Valuación por Flujos Descontados y Reverse DCF ({t_obj})")
        
        c_v1, c_v2 = st.columns(2)
        with c_v1:
            st.markdown("#### DCF Estocástico (Simulaciones Monte Carlo)")
            fig_dcf = px.histogram(vals_dcf, nbins=40, color_discrete_sequence=['#10b981'])
            fig_dcf.add_vline(x=precio_mkt, line_width=2, line_dash="dash", line_color="#f43f5e", annotation_text="Precio Mercado")
            fig_dcf.update_layout(template="plotly_dark", paper_bgcolor='#0d111a', plot_bgcolor='#06080d', height=260, showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_dcf, use_container_width=True)
            
            upside_dcf = ((dcf_mediano - precio_mkt) / dcf_mediano) * 100
            st.markdown(f"<div class='terminal-card green-card'><b>Valor Intrínseco Mediano:</b> ${dcf_mediano:.2f} USD<br>• Precio Mercado: ${precio_mkt:.2f} USD | Margen de Seguridad: <b>{upside_dcf:+.1f}%</b></div>", unsafe_allow_html=True)
            
        with c_v2:
            st.markdown("#### Reverse DCF (Expectativas Implícitas)")
            st.metric("Crecimiento de FCF Anual Exigido por el Mercado (5A)", f"{g_implicito*100:+.1f}%")
            st.markdown(f"""<div class='terminal-card gold-card'>
            <b>Interpretación de Expectativas:</b> El precio actual exige que {t_obj} expanda su flujo libre al <b>{g_implicito*100:+.1f}% anual</b> durante el próximo lustro. Si la tasa es inferior al ROE ({d_obj['ROE']*100:.1f}%), la exigencia del mercado es conservadora y ofrece una asimetría favorable.
            </div>""", unsafe_allow_html=True)

    # --- PESTAÑA 4: MONTE CARLO Y RIESGO DE COLA ---
    with tab_mc:
        st.markdown(f"### 🎲 Simulación Estocástica de Precios (Movimiento Browniano Geométrico)")
        st.markdown("""<div class='terminal-card'>
        <b>Marco Metodológico del Modelo GBM:</b> El Movimiento Browniano Geométrico asume que las cotizaciones siguen la ecuación diferencial estocástica $dS_t = \mu S_t dt + \sigma S_t dW_t$.
        <br>• <b>Deriva ($\mu$):</b> Tendencia central calculada como $\mu = \bar{r} - \\frac{1}{2}\sigma^2$, descontando el arrastre de volatilidad (volatility drag).
        <br>• <b>Volatilidad ($\sigma$):</b> Dispersión anualizada observada en las últimas 252 ruedas.
        <br>• <b>Lectura de Percentiles:</b> La banda P90/P10 representa los conos donde se ubica el 80% de los escenarios proyectados. El percentil 10 refleja el soporte de cola en escenarios de estrés.
        </div>""", unsafe_allow_html=True)

        if not serie_mc.empty:
            ret = serie_mc.pct_change().dropna()
            sigma, mu_d = ret.std(), ret.mean() - 0.5 * (ret.std() ** 2)
            px_0 = float(serie_mc.iloc[-1])
            
            c_mc1, c_mc2 = st.columns(2)
            with c_mc1:
                st.markdown("#### Cono de Dispersión: 30 Ruedas")
                m_30 = np.zeros((30, 800))
                m_30[0] = px_0
                z_30 = np.random.standard_normal((29, 800))
                for t in range(1, 30): m_30[t] = m_30[t-1] * np.exp(mu_d + sigma * z_30[t-1])
                
                p10_30 = np.percentile(m_30[-1, :], 10)
                p50_30 = np.percentile(m_30[-1, :], 50)
                p90_30 = np.percentile(m_30[-1, :], 90)
                
                f30 = go.Figure()
                for i in range(20): f30.add_trace(go.Scatter(y=m_30[:, i], mode='lines', line=dict(color='rgba(2, 132, 199, 0.08)'), showlegend=False))
                f30.add_trace(go.Scatter(y=np.median(m_30, axis=1), mode='lines', line=dict(color='#d4a34b', width=2), name="Mediana"))
                f30.update_layout(template="plotly_dark", paper_bgcolor='#0d111a', plot_bgcolor='#06080d', height=240, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(f30, use_container_width=True)
                st.caption(f"🎯 **Horizontes 30D:** P10 (Soporte estrés): ${p10_30:.2f} | Mediana: ${p50_30:.2f} | P90 (Techo probable): ${p90_30:.2f}")
                
            with c_mc2:
                st.markdown("#### Cono de Dispersión: 1 Año (252 Ruedas)")
                m_252 = np.zeros((252, 800))
                m_252[0] = px_0
                z_252 = np.random.standard_normal((251, 800))
                for t in range(1, 252): m_252[t] = m_252[t-1] * np.exp(mu_d + sigma * z_252[t-1])
                
                p10_1y = np.percentile(m_252[-1, :], 10)
                p50_1y = np.percentile(m_252[-1, :], 50)
                p90_1y = np.percentile(m_252[-1, :], 90)
                
                f252 = go.Figure()
                for i in range(20): f252.add_trace(go.Scatter(y=m_252[:, i], mode='lines', line=dict(color='rgba(212, 163, 75, 0.08)'), showlegend=False))
                f252.add_trace(go.Scatter(y=np.median(m_252, axis=1), mode='lines', line=dict(color='#10b981', width=2), name="Mediana"))
                f252.update_layout(template="plotly_dark", paper_bgcolor='#0d111a', plot_bgcolor='#06080d', height=240, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(f252, use_container_width=True)
                st.caption(f"🎯 **Horizontes 1Y:** P10 (Soporte estrés): ${p10_1y:.2f} | Mediana: ${p50_1y:.2f} | P90 (Techo probable): ${p90_1y:.2f}")

# ==============================================================================
# 3. PORTAFOLIO, REPORTE PDF, BENCHMARK Y ESTRATEGIAS
# ==============================================================================
elif menu == "💼 PORTAFOLIO Y MODELOS":
    st.subheader("💼 Portafolio Consolidado (Tracking, Benchmark Real y Auditoría)")

    # Formulario dinámico para registrar Compras o Ventas
    with st.expander("➕ Cargar Operación en Cartera (Compra / Venta con PPC)"):
        col_op1, col_op2, col_op3, col_op4, col_op5 = st.columns(5)
        tipo_op = col_op1.selectbox("Tipo de Operación:", ["Compra (Aporte)", "Venta (Liquidación)"])
        n_tk = col_op2.selectbox("Ticker:", TOP_100_ARG, index=0)
        n_cant = col_op3.number_input("Nominales:", min_value=1, value=50, step=10)
        n_precio = col_op4.number_input("Precio Cedear (ARS):", min_value=1.0, value=75000.0, step=500.0)
        n_fecha = col_op5.date_input("Fecha de Operación:", value=datetime.date.today())
        
        if st.button("Procesar Operación"):
            pos_existente = next((p for p in st.session_state.cartera_operaciones if p["Ticker"] == n_tk), None)
            
            if "Compra" in tipo_op:
                if pos_existente:
                    c_ant, p_ant = pos_existente["Nominales"], pos_existente["PPC_ARS"]
                    c_nueva = c_ant + n_cant
                    pos_existente["Nominales"] = c_nueva
                    pos_existente["PPC_ARS"] = ((c_ant * p_ant) + (n_cant * n_precio)) / c_nueva
                    st.success(f"Compra registrada. Nuevo PPC para {n_tk}: ${pos_existente['PPC_ARS']:,.2f} ARS ({c_nueva} nominales).")
                else:
                    st.session_state.cartera_operaciones.append({
                        "Ticker": n_tk, "Nominales": n_cant, "PPC_ARS": n_precio, 
                        "Fecha_Compra": n_fecha, "Dividendos_USD": 0.0, "Yield_Est": 0.02
                    })
                    st.success(f"Posición en {n_tk} dada de alta exitosamente.")
            else:
                if not pos_existente:
                    st.error(f"No podés vender {n_tk} porque no figura en tu cartera.")
                elif pos_existente["Nominales"] < n_cant:
                    st.error(f"Nominales insuficientes. Tenés {pos_existente['Nominales']} y querés vender {n_cant}.")
                else:
                    ganancia_ars = (n_precio - pos_existente["PPC_ARS"]) * n_cant
                    ganancia_usd = ganancia_ars / DOLAR_MEP
                    pos_existente["Nominales"] -= n_cant
                    
                    st.session_state.ventas_realizadas.append({
                        "Ticker": n_tk, "Nominales": n_cant, "Fecha": n_fecha,
                        "Precio_Venta_ARS": n_precio, "PnL_USD": ganancia_usd
                    })
                    
                    if pos_existente["Nominales"] == 0:
                        st.session_state.cartera_operaciones.remove(pos_existente)
                        st.warning(f"Posición en {n_tk} cerrada totalmente. P&L Realizado: ${ganancia_usd:,.2f} USD.")
                    else:
                        st.info(f"Venta parcial ejecutada. Quedan {pos_existente['Nominales']} títulos. P&L Realizado: ${ganancia_usd:,.2f} USD.")
            st.rerun()

    is_ars = st.radio("Moneda de visualización:", ["ARS", "USD"], horizontal=True) == "ARS"
    
    # Procesamiento de cartera viva
    c_tot_usd, v_tot_usd, div_tot_usd, div_anual_est_usd = 0.0, 0.0, 0.0, 0.0
    filas_html_cartera = []
    datos_pdf_filas = []

    for pos in st.session_state.cartera_operaciones:
        tk, nom, ppc_ars, f_ing = pos["Ticker"], pos["Nominales"], pos["PPC_ARS"], pos.get("Fecha_Compra", datetime.date(2025, 1, 1))
        divs = pos.get("Dividendos_USD", 0.0)
        yield_est = pos.get("Yield_Est", 0.02)
        ratio = RATIOS_CEDEAR.get(tk, 1)
        px_actual_usd = DATOS_RADAR.get(tk, {}).get("precio", (ppc_ars * ratio / DOLAR_MEP))
        
        costo_usd = ((nom * ppc_ars) / DOLAR_MEP) * ratio
        val_usd = nom * px_actual_usd
        pl_usd = (val_usd + divs) - costo_usd
        ret_pct = (pl_usd / costo_usd) * 100 if costo_usd > 0 else 0.0
        flujo_anual_pos = val_usd * yield_est
        
        c_tot_usd += costo_usd
        v_tot_usd += val_usd
        div_tot_usd += divs
        div_anual_est_usd += flujo_anual_pos
        
        ppc_view = ppc_ars if is_ars else (ppc_ars * ratio / DOLAR_MEP)
        px_view = (px_actual_usd * DOLAR_MEP / ratio) if is_ars else px_actual_usd
        costo_view = costo_usd * (DOLAR_MEP if is_ars else 1.0)
        val_view = val_usd * (DOLAR_MEP if is_ars else 1.0)
        pl_view = pl_usd * (DOLAR_MEP if is_ars else 1.0)
        
        if ret_pct >= 20.0:
            badge = "<span class='badge-state badge-hold'>🟡 MANTENER</span>"
            tip_txt = f"Ganancia superior al +20% ({ret_pct:+.1f}%). Sostener posición con trailing stop."
        elif ret_pct <= -12.0:
            badge = "<span class='badge-state badge-sell'>🔴 REVISAR / STOP</span>"
            tip_txt = f"Pérdida acumulada del {ret_pct:+.1f}%. Controlar niveles de riesgo frente al PPC."
        else:
            badge = "<span class='badge-state badge-buy'>🟢 ACUMULAR</span>"
            tip_txt = f"Desempeño equilibrado ({ret_pct:+.1f}%). Rango apto para añadir o promediar."
            
        badge_html = f"<div class='th-tooltip'>{badge}<span class='th-tooltiptext'>{tip_txt}</span></div>"
        
        fila = f"""<tr>
            <td><b>{tk}</b></td>
            <td style='font-size:11px; color:#94a3b8;'>{f_ing.strftime('%d/%m/%Y')}</td>
            <td style='font-family:JetBrains Mono;'>{nom}</td>
            <td style='font-family:JetBrains Mono;'>${ppc_view:,.2f}</td>
            <td style='font-family:JetBrains Mono;'>${px_view:,.2f}</td>
            <td style='font-family:JetBrains Mono;'>${costo_view:,.2f}</td>
            <td style='font-family:JetBrains Mono;'>${val_view:,.2f}</td>
            <td style='color: {'#34d399' if pl_usd >= 0 else '#f43f5e'}; font-weight:bold; font-family:JetBrains Mono;'>${pl_view:,.2f}</td>
            <td style='color: {'#34d399' if ret_pct >= 0 else '#f43f5e'}; font-weight:bold; font-family:JetBrains Mono;'>{ret_pct:+.2f}%</td>
            <td>{badge_html}</td>
        </tr>"""
        filas_html_cartera.append(fila)

        datos_pdf_filas.append([
            tk, f_ing.strftime('%d/%m/%Y'), str(nom), f"${costo_usd:,.2f}", 
            f"${val_usd:,.2f}", f"${pl_usd:,.2f}", f"{ret_pct:+.2f}\%", f"${flujo_anual_pos:,.2f}"
        ])

    tabla_cartera_completa = f"""<div class='table-viewport'><table class='terminal-table'>
        <thead><tr>
            <th>Ticker</th><th>Fecha Ingreso</th><th>Nominales</th><th>PPC</th><th>Precio Actual</th>
            <th>Invertido</th><th>Valuación</th><th>P&L Neto</th><th>Total Return</th><th>Semáforo Táctico</th>
        </tr></thead>
        <tbody>{"".join(filas_html_cartera)}</tbody>
    </table></div>"""
    st.markdown(tabla_cartera_completa, unsafe_allow_html=True)

    # Métricas Globales
    st.markdown("#### Métricas Patrimoniales Consolidadas")
    k1, k2, k3, k4, k5 = st.columns(5)
    ret_total_cartera = ((v_tot_usd + div_tot_usd - c_tot_usd) / c_tot_usd) * 100 if c_tot_usd > 0 else 0.0
    mon_lbl = "ARS" if is_ars else "USD"
    conv_f = DOLAR_MEP if is_ars else 1.0
    spy_ret = DATOS_RADAR.get("SPY", {}).get("YTD", 0.0)
    alpha_spy = ret_total_cartera - spy_ret

    k1.metric("Capital Invertido", f"${(c_tot_usd*conv_f):,.0f} {mon_lbl}")
    k2.metric("Valuación Actual", f"${(v_tot_usd*conv_f):,.0f} {mon_lbl}")
    k3.metric("Flujo Divs Anual Est.", f"${(div_anual_est_usd*conv_f):,.0f} {mon_lbl}")
    k4.metric("Total Return", f"{ret_total_cartera:+.2f}%")
    k5.metric("Alpha vs SPY", f"{alpha_spy:+.2f}%", delta_color="normal" if alpha_spy >= 0 else "inverse")

    # MÓDULO DE DESCARGA PDF AUDITABLE
    st.markdown("---")
    st.markdown("#### 📄 Informe de Gestión Institucional (Exportable)")
    
    def generar_pdf_cartera():
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        styles = getSampleStyleSheet()
        
        titulo_style = ParagraphStyle('Titulo', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#06080d'))
        body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=9, leading=13, textColor=colors.HexColor('#334155'))
        
        elementos = []
        elementos.append(Paragraph("<b>APEX TERMINAL - INFORME AUDITADO DE CARTERA</b>", titulo_style))
        elementos.append(Paragraph(f"Fecha de Emisión: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')} | Moneda Base: USD | Dólar MEP: ${DOLAR_MEP:,.2f} ARS", body_style))
        elementos.append(Spacer(1, 15))
        
        resumen_data = [
            ["Capital Invertido (USD)", f"${c_tot_usd:,.2f}"],
            ["Valuación de Mercado (USD)", f"${v_tot_usd:,.2f}"],
            ["Renta Anual Proyectada por Dividendos (USD)", f"${div_anual_est_usd:,.2f}"],
            ["Retorno Total de Cartera (%)", f"{ret_total_cartera:+.2f}%"],
            ["Alpha Generado vs S&P 500 YTD (%)", f"{alpha_spy:+.2f}%"]
        ]
        t_resumen = Table(resumen_data, colWidths=[240, 260])
        t_resumen.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#0f172a')),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        elementos.append(t_resumen)
        elementos.append(Spacer(1, 15))
        
        elementos.append(Paragraph("<b>Detalle de Tenencias Vivas y Flujos Proyectados</b>", styles['Heading3']))
        headers_tenencias = ["Ticker", "Fecha", "Cant", "Costo USD", "Valuación", "P&L USD", "Ret %", "Div Est/Año"]
        tabla_tenencias = [headers_tenencias] + datos_pdf_filas
        
        t_tenencias = Table(tabla_tenencias, colWidths=[45, 55, 35, 65, 65, 65, 50, 70])
        t_tenencias.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0d111a')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 7.5),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        elementos.append(t_tenencias)
        
        doc.build(elementos)
        buffer.seek(0)
        return buffer

    if HAS_REPORTLAB:
        pdf_bytes = generar_pdf_cartera()
        st.download_button(
            label="📥 Descargar Informe Completo en PDF",
            data=pdf_bytes,
            file_name=f"Reporte_Cartera_{datetime.date.today().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )
    else:
        st.caption("ℹ️ Instalar `reportlab` en requirements.txt para habilitar la generación del informe en PDF.")

    # BENCHMARK DINÁMICO DESDE LA PRIMERA COMPRA
    st.markdown("---")
    st.markdown("#### 📊 Curva de Rendimiento Relativo: Cartera vs. SPY vs. QQQ")
    
    if st.session_state.cartera_operaciones:
        primera_fecha = min([p.get("Fecha_Compra", datetime.date(2025, 1, 1)) for p in st.session_state.cartera_operaciones])
        st.caption(f"ℹ️ *Curva de retorno normalizada (Base 0%) calculada a partir de la primera compra registrada en cartera: {primera_fecha.strftime('%d/%m/%Y')}.*")
        
        try:
            tks_port = list(set([p["Ticker"] for p in st.session_state.cartera_operaciones] + ["SPY", "QQQ"]))
            data_bench = yf.download(tks_port, start=primera_fecha.strftime('%Y-%m-%d'), progress=False, session=yf_session)
            close_b = data_bench['Close'].ffill().bfill() if isinstance(data_bench.columns, pd.MultiIndex) else data_bench['Close'].to_frame() if 'Close' in data_bench.columns else data_bench.ffill().bfill()
                
            if not close_b.empty and 'SPY' in close_b.columns and 'QQQ' in close_b.columns:
                weights = {p["Ticker"]: (p["Nominales"] * DATOS_RADAR.get(p["Ticker"], {}).get("precio", 100)) for p in st.session_state.cartera_operaciones}
                w_sum = sum(weights.values())
                weights = {k: v / w_sum for k, v in weights.items()}
                
                df_curvas = pd.DataFrame(index=close_b.index)
                cartera_serie = sum((close_b[tk] / close_b[tk].iloc[0]) * weights[tk] for tk in weights if tk in close_b.columns)
                
                df_curvas["Mi Cartera"] = (cartera_serie - 1) * 100
                df_curvas["S&P 500 (SPY)"] = ((close_b["SPY"] / close_b["SPY"].iloc[0]) - 1) * 100
                df_curvas["Nasdaq 100 (QQQ)"] = ((close_b["QQQ"] / close_b["QQQ"].iloc[0]) - 1) * 100
                
                fig_bench = px.line(df_curvas, y=["Mi Cartera", "S&P 500 (SPY)", "Nasdaq 100 (QQQ)"],
                                    color_discrete_map={"Mi Cartera": "#10b981", "S&P 500 (SPY)": "#0284c7", "Nasdaq 100 (QQQ)": "#d4a34b"})
                fig_bench.update_layout(template="plotly_dark", paper_bgcolor='#0d111a', plot_bgcolor='#06080d', height=340, yaxis_title="Retorno Acumulado (%)", margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig_bench, use_container_width=True)
        except Exception as e:
            st.caption(f"Curva de benchmark en cálculo: {e}")

    # ESTRATEGIAS POR PERFIL DE INVERSOR
    st.markdown("---")
    st.subheader("🎯 Carteras Modelo y Asignación Estratégica por Perfil")

    estrategias_detalle = {
        "💰 Income & Dividendos (Flujo de Caja)": [
            ("KO", "**Coca-Cola:** Payout ratio predecible, flujo inelástico y récord ininterrumpido de dividendos crecientes."),
            ("XOM", "**ExxonMobil:** Breakeven operativo líder por barril, permitiendo recompras y dividendos líquidos."),
            ("JNJ", "**Johnson & Johnson:** Calificación crediticia AAA con demanda farmacéutica inmune al ciclo macro."),
            ("PBR", "**Petrobras:** Dividend yield de dos dígitos respaldado por extracción en aguas ultraprofundas (Pre-Sal).")
        ],
        "🏰 Quality & Wide Moat (Fosos Defensivos)": [
            ("ASML", "**ASML:** Monopolio absoluto en litografía ultravioleta extrema (EUV), fijación de precios cautiva."),
            ("V", "**Visa:** Red de pagos de altísimo retorno sobre capital con márgenes operativos sobre el 55%."),
            ("MSFT", "**Microsoft:** Infraestructura B2B y nube crítica que genera altos costos de cambio para corporaciones."),
            ("GOOGL", "**Alphabet:** Dominio absoluto en búsquedas globales y reservas de liquidez equivalentes al 10% de su cap.")
        ],
        "🚀 Crecimiento Secular (High Beta / Tech)": [
            ("NVDA", "**NVIDIA:** Liderazgo estructural en hardware acelerado para entrenamiento e inferencia de IA."),
            ("MELI", "**MercadoLibre:** Penetración sinérgica en e-commerce y fintech bancarizada en América Latina."),
            ("AMD", "**AMD:** Ganancia constante de cuota de mercado en procesadores de centros de datos y servidores.")
        ],
        "⚖️ Value & Ciclos Energéticos (Descuento Patrimonial)": [
            ("VIST", "**Vista Energy:** Operador de shale oil de menor lifting cost en Vaca Muerta con expansión sostenida de reservas."),
            ("YPF", "**YPF:** Salida de activos maduros para focalizar el 100% de la inversión en el desarrollo no convencional."),
            ("BMA", "**Banco Macro:** Múltiplos comprimidos respecto al valor libro en un contexto de normalización monetaria.")
        ]
    }

    t_est = st.tabs(list(estrategias_detalle.keys()))
    for idx, (cat, items) in enumerate(estrategias_detalle.items()):
        with t_est[idx]:
            for tk, desc in items:
                st.markdown(f"• {desc}")
