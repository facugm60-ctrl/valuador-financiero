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
# CONECTIVIDAD APIs (GEMINI & FINNHUB)
# ------------------------------------------------------------------------------
try:
    import google.generativeai as genai
    HAS_GEMINI_LIB = True
except ImportError:
    HAS_GEMINI_LIB = False

st.sidebar.markdown("### 🔑 Conexión APIs Externas")
secrets_gemini = st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, "secrets") else ""
gemini_input_key = st.sidebar.text_input("Gemini API Key (Para Análisis):", value=secrets_gemini, type="password")
GEMINI_KEY = gemini_input_key.strip() if gemini_input_key else None
if HAS_GEMINI_LIB and GEMINI_KEY:
    try: genai.configure(api_key=GEMINI_KEY)
    except: pass

secrets_finnhub = st.secrets.get("FINNHUB_API_KEY", "") if hasattr(st, "secrets") else ""
finnhub_input_key = st.sidebar.text_input("Finnhub API Key (Para EECC EPS):", value=secrets_finnhub, type="password")
FINNHUB_KEY = finnhub_input_key.strip() if finnhub_input_key else None

def ia_perfil_analista_senior(ticker, nombre, info_dict):
    deuda, margen, roe = info_dict.get('deuda', 0.0), info_dict.get('margen', 0.0), info_dict.get('roe', 0.0)
    if HAS_GEMINI_LIB and GEMINI_KEY:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = f"Actúa como Senior Equity Research Analyst. Elabora una radiografía de {nombre} ({ticker}) en exactamente 5 renglones corridos:\n- Renglones 1-2: Core business, economía unitaria y foso defensivo (Moat).\n- Renglones 3-4: Asignación de capital, CapEx y guidance directivo.\n- Renglón 5: Salud patrimonial (Deuda Neta/EBITDA: {deuda:.2f}x, Margen Neto: {margen*100:.1f}%, ROE: {roe*100:.1f}%).\nSin introducciones."
            res = model.generate_content(prompt)
            if res and res.text: return res.text.strip()
        except: pass
    return f"{nombre} ({ticker}) sostiene su modelo en activos estratégicos con ventajas de escala y capacidad de fijación de precios.\nLa asignación de capital prioriza proyectos de alta TIR disciplinando el CapEx hacia eficiencias operativas.\nSu balance exhibe una solvencia con ratio Deuda Neta/EBITDA de {deuda:.2f}x, margen neto del {margen*100:.1f}% y ROE del {roe*100:.1f}%."

def ia_analisis_multiplos_profundo(d_obj, dataset):
    if HAS_GEMINI_LIB and GEMINI_KEY:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = f"Actúa como Portfolio Manager. Analiza la valuación de {d_obj['Ticker']} frente a sus comparables ({', '.join([d['Ticker'] for d in dataset if d['Ticker'] != d_obj['Ticker']])}):\nMétricas de {d_obj['Ticker']}: P/E {d_obj['PE']:.2f}x, EV/EBITDA {d_obj['EV']:.2f}x, Deuda Neta/EBITDA {d_obj['DEUDA']:.2f}x, Margen Neto {d_obj['MARGEN']*100:.1f}%, ROE {d_obj['ROE']*100:.1f}%.\nRedacta en un único párrafo de 4 renglones:\n- Explica si el P/E refleja una oportunidad de descalce o un 'Value Trap'.\n- Evalúa si el ROE proviene de margen operativo o apalancamiento financiero excesivo (Lógica DuPont).\n- Concluye si la dispersión de múltiplos otorga un punto de entrada con margen de seguridad."
            res = model.generate_content(prompt)
            if res and res.text: return res.text.strip()
        except: pass
    return f"La valuación de {d_obj['Ticker']} a {d_obj['PE']:.2f}x utilidades frente al promedio del grupo refleja un descuento relativo justificado por su perfil de riesgo. Su ROE del {d_obj['ROE']*100:.1f}%, contrastado con una carga de deuda neta de {d_obj['DEUDA']:.2f}x EBITDA, confirma que la rentabilidad sobre capital deriva de productividad operativa y márgenes sostenibles ({d_obj['MARGEN']*100:.1f}%), minimizando el riesgo de value trap y ofreciendo un punto de entrada con margen de seguridad razonable."

def ia_tesis_macro_coyuntura(ticker, nombre, precio, pe, roe, deuda, margen, dcf_valor):
    upside = ((dcf_valor - precio) / precio) * 100 if precio > 0 else 0
    if HAS_GEMINI_LIB and GEMINI_KEY:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = f"Actúa como CIO. Redacta una tesis ejecutiva en UN SOLO PÁRRAFO FLUIDO (5 renglones) para {nombre} ({ticker}):\n- Precio actual: ${precio:.2f} USD vs Fair Value DCF: ${dcf_valor:.2f} USD (Upside: {upside:+.1f}%).\n- P/E {pe:.1f}x, ROE {roe*100:.1f}%, Margen {margen*100:.1f}%, Deuda Neta/EBITDA {deuda:.2f}x.\nIntegra la coyuntura macro (tasas de la Fed e inflación) y concluye si es momento de Acumular, Mantener o Liquidar."
            res = model.generate_content(prompt)
            if res and res.text: return res.text.strip()
        except: pass
    sentido = "Acumular con horizonte táctico" if upside > 15 else "Mantener en cartera core" if upside >= -10 else "Reducir exposición"
    return f"Frente al actual ciclo monetario restrictivo y la volatilidad en las primas de riesgo, {ticker} cotiza con un descalce del {upside:+.1f}% frente a su valor intrínseco estimado por flujos (${dcf_valor:.2f} USD). Su margen neto del {margen*100:.1f}% y el apalancamiento contenido en {deuda:.2f}x EBITDA le permiten navegar entornos de financiamiento exigente sin deteriorar su capacidad de reinversión. En consecuencia, el balance de riesgo/retorno recomienda {sentido}."

# ------------------------------------------------------------------------------
# CLASIFICACIÓN SECTORIAL Y MAPEO DE 100 ACTIVOS
# ------------------------------------------------------------------------------
SECTORES_MAP = {
    "Tecnología": ["AAPL", "MSFT", "NVDA", "AMD", "QCOM", "INTC", "TSM", "ASML", "CRM", "ADBE", "ORCL", "CSCO", "XLK"],
    "Energía & Oil": ["VIST", "YPF", "PAMP", "XOM", "CVX", "PBR", "SLB", "HAL", "BP", "SHEL", "TTE", "XLE"],
    "Financiero": ["GGAL", "BMA", "BBAR", "SUPV", "BYMA", "VALO", "JPM", "BAC", "WFC", "C", "GS", "MS", "V", "MA", "AXP", "BLK", "NU", "BBD", "ITUB", "XLF"],
    "Consumo Discrecional": ["AMZN", "TSLA", "MELI", "DESP", "BABA", "JD", "BIDU", "NKE", "HD", "MCD"],
    "Consumo Masivo": ["KO", "PEP", "WMT", "COST", "PG", "PM", "MO", "LEDE", "MOLI", "XLP"],
    "Salud & Farma": ["JNJ", "PFE", "MRK", "ABBV", "LLY", "UNH", "BMY", "AMGN", "XLV"],
    "Industrial & Materiales": ["TXAR", "ALUA", "LOMA", "CAT", "DE", "BA", "LMT", "GE", "HON", "MMM", "UPS", "FDX", "HARG", "SEMI"],
    "Utilities & Real Estate": ["CEPU", "EDN", "TGSU2", "TGNO4", "TRAN", "METR", "AUSO", "CRES", "IRSA"],
    "Comunicaciones": ["TECO2", "CVH", "GOOGL", "META", "NFLX", "DIS"],
    "Índices & ETFs": ["SPY", "QQQ", "DIA", "IWM", "EEM"]
}

TICKER_TO_SECTOR = {}
for sec, tickers in SECTORES_MAP.items():
    for tk in tickers: TICKER_TO_SECTOR[tk] = sec
TOP_100_ARG = list(TICKER_TO_SECTOR.keys())

MARKET_CAPS = {
    "MSFT": 3100, "AAPL": 3300, "NVDA": 2900, "GOOGL": 2100, "AMZN": 1950, "META": 1300, "TSLA": 750,
    "BRK-B": 900, "LLY": 850, "AVGO": 780, "JPM": 580, "V": 520, "XOM": 480, "UNH": 470, "WMT": 540,
    "MA": 420, "PG": 390, "JNJ": 380, "COST": 380, "HD": 360, "MRK": 320, "ABBV": 310, "CVX": 290,
    "KO": 280, "PEP": 230, "BAC": 310, "AMD": 240, "QCOM": 190, "INTC": 90, "ASML": 340, "TSM": 850,
    "MELI": 105, "PBR": 95, "VIST": 5.5, "YPF": 11.2, "GGAL": 6.8, "PAMP": 3.9, "BMA": 4.1, "TXAR": 2.8,
    "ALUA": 2.6, "CEPU": 2.2, "CRES": 1.4, "EDN": 1.1, "LOMA": 1.8, "SPY": 500, "QQQ": 300
}

RATIOS_CEDEAR = {
    "VIST": 1, "YPF": 1, "GGAL": 1, "PAMP": 1, "TXAR": 1, "ALUA": 1, "BMA": 1, "CEPU": 1, "CRES": 1, "EDN": 1,
    "BYMA": 1, "VALO": 1, "COME": 1, "BBAR": 1, "TECO2": 1, "LOMA": 1, "TGSU2": 1, "TGNO4": 1, "TRAN": 1, "MIRG": 1,
    "SUPV": 1, "IRSA": 1, "CVH": 1, "METR": 1, "AUSO": 1, "HARG": 1, "MOLI": 1, "LEDE": 1, "SEMI": 1,
    "AAPL": 10, "NVDA": 24, "MSFT": 30, "AMZN": 14, "GOOGL": 11, "META": 24, "TSLA": 15, "KO": 5, "XOM": 5,
    "PBR": 1, "MELI": 60, "GLOB": 18, "DESP": 1, "NU": 3, "BBD": 1, "ITUB": 1, "AMD": 10, "QCOM": 11, "INTC": 5,
    "TSM": 9, "ASML": 30, "JNJ": 15, "PFE": 4, "MRK": 10, "ABBV": 10, "LLY": 32, "UNH": 33, "WMT": 6, "COST": 48,
    "PG": 15, "PEP": 15, "PM": 12, "MO": 4, "CVX": 8, "SLB": 3, "HAL": 2, "BP": 5, "SHEL": 4, "TTE": 4,
    "JPM": 15, "BAC": 4, "WFC": 5, "C": 3, "GS": 20, "MS": 10, "V": 18, "MA": 33, "AXP": 15, "BLK": 40,
    "CAT": 20, "DE": 20, "BA": 6, "LMT": 20, "GE": 10, "HON": 10, "MMM": 10, "UPS": 10, "FDX": 10, "DIS": 12,
    "NFLX": 48, "CRM": 16, "ADBE": 22, "ORCL": 10, "CSCO": 5, "BABA": 9, "JD": 4, "BIDU": 11,
    "SPY": 20, "QQQ": 20, "DIA": 20, "IWM": 10, "EEM": 5, "XLE": 5, "XLK": 10, "XLF": 5, "XLV": 5, "XLP": 5
}

DATOS_FUNDAMENTALES_BASE = {
    "VIST": {"Nombre": "Vista Energy S.A.B.", "PE": 8.45, "EV": 5.12, "DEUDA": 0.85, "LIQUIDEZ": 1.25, "MARGEN": 0.32, "ROE": 0.285, "Rev": 1.45, "Gross": 0.98, "EpsT": 5.40, "EpsF": 6.85},
    "YPF": {"Nombre": "YPF Sociedad Anónima", "PE": 6.20, "EV": 4.10, "DEUDA": 1.65, "LIQUIDEZ": 1.10, "MARGEN": 0.11, "ROE": 0.162, "Rev": 18.2, "Gross": 5.40, "EpsT": 4.15, "EpsF": 5.20},
    "XOM": {"Nombre": "Exxon Mobil Corp", "PE": 14.1, "EV": 7.30, "DEUDA": 0.45, "LIQUIDEZ": 1.40, "MARGEN": 0.125, "ROE": 0.180, "Rev": 345.0, "Gross": 112.0, "EpsT": 8.10, "EpsF": 8.65},
    "AAPL": {"Nombre": "Apple Inc.", "PE": 31.5, "EV": 24.2, "DEUDA": 0.95, "LIQUIDEZ": 1.05, "MARGEN": 0.263, "ROE": 1.54, "Rev": 385.0, "Gross": 170.0, "EpsT": 6.60, "EpsF": 7.45},
    "NVDA": {"Nombre": "NVIDIA Corporation", "PE": 42.0, "EV": 36.5, "DEUDA": 0.10, "LIQUIDEZ": 3.80, "MARGEN": 0.550, "ROE": 1.15, "Rev": 96.0, "Gross": 72.0, "EpsT": 2.80, "EpsF": 4.10},
    "AMD": {"Nombre": "Advanced Micro Devices", "PE": 38.2, "EV": 32.1, "DEUDA": 0.15, "LIQUIDEZ": 2.40, "MARGEN": 0.165, "ROE": 0.082, "Rev": 24.5, "Gross": 12.2, "EpsT": 1.95, "EpsF": 3.45},
    "GGAL": {"Nombre": "Grupo Financiero Galicia", "PE": 7.80, "EV": 5.50, "DEUDA": 0.60, "LIQUIDEZ": 1.30, "MARGEN": 0.220, "ROE": 0.240, "Rev": 3.20, "Gross": 1.80, "EpsT": 3.20, "EpsF": 3.90},
    "KO": {"Nombre": "Coca-Cola Co.", "PE": 24.5, "EV": 18.2, "DEUDA": 2.10, "LIQUIDEZ": 1.15, "MARGEN": 0.235, "ROE": 0.420, "Rev": 46.0, "Gross": 27.5, "EpsT": 2.70, "EpsF": 2.95},
    "WMT": {"Nombre": "Walmart Inc.", "PE": 29.0, "EV": 14.0, "DEUDA": 1.10, "LIQUIDEZ": 0.85, "MARGEN": 0.024, "ROE": 0.210, "Rev": 665.0, "Gross": 160.0, "EpsT": 2.45, "EpsF": 2.75}
}

yf_session = requests.Session()
yf_session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

def safe_float(val):
    try: return float(val)
    except: return 0.0

@st.cache_data(ttl=300)
def obtener_cotizaciones_arg():
    try:
        r = requests.get("https://api.argentinadatos.com/v1/cotizaciones/dolares", timeout=5)
        if r.status_code == 200:
            df = pd.DataFrame(r.json())
            latest = df.sort_values('fecha').groupby('casa').last()
            return {
                "MEP": latest.loc['mep', 'venta'] if 'mep' in latest.index else 1420.0,
                "CCL": latest.loc['contadoconliqui', 'venta'] if 'contadoconliqui' in latest.index else 1450.0,
                "Oficial": latest.loc['oficial', 'venta'] if 'oficial' in latest.index else 1000.0,
            }
    except: pass
    return {"MEP": 1420.0, "CCL": 1450.0, "Oficial": 1000.0}

COTIZACIONES_ARG = obtener_cotizaciones_arg()
DOLAR_MEP = COTIZACIONES_ARG["MEP"]
DOLAR_CCL = COTIZACIONES_ARG["CCL"]

def obtener_eps_finnhub(ticker):
    if FINNHUB_KEY:
        try:
            r = requests.get(f"https://finnhub.io/api/v1/stock/earnings?symbol={ticker}&token={FINNHUB_KEY}")
            if r.status_code == 200: return r.json()
        except: pass
    return None

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
    px_val = DATOS_RADAR.get(symbol, {}).get("precio", 50.0)
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
            "Ticker": symbol, "Nombre": inf.get("longName", base["Nombre"]), "Precio": px_val,
            "PE": pe if pe > 0 else base["PE"], "EV": ev if ev > 0 else base["EV"],
            "DEUDA": deuda if deuda > 0 else base["DEUDA"], "LIQUIDEZ": liq if liq > 0 else base["LIQUIDEZ"],
            "MARGEN": margen if margen > 0 else base["MARGEN"], "ROE": roe if roe > 0 else base["ROE"],
            "Rev": rev if rev > 0 else base["Rev"], "Gross": gross if gross > 0 else base["Gross"],
            "EpsT": epst if epst > 0 else base["EpsT"], "EpsF": epsf if epsf > 0 else base["EpsF"],
            "RAW": inf
        }
    except:
        return {
            "Ticker": symbol, "Nombre": base["Nombre"], "Precio": px_val,
            "PE": base["PE"], "EV": base["EV"], "DEUDA": base["DEUDA"],
            "LIQUIDEZ": base["LIQUIDEZ"], "MARGEN": base["MARGEN"], "ROE": base["ROE"],
            "Rev": base["Rev"], "Gross": base["Gross"], "EpsT": base["EpsT"], "EpsF": base["EpsF"], "RAW": {}
        }

# Estado de Cartera
if "cartera_operaciones" not in st.session_state:
    st.session_state.cartera_operaciones = [
        {"Ticker": "VIST", "Nominales": 100, "PPC_ARS": 77200.0, "Fecha_Compra": datetime.date(2025, 6, 15), "Dividendos_USD": 15.0, "Yield_Est": 0.018},
        {"Ticker": "XOM", "Nominales": 50, "PPC_ARS": 31500.0, "Fecha_Compra": datetime.date(2025, 8, 10), "Dividendos_USD": 25.5, "Yield_Est": 0.034}
    ]

if "ventas_realizadas" not in st.session_state: st.session_state.ventas_realizadas = []
if "watchlist_tickers" not in st.session_state:
    st.session_state.watchlist_tickers = ["VIST", "YPF", "AAPL", "GGAL", "NVDA", "AMD", "KO", "XOM", "WMT", "SPY"]

if "activo_analizado" not in st.session_state: st.session_state.activo_analizado = "AMD"
if "peers_analizados" not in st.session_state: st.session_state.peers_analizados = ["NVDA", "INTC", "TSM"]

menu = st.radio("Secciones operativas:", [
    "🌐 DASHBOARD & MAPA DE RENDIMIENTOS", 
    "🔍 ANÁLISIS & COMPARADOR", 
    "💼 PORTAFOLIO Y MODELOS"
], horizontal=True)
st.markdown("---")

# ==============================================================================
# 1. DASHBOARD & MAPA DE RENDIMIENTOS
# ==============================================================================
if menu == "🌐 DASHBOARD & MAPA DE RENDIMIENTOS":
    st.subheader("⚡ Mapa de Rendimientos Sectorial")
    
    col_p1, col_p2 = st.columns([1, 3])
    periodo_map = col_p1.selectbox("Período de Rendimiento:", ["1D (Rueda)", "1M (Mensual)", "6M (Semestral)", "1Y (Anual)", "YTD (Año en curso)"])
    p_key = "1D" if "1D" in periodo_map else "1M" if "1M" in periodo_map else "6M" if "6M" in periodo_map else "1Y" if "1Y" in periodo_map else "YTD"
    
    data_treemap = []
    for tk in TOP_100_ARG:
        if tk in DATOS_RADAR:
            sec = TICKER_TO_SECTOR.get(tk, "Otros")
            ret_val = DATOS_RADAR[tk][p_key]
            cap_val = MARKET_CAPS.get(tk, 25.0)
            data_treemap.append({
                "Ticker": tk, "Sector": sec, "Rendimiento": ret_val, "MarketCap": cap_val, "Texto": f"{tk}<br>{ret_val:+.2f}%"
            })
            
    df_tree = pd.DataFrame(data_treemap)
    if not df_tree.empty:
        fig_tree = px.treemap(
            df_tree, path=['Sector', 'Ticker'], values='MarketCap', color='Rendimiento',
            color_continuous_scale=[[0.0, '#ef4444'], [0.45, '#7f1d1d'], [0.5, '#1e293b'], [0.55, '#064e3b'], [1.0, '#10b981']],
            color_continuous_midpoint=0, hover_data={'Rendimiento': ':.2f%'}, custom_data=['Texto']
        )
        fig_tree.data[0].texttemplate = "%{customdata[0]}"
        fig_tree.update_layout(template="plotly_dark", paper_bgcolor='#06080d', height=540, margin=dict(l=5, r=5, t=10, b=10))
        st.plotly_chart(fig_tree, use_container_width=True)
    
    st.markdown("---")
    st.subheader("📌 Monitoreo y Mapa de Calor (Arbitraje CEDEARs vs Dólar CCL)")
    
    seleccion_wl = st.multiselect("Personalizar Watchlist:", options=TOP_100_ARG, default=st.session_state.watchlist_tickers)
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
        ratio = RATIOS_CEDEAR.get(t, 1)
        px_ars = (d["precio"] / ratio) * DOLAR_MEP
        
        ccl_implicito = (px_ars * ratio) / d["precio"] if d["precio"] > 0 else 0.0
        arbitraje = (ccl_implicito / DOLAR_CCL - 1) * 100 if DOLAR_CCL > 0 else 0.0
        
        fila = f"""<tr>
            <td><b>{t}</b></td>
            <td style='font-family:JetBrains Mono;'>${d['precio']:.2f}</td>
            <td style='font-family:JetBrains Mono;'>${px_ars:,.2f}</td>
            <td style='font-family:JetBrains Mono;'>${ccl_implicito:,.2f}</td>
            <td style='color:{"#34d399" if arbitraje <= 0 else "#f43f5e"}; font-family:JetBrains Mono;'>{arbitraje:+.2f}%</td>
            <td {get_heat_style(d['1D'])}>{d['1D']:+.2f}%</td>
            <td {get_heat_style(d['1M'])}>{d['1M']:+.2f}%</td>
            <td {get_heat_style(d['YTD'])}>{d['YTD']:+.2f}%</td>
        </tr>"""
        filas_wl_html.append(fila)

    st.markdown(f"<div class='table-viewport'><table class='terminal-table'><thead><tr><th>Ticker</th><th>Precio USD</th><th>Cedear ARS</th><th>CCL Impl.</th><th>Arbitraje CCL</th><th style='text-align:right;'>1D</th><th style='text-align:right;'>1M</th><th style='text-align:right;'>YTD</th></tr></thead><tbody>{''.join(filas_wl_html)}</tbody></table></div>", unsafe_allow_html=True)
    st.caption(f"ℹ️ *Arbitraje CCL: Si está en verde (negativo), el CEDEAR se está comprando con descuento frente al Dólar CCL mercado (${DOLAR_CCL:,.2f} ARS).*")

# ==============================================================================
# 2. ANÁLISIS & COMPARADOR RELATIVO
# ==============================================================================
elif menu == "🔍 ANÁLISIS & COMPARADOR":
    col_sel1, col_sel2 = st.columns([1, 2])
    t_obj = col_sel1.selectbox("Activo Principal:", TOP_100_ARG, index=TOP_100_ARG.index(st.session_state.activo_analizado)).upper().strip()
    
    sector_activo = TICKER_TO_SECTOR.get(t_obj, "Tecnología")
    pares_mismo_sector = [tk for tk in SECTORES_MAP.get(sector_activo, []) if tk != t_obj]
    
    if t_obj != st.session_state.activo_analizado:
        st.session_state.activo_analizado = t_obj
        st.session_state.peers_analizados = pares_mismo_sector[:3]
        st.rerun()

    peers_seleccionados = col_sel2.multiselect(
        f"Comparar con competidores de {sector_activo}:",
        options=[tk for tk in TOP_100_ARG if tk != t_obj],
        default=[p for p in st.session_state.peers_analizados if p in TOP_100_ARG]
    )
    st.session_state.peers_analizados = peers_seleccionados

    tab_gfinance, tab_fund, tab_tech, tab_dcf, tab_mc = st.tabs([
        "📈 Comparador Relativo", 
        "📊 Fundamental & Ratios", 
        "📈 Técnico (DMI)", 
        "🧬 DCF & Reverse DCF",
        "🎲 Montecarlo Precio"
    ])

    # --- PESTAÑA COMPARADOR RELATIVO ---
    with tab_gfinance:
        st.markdown(f"### 📊 Gráfico de Rendimiento Comparativo Relativo (Base 0%)")
        tf_col, _ = st.columns([2, 3])
        tf_sel = tf_col.radio("Ventana Temporal:", ["1D", "1M", "3M", "6M", "YTD", "1Y"], horizontal=True)
        
        tickers_comparativa = [t_obj] + peers_seleccionados
        df_sub = pd.DataFrame()
        
        if tf_sel == "1D":
            data_1d = yf.download(tickers_comparativa, period="1d", interval="5m", progress=False, session=yf_session)
            if isinstance(data_1d.columns, pd.MultiIndex):
                df_sub = data_1d['Close'].ffill().bfill()
            else:
                df_sub = data_1d['Close'].to_frame() if 'Close' in data_1d.columns else data_1d.ffill().bfill()
        else:
            df_comp = DF_HIST_GLOBAL[tickers_comparativa].dropna() if all(tk in DF_HIST_GLOBAL.columns for tk in tickers_comparativa) else pd.DataFrame()
            if not df_comp.empty:
                dias_hist = 30 if tf_sel == "1M" else 90 if tf_sel == "3M" else 180 if tf_sel == "6M" else 252 if tf_sel == "1Y" else None
                if tf_sel == "YTD":
                    f_ytd = datetime.date(datetime.date.today().year, 1, 1)
                    df_sub = df_comp[df_comp.index.date >= f_ytd]
                else:
                    df_sub = df_comp.tail(dias_hist)
        
        if not df_sub.empty:
            df_norm = (df_sub / df_sub.iloc[0] - 1.0) * 100.0
            paleta = ["#38bdf8", "#f59e0b", "#10b981", "#ef4444", "#a855f7", "#ec4899"]
            fig_g = px.line(df_norm, labels={"value": "Variación (%)", "index": "Fecha"}, color_discrete_sequence=paleta)
            fig_g.update_traces(mode='lines')
            
            # Formato limpio Crosshair (Estilo Google Finance)
            fig_g.update_layout(
                template="plotly_dark", paper_bgcolor='#0d111a', plot_bgcolor='#06080d', height=380,
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                hovermode='x'
            )
            fig_g.update_xaxes(showspikes=True, spikethickness=1, spikedash="dot", spikecolor="#94a3b8", spikemode="across")
            st.plotly_chart(fig_g, use_container_width=True)
            
            filas_gf = []
            for tk in tickers_comparativa:
                p_act = float(df_sub[tk].iloc[-1])
                p_prev = float(df_sub[tk].iloc[0]) if len(df_sub) >= 2 else p_act
                chg_usd = p_act - p_prev
                pct_chg = (chg_usd / p_prev) * 100 if p_prev > 0 else 0.0
                nom_emp = DATOS_FUNDAMENTALES_BASE.get(tk, {}).get("Nombre", tk)
                
                filas_gf.append(f"""<tr>
                    <td><b>{tk}</b><br><span style='font-size:10px; color:#64748b;'>{nom_emp}</span></td>
                    <td style='font-family:JetBrains Mono;'>${p_act:,.2f}</td>
                    <td style='color: {"#34d399" if chg_usd >= 0 else "#f43f5e"}; font-family:JetBrains Mono;'>${chg_usd:+,.2f}</td>
                    <td style='color: {"#34d399" if pct_chg >= 0 else "#f43f5e"}; font-weight:700; font-family:JetBrains Mono;'>{pct_chg:+.2f}%</td>
                    <td style='font-family:JetBrains Mono; color:#94a3b8;'>${p_prev:,.2f}</td>
                </tr>""")
                
            st.markdown(f"<div class='table-viewport'><table class='terminal-table'><thead><tr><th>Símbolo / Compañía</th><th>Precio USD</th><th>Variación ($) [{tf_sel}]</th><th>Variación (%) [{tf_sel}]</th><th>Apertura Período</th></tr></thead><tbody>{''.join(filas_gf)}</tbody></table></div>", unsafe_allow_html=True)

    # --- PESTAÑA BALANCES & RATIOS ---
    with tab_fund:
        d_obj = obtener_fundamental_robusto(t_obj)
        dataset_peers = [d_obj] + [obtener_fundamental_robusto(p) for p in peers_seleccionados]
        
        st.markdown(f"### 🏢 Perfil y Calidad Operativa: {d_obj['Nombre']}")
        resumen_empresa = ia_perfil_analista_senior(t_obj, d_obj["Nombre"], {"deuda": d_obj["DEUDA"], "margen": d_obj["MARGEN"], "roe": d_obj["ROE"]})
        st.markdown(f"<div class='terminal-card blue-card'>{resumen_empresa.replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)

        c_w1, c_w2 = st.columns([1, 2])
        with c_w1:
            st.markdown("#### Consenso Analistas Sell-Side")
            
            # Cálculo determinista del consenso (No aleatorio)
            rec_mean = d_obj["RAW"].get("recommendationMean")
            if rec_mean is not None:
                val_gauge = 6.0 - safe_float(rec_mean)
                fuente_txt = f"Promedio matemático de analistas (Fuente: Yahoo Finance). Score original: {rec_mean}"
            else:
                val_gauge = 3.0
                fuente_txt = "Consenso neutral por defecto (Datos no disponibles en API)."

            fig_g = go.Figure(go.Indicator(
                mode="gauge+number",
                value=val_gauge,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Escala 1 (Venta) a 5 (Compra)", 'font': {'size': 11, 'color': '#94a3b8'}},
                gauge={
                    'axis': {'range': [1, 5], 'tickvals': [1, 2, 3, 4, 5], 'ticktext': ['Venta F.', 'Venta', 'Mantener', 'Compra', 'Compra F.']},
                    'bar': {'color': "#d4a34b"},
                    'steps': [
                        {'range': [1, 2.5], 'color': "rgba(244, 63, 94, 0.2)"},
                        {'range': [2.5, 3.5], 'color': "rgba(255, 255, 255, 0.05)"},
                        {'range': [3.5, 5], 'color': "rgba(16, 185, 129, 0.2)"}
                    ]
                }
            ))
            fig_g.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=10), paper_bgcolor='#0d111a', font={'color': '#ffffff'})
            st.plotly_chart(fig_g, use_container_width=True)
            st.caption(f"ℹ️ *{fuente_txt}*")

        with c_w2:
            st.markdown("#### Calidad de Ganancias y Flujos (TTM vs Estimación)")
            eps_trail, eps_fwd = d_obj["EpsT"], d_obj["EpsF"]
            rev_tot, gross_prof = d_obj["Rev"], d_obj["Gross"]

            filas_bal = [
                f"<tr><td><b>EPS (Ganancia Neta por Acción)</b></td><td>${eps_trail:.2f}</td><td>${eps_fwd:.2f}</td><td style='color: {'#34d399' if eps_fwd >= eps_trail else '#f43f5e'}; font-weight:bold;'>{(((eps_fwd/eps_trail)-1)*100 if eps_trail > 0 else 0.0):+.2f}%</td></tr>",
                f"<tr><td><b>Ingresos Totales (Revenue)</b></td><td>${rev_tot:.2f} B</td><td>${gross_prof:.2f} B (Gross Profit)</td><td style='color: #34d399; font-weight:bold;'>{(gross_prof/rev_tot*100 if rev_tot>0 else 0):.1f}% Margen Bruto</td></tr>"
            ]
            st.markdown(f"<div class='table-viewport'><table class='terminal-table'><thead><tr><th>Métrica Contable</th><th>Últimos 12M</th><th>Consenso Siguiente Ejercicio</th><th>Variación</th></tr></thead><tbody>{''.join(filas_bal)}</tbody></table></div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(f"#### 📅 Reporte de Resultados y Expectativas de Beneficios (EPS) - {t_obj}")
        
        finnhub_data = obtener_eps_finnhub(t_obj)
        if finnhub_data:
            eps_data = sorted(finnhub_data, key=lambda x: x['period'])
            trimestres_ej = [e['period'] for e in eps_data]
            eps_estimados = [e['estimate'] for e in eps_data]
            eps_reales = [e['actual'] for e in eps_data]
            fuente_eps = "Datos oficiales extraídos de Finnhub API en tiempo real."
        else:
            trimestres_ej = ["Q3 '25", "Q4 '25", "Q1 '26", "Q2 '26", "Q3 '26"]
            eps_estimados = [eps_trail*0.22, eps_trail*0.24, eps_trail*0.25, eps_trail*0.26, eps_trail*0.28]
            eps_reales = [eps_trail*0.23, eps_trail*0.25, eps_trail*0.29, eps_trail*0.25, None]
            fuente_eps = "Simulación estadística de EPS. Ingrese una Key de Finnhub para conectar los reportes auditados ante la SEC."
            
        fig_eecc = go.Figure()
        fig_eecc.add_trace(go.Scatter(
            x=trimestres_ej, y=eps_estimados, mode='markers', name='Estimación (Consenso)',
            marker=dict(size=14, color='rgba(255,255,255,0.2)', line=dict(width=2, color='#ffffff'))
        ))
        
        # Filtro seguro para evitar errores en list comprehension
        eps_reales_valid = [r for r in eps_reales if r is not None]
        eps_est_valid = eps_estimados[:len(eps_reales_valid)]
        colores_reales = ['#10b981' if r >= e else '#f43f5e' for r, e in zip(eps_reales_valid, eps_est_valid)]
        
        fig_eecc.add_trace(go.Scatter(
            x=trimestres_ej[:len(eps_reales_valid)], y=eps_reales_valid, mode='markers', name='Reportado (Real)',
            marker=dict(size=16, color=colores_reales)
        ))
        fig_eecc.update_layout(
            template="plotly_dark", paper_bgcolor='#0d111a', plot_bgcolor='#06080d', height=280,
            margin=dict(l=10, r=10, t=10, b=10), yaxis_title="Beneficio por Acción ($)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_eecc, use_container_width=True)
        st.caption(f"ℹ️ *{fuente_eps}*")

        st.markdown("---")
        st.markdown("#### Matriz Comparativa Relativa vs Peers")
        
        t_pe = "P/E: Cuántas veces beneficios netos descuenta el precio de cotización."
        t_ev = "EV/EBITDA: Valuación global de la firma sobre su flujo de caja operativo limpio."
        t_deuda = "Deuda Neta/EBITDA: Años necesarios para cancelar el pasivo exigible con el EBITDA actual."
        t_liq = "Liquidez Corriente: Capacidad de cubrir pasivos de corto plazo con activo corriente."
        t_mg = "Margen Neto: Porcentaje de utilidad líquida resultante por cada $100 vendidos."
        t_roe = "ROE: Tasa de retorno generada sobre el patrimonio neto contable de los accionistas."

        validos_pe = [d for d in dataset_peers if d["PE"] > 0]
        g_pe = min(validos_pe, key=lambda x: x["PE"])["Ticker"] if validos_pe else ""
        g_roe = max(dataset_peers, key=lambda x: x["ROE"])["Ticker"] if dataset_peers else ""

        filas_peers = []
        for r in dataset_peers:
            c_pe = "class='winner-cell'" if r["Ticker"] == g_pe else ""
            c_roe = "class='winner-cell'" if r["Ticker"] == g_roe else ""
            filas_peers.append(f"<tr><td><b>{r['Ticker']}</b></td><td>{r['Nombre']}</td><td {c_pe}>{r['PE']:.2f}x</td><td>{r['EV']:.2f}x</td><td>{r['DEUDA']:.2f}x</td><td>{r['LIQUIDEZ']:.2f}x</td><td>{r['MARGEN']*100:.1f}%</td><td {c_roe}>{r['ROE']*100:.1f}%</td></tr>")

        matriz_html = f"<div class='table-viewport'><table class='terminal-table'><thead><tr><th>Ticker</th><th>Razón Social</th><th>P/E <span class='th-tooltip'>ⓘ<span class='th-tooltiptext'>{t_pe}</span></span></th><th>EV/EBITDA <span class='th-tooltip'>ⓘ<span class='th-tooltiptext'>{t_ev}</span></span></th><th>Deuda <span class='th-tooltip'>ⓘ<span class='th-tooltiptext'>{t_deuda}</span></span></th><th>Liquidez <span class='th-tooltip'>ⓘ<span class='th-tooltiptext'>{t_liq}</span></span></th><th>Margen <span class='th-tooltip'>ⓘ<span class='th-tooltiptext'>{t_mg}</span></span></th><th>ROE <span class='th-tooltip'>ⓘ<span class='th-tooltiptext'>{t_roe}</span></span></th></tr></thead><tbody>{''.join(filas_peers)}</tbody></table></div>"
        st.markdown(matriz_html, unsafe_allow_html=True)

        diagnostico_multiplos = ia_analisis_multiplos_profundo(d_obj, dataset_peers)
        st.markdown(f"<div class='terminal-card gold-card'><b>Diagnóstico de Múltiplos y Retorno (DuPont):</b><br>{diagnostico_multiplos}</div>", unsafe_allow_html=True)

    # --- PESTAÑA TÉCNICA ---
    with tab_tech:
        st.markdown(f"### 📈 Fuerza Tendencial (DMI / ADX): {t_obj}")
        df_ind = yf.download(t_obj, period="1y", progress=False, session=yf_session)
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
            fig_d.add_trace(go.Scatter(x=df_t.index, y=df_t['Close'], name="Precio", line=dict(color='#ffffff')), row=1, col=1)
            fig_d.add_trace(go.Scatter(x=df_t.index, y=df_t['EMA30'], name="EMA 30", line=dict(color='#d4a34b', dash='dash')), row=1, col=1)
            fig_d.add_trace(go.Scatter(x=df_t.index, y=df_t['+DI'], name="+DI", line=dict(color='#10b981')), row=2, col=1)
            fig_d.add_trace(go.Scatter(x=df_t.index, y=df_t['-DI'], name="-DI", line=dict(color='#f43f5e')), row=2, col=1)
            fig_d.add_trace(go.Scatter(x=df_t.index, y=df_t['ADX'], name="ADX", line=dict(color='#0284c7')), row=2, col=1)
            fig_d.update_layout(template="plotly_dark", paper_bgcolor='#0d111a', plot_bgcolor='#06080d', height=360, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_d, use_container_width=True)

            di_p, di_m, adx_val = df_t['+DI'].iloc[-1], df_t['-DI'].iloc[-1], df_t['ADX'].iloc[-1]
            soporte = df_t['Low'].tail(30).min()
            resistencia = df_t['High'].tail(30).max()
            
            l1 = f"• <b>Dinámica y Momentum:</b> {'Presión compradora dominante (+DI > -DI)' if di_p > di_m else 'Presión vendedora dominante (-DI > +DI)'}, con un ADX en {adx_val:.1f} pts que ratifica {'inercia tendencial activa (>25)' if adx_val > 25 else 'movimiento lateral o indecisión (<25)'}."
            l2 = f"• <b>Comportamiento vs Tendencia:</b> Cotiza {'por sobre su media de 30 ruedas, conservando estructura favorable' if df_t['Close'].iloc[-1] >= df_t['EMA30'].iloc[-1] else 'por debajo de la media de 30 ruedas, advirtiendo cautela en entradas largas'}."
            l3 = f"• <b>Zonas Relevantes:</b> Soporte táctico en <b>${soporte:.2f} USD</b> para control de drawdown y resistencia inmediata en <b>${resistencia:.2f} USD</b>."
            st.markdown(f"<div class='terminal-card'><b>Lectura Técnica (3 Renglones):</b><br>{l1}<br>{l2}<br>{l3}</div>", unsafe_allow_html=True)

    # --- PESTAÑA DCF & REVERSE ---
    with tab_dcf:
        d_fund = obtener_fundamental_robusto(t_obj)
        ingresos, margen_base = d_fund["Rev"], d_fund["MARGEN"]
        wacc_base, g_terminal = 0.115, 0.02
        precio_mkt = d_fund["Precio"]
        shares = 0.20 * 1e9

        sims = 2000
        crec_sim = np.random.normal(0.07, 0.04, sims)
        vals_dcf = []
        for s in range(sims):
            ing = ingresos
            flujos = []
            for y in range(1, 6):
                ing *= (1 + crec_sim[s])
                flujos.append((ing * margen_base * 0.65) / ((1 + wacc_base)**y))
            vt = (ing * margen_base * 0.65 * (1 + g_terminal)) / (wacc_base - g_terminal)
            vals_dcf.append((sum(flujos) + (vt / ((1 + wacc_base)**5))) * 1e9 / shares)
        dcf_mediano = float(np.median([v for v in vals_dcf if v > 0])) if vals_dcf else precio_mkt

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
            <b>Interpretación de Expectativas:</b> El precio actual exige que {t_obj} expanda su flujo libre al <b>{g_implicito*100:+.1f}% anual</b> durante el próximo lustro. Si la tasa es inferior al ROE ({d_fund['ROE']*100:.1f}%), la exigencia del mercado es conservadora y ofrece una asimetría favorable.
            </div>""", unsafe_allow_html=True)

    # --- PESTAÑA MONTE CARLO ---
    with tab_mc:
        st.markdown(f"### 🎲 Simulación Estocástica de Precios (Movimiento Browniano Geométrico)")
        st.markdown("""<div class='terminal-card'>
        <b>Marco Metodológico del Modelo GBM:</b> El Movimiento Browniano Geométrico asume que las cotizaciones siguen la ecuación diferencial estocástica $dS_t = \mu S_t dt + \sigma S_t dW_t$.
        <br>• <b>Deriva ($\mu$):</b> Tendencia central descontando el arrastre de volatilidad.
        <br>• <b>Volatilidad ($\sigma$):</b> Dispersión anualizada observada en las últimas 252 ruedas.
        <br>• <b>Lectura de Percentiles:</b> La banda P90/P10 representa los conos donde se ubica el 80% de los escenarios proyectados. El percentil 10 refleja el soporte de cola en escenarios de estrés.
        </div>""", unsafe_allow_html=True)

        serie_mc = DF_HIST_GLOBAL[t_obj].dropna() if t_obj in DF_HIST_GLOBAL.columns else pd.Series(dtype=float)
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
# 3. PORTAFOLIO Y MODELOS (BENCHMARK REAL Y ESTRATEGIAS)
# ==============================================================================
elif menu == "💼 PORTAFOLIO Y MODELOS":
    st.subheader("💼 Portafolio Consolidado (Auditoría y Benchmark Real)")

    with st.expander("➕ Cargar Operación en Cartera (Compra / Venta con PPC)"):
        col_op1, col_op2, col_op3, col_op4, col_op5 = st.columns(5)
        tipo_op = col_op1.selectbox("Operación:", ["Compra (Aporte)", "Venta (Liquidación)"])
        n_tk = col_op2.selectbox("Ticker:", TOP_100_ARG, index=0)
        n_cant = col_op3.number_input("Nominales:", min_value=1, value=50, step=10)
        n_precio = col_op4.number_input("Precio Cedear (ARS):", min_value=1.0, value=75000.0, step=500.0)
        n_fecha = col_op5.date_input("Fecha:", value=datetime.date.today())
        
        if st.button("Procesar Operación"):
            pos = next((p for p in st.session_state.cartera_operaciones if p["Ticker"] == n_tk), None)
            if "Compra" in tipo_op:
                if pos:
                    c_ant, p_ant = pos["Nominales"], pos["PPC_ARS"]
                    c_nueva = c_ant + n_cant
                    pos["Nominales"] = c_nueva
                    pos["PPC_ARS"] = ((c_ant * p_ant) + (n_cant * n_precio)) / c_nueva
                else:
                    st.session_state.cartera_operaciones.append({"Ticker": n_tk, "Nominales": n_cant, "PPC_ARS": n_precio, "Fecha_Compra": n_fecha, "Dividendos_USD": 0.0, "Yield_Est": 0.02})
            else:
                if pos and pos["Nominales"] >= n_cant:
                    ganancia_usd = ((n_precio - pos["PPC_ARS"]) * n_cant) / DOLAR_MEP
                    pos["Nominales"] -= n_cant
                    st.session_state.ventas_realizadas.append({"Ticker": n_tk, "Nominales": n_cant, "Fecha": n_fecha, "PnL_USD": ganancia_usd})
                    if pos["Nominales"] == 0: st.session_state.cartera_operaciones.remove(pos)
            st.rerun()

    is_ars = st.radio("Moneda:", ["ARS", "USD"], horizontal=True) == "ARS"
    c_tot_usd, v_tot_usd, div_anual_est_usd = 0.0, 0.0, 0.0
    filas_html = []
    datos_pdf_filas = []

    for pos in st.session_state.cartera_operaciones:
        tk, nom, ppc_ars, f_ing = pos["Ticker"], pos["Nominales"], pos["PPC_ARS"], pos.get("Fecha_Compra", datetime.date(2025, 1, 1))
        ratio = RATIOS_CEDEAR.get(tk, 1)
        px_actual_usd = DATOS_RADAR.get(tk, {}).get("precio", (ppc_ars * ratio / DOLAR_MEP))
        costo_usd = ((nom * ppc_ars) / DOLAR_MEP) * ratio
        val_usd = nom * px_actual_usd
        pl_usd = val_usd - costo_usd
        ret_pct = (pl_usd / costo_usd) * 100 if costo_usd > 0 else 0.0
        flujo_pos = val_usd * pos.get("Yield_Est", 0.02)
        
        c_tot_usd += costo_usd
        v_tot_usd += val_usd
        div_anual_est_usd += flujo_pos
        
        filas_html.append(f"""<tr>
            <td><b>{tk}</b></td>
            <td style='font-size:11px; color:#94a3b8;'>{f_ing.strftime('%d/%m/%Y')}</td>
            <td style='font-family:JetBrains Mono;'>{nom}</td>
            <td style='font-family:JetBrains Mono;'>${(ppc_ars if is_ars else ppc_ars*ratio/DOLAR_MEP):,.2f}</td>
            <td style='font-family:JetBrains Mono;'>${(px_actual_usd*DOLAR_MEP/ratio if is_ars else px_actual_usd):,.2f}</td>
            <td style='font-family:JetBrains Mono;'>${(costo_usd*(DOLAR_MEP if is_ars else 1)):,.2f}</td>
            <td style='font-family:JetBrains Mono;'>${(val_usd*(DOLAR_MEP if is_ars else 1)):,.2f}</td>
            <td style='color:{"#34d399" if pl_usd>=0 else "#f43f5e"}; font-weight:700;'>${(pl_usd*(DOLAR_MEP if is_ars else 1)):,.2f}</td>
            <td style='color:{"#34d399" if ret_pct>=0 else "#f43f5e"}; font-weight:700;'>{ret_pct:+.2f}%</td>
            <td><span class='badge-state {"badge-buy" if ret_pct < 20 and ret_pct > -10 else "badge-hold" if ret_pct >= 20 else "badge-sell"}'>{"ACUMULAR" if ret_pct < 20 and ret_pct > -10 else "MANTENER" if ret_pct >= 20 else "REVISAR"}</span></td>
        </tr>""")
        
        datos_pdf_filas.append([tk, f_ing.strftime('%d/%m/%Y'), str(nom), f"${costo_usd:,.2f}", f"${val_usd:,.2f}", f"${pl_usd:,.2f}", f"{ret_pct:+.2f}%", f"${flujo_pos:,.2f}"])

    st.markdown(f"<div class='table-viewport'><table class='terminal-table'><thead><tr><th>Ticker</th><th>Fecha Ingreso</th><th>Nominales</th><th>PPC</th><th>Precio Actual</th><th>Invertido</th><th>Valuación</th><th>P&L Neto</th><th>Total Return</th><th>Semáforo</th></tr></thead><tbody>{''.join(filas_html)}</tbody></table></div>", unsafe_allow_html=True)

    k1, k2, k3, k4, k5 = st.columns(5)
    ret_tot = ((v_tot_usd - c_tot_usd) / c_tot_usd) * 100 if c_tot_usd > 0 else 0.0
    mon = "ARS" if is_ars else "USD"
    conv = DOLAR_MEP if is_ars else 1.0
    alpha = ret_tot - DATOS_RADAR.get("SPY", {}).get("YTD", 0.0)
    
    k1.metric("Capital Invertido", f"${(c_tot_usd*conv):,.0f} {mon}")
    k2.metric("Valuación Actual", f"${(v_tot_usd*conv):,.0f} {mon}")
    k3.metric("Flujo Divs Anual Est.", f"${(div_anual_est_usd*conv):,.0f} {mon}")
    k4.metric("Total Return", f"{ret_tot:+.2f}%")
    k5.metric("Alpha vs SPY", f"{alpha:+.2f}%", delta_color="normal" if alpha >= 0 else "inverse")

    if HAS_REPORTLAB:
        def generar_pdf():
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
            styles = getSampleStyleSheet()
            elementos = [
                Paragraph("<b>APEX TERMINAL - INFORME AUDITADO DE CARTERA</b>", styles['Heading1']),
                Paragraph(f"Fecha: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')} | Moneda: USD | Dólar MEP: ${DOLAR_MEP:,.2f}", styles['Normal']),
                Spacer(1, 15),
                Table([["Capital Invertido", f"${c_tot_usd:,.2f}"], ["Valuación Mercado", f"${v_tot_usd:,.2f}"], ["Renta Anual Divs Est.", f"${div_anual_est_usd:,.2f}"], ["Retorno Cartera", f"{ret_tot:+.2f}%"]], colWidths=[200, 300]),
                Spacer(1, 15),
                Table([["Ticker", "Fecha", "Cant", "Costo", "Valuación", "P&L", "Ret %", "Div Est"]] + datos_pdf_filas, colWidths=[45, 55, 35, 65, 65, 65, 50, 70])
            ]
            doc.build(elementos)
            buffer.seek(0)
            return buffer
            
        st.download_button("📥 Descargar Reporte Completo en PDF", generar_pdf(), "Reporte_Cartera.pdf", "application/pdf")

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

    st.markdown("---")
    st.subheader("🎯 Carteras Modelo y Asignación Estratégica por Perfil")

    estrategias_detalle = {
        "💰 Income & Dividendos": [
            ("KO", "**Coca-Cola:** Payout ratio predecible, flujo inelástico y récord ininterrumpido de dividendos crecientes."),
            ("XOM", "**ExxonMobil:** Breakeven operativo líder por barril, permitiendo recompras y dividendos líquidos."),
            ("JNJ", "**Johnson & Johnson:** Calificación crediticia AAA con demanda farmacéutica inmune al ciclo macro."),
            ("PBR", "**Petrobras:** Dividend yield de dos dígitos respaldado por extracción en aguas ultraprofundas.")
        ],
        "🏰 Quality & Wide Moat": [
            ("ASML", "**ASML:** Monopolio absoluto en litografía ultravioleta extrema (EUV), fijación de precios cautiva."),
            ("V", "**Visa:** Red de pagos de altísimo retorno sobre capital con márgenes operativos sobre el 55%."),
            ("MSFT", "**Microsoft:** Infraestructura B2B y nube crítica que genera altos costos de cambio."),
            ("GOOGL", "**Alphabet:** Dominio absoluto en búsquedas globales y reservas masivas de liquidez.")
        ],
        "🚀 Crecimiento Secular (Growth)": [
            ("NVDA", "**NVIDIA:** Liderazgo estructural en hardware acelerado para entrenamiento e inferencia de IA."),
            ("MELI", "**MercadoLibre:** Penetración sinérgica en e-commerce y fintech bancarizada en América Latina."),
            ("AMD", "**AMD:** Ganancia constante de cuota de mercado en procesadores de centros de datos.")
        ],
        "⚖️ Value Investing (Descuento)": [
            ("VIST", "**Vista Energy:** Operador de shale oil de menor lifting cost en Vaca Muerta con expansión sostenida."),
            ("YPF", "**YPF:** Salida de activos maduros para focalizar el 100% de la inversión en el no convencional."),
            ("BMA", "**Banco Macro:** Múltiplos comprimidos respecto al valor libro en un contexto de normalización monetaria.")
        ]
    }

    t_est = st.tabs(list(estrategias_detalle.keys()))
    for idx, (cat, items) in enumerate(estrategias_detalle.items()):
        with t_est[idx]:
            for tk, desc in items:
                st.markdown(f"• {desc}")

    st.markdown("---")
    st.subheader("🧠 Asignación Óptima de Markowitz (Máximo Ratio Sharpe)")
    if st.button("Calcular Asignación Óptima"):
        tks_cartera = list(set([p["Ticker"] for p in st.session_state.cartera_operaciones]))
        if len(tks_cartera) < 2:
            st.error("Se requieren al menos 2 activos distintos en cartera para calcular la matriz de covarianza.")
        else:
            _, df_opt = descargar_mercado_pool(tks_cartera)
            rets = df_opt[tks_cartera].pct_change().dropna()
            mean_ret = rets.mean() * 252
            cov_mat = rets.cov() * 252
            
            def min_sharpe(w):
                p_r = np.sum(mean_ret * w)
                p_v = np.sqrt(np.dot(w.T, np.dot(cov_mat, w)))
                return -(p_r - 0.04) / p_v
                
            n = len(tks_cartera)
            res = sco.minimize(min_sharpe, n * [1./n], method='SLSQP', bounds=tuple((0, 1) for _ in range(n)), constraints=({'type': 'eq', 'fun': lambda x: np.sum(x) - 1}))
            
            fig_pie = px.pie(values=res.x, names=tks_cartera, title="Ponderación Sugerida", hole=0.45,
                             color_discrete_sequence=['#d4a34b', '#0284c7', '#10b981', '#f43f5e', '#a855f7'])
            fig_pie.update_layout(template="plotly_dark", paper_bgcolor='#0d111a', plot_bgcolor='#06080d')
            st.plotly_chart(fig_pie, use_container_width=True)
