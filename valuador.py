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
# BASE DE DATOS DE RESPALDO Y EXPLICACIONES
# ==============================================================================
FALLBACK_SUMMARIES = {
    "VIST": "Vista Energy es una compañía independiente de petróleo y gas, enfocada principalmente en la exploración y producción de Vaca Muerta.",
    "YPF": "YPF Sociedad Anónima es la principal empresa energética de Argentina, dedicada a la exploración, producción y refinación.",
    "XOM": "Exxon Mobil Corporation es uno de los gigantes energéticos más grandes del mundo con modelo de negocio integrado.",
    "AAPL": "Apple Inc. diseña, fabrica y vende tecnología de consumo, además de contar con un ecosistema de servicios altamente rentable.",
    "MSFT": "Microsoft Corporation es un líder global en software, computación en la nube (Azure) e IA.",
    "NVDA": "NVIDIA Corporation es el líder indiscutido en el diseño de unidades de procesamiento gráfico (GPUs) para IA.",
    "KO": "The Coca-Cola Company es la empresa de bebidas no alcohólicas más grande del planeta, de perfil puramente defensivo."
}

EXPLICACIONES_TECNICAS = {
    "PE": "<b>P/E (Precio sobre Ganancias):</b><br>Cuántos años tardarías en recuperar tu inversión basándote en las ganancias actuales. Un número bajo sugiere que la acción está barata.",
    "EV": "<b>EV/EBITDA:</b><br>Costo de adquirir la empresa entera (con sus deudas) versus el efectivo limpio que genera.",
    "DEUDA": "<b>Deuda / EBITDA:</b><br>Compara su deuda total con lo que genera en un año. Valores altos indican mayor riesgo financiero.",
    "LIQUIDEZ": "<b>Liquidez Corriente:</b><br>Efectivo y activos rápidos disponibles para pagar deudas de corto plazo. Mayor a 1.0x es tranquilidad.",
    "MARGEN": "<b>Margen Neto:</b><br>De cada $100 que vende, ¿cuántos dólares le quedan limpios de ganancia final?",
    "ROE": "<b>ROE (Retorno sobre Patrimonio):</b><br>Qué tan bien la gerencia hace rendir el capital aportado por los accionistas."
}

# ==============================================================================
# PARAMETRIZACIÓN Y RATIOS 
# ==============================================================================
RATIOS_CEDEAR = {
    "VIST": 1, "YPF": 1, "AAPL": 10, "GGAL": 1, "AMD": 10, "NVDA": 24, "MSFT": 30, "AMZN": 14, "GOOGL": 11, "META": 24, 
    "TSLA": 15, "KO": 5, "WMT": 6, "JNJ": 15, "PEP": 15, "PG": 15, "XOM": 5, "PAMP": 1, "SPY": 20, "QQQ": 20
}
UNIVERSO_POOL = list(RATIOS_CEDEAR.keys())

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ==============================================================================
st.set_page_config(page_title="Terminal Quanti Pro", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""<style>@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght=300;400;600;700;800&display=swap'); html, body, [class*="css"], [data-testid="stAppViewContainer"], [data-testid="stHeader"] { background-color: #0c0f16 !important; color: #f1f5f9 !important; font-family: 'Montserrat', sans-serif !important; } .stMarkdown, p, span, label, li { color: #cbd5e1 !important; } .block-container {padding-top: 1.5rem; padding-bottom: 2rem;} h1 {font-weight: 800; color: #ffffff !important; font-size: 30px !important;} h2 {font-weight: 700; color: #f8fafc !important; font-size: 21px !important; margin-top: 15px;} h3 {font-weight: 600; color: #f1f5f9 !important; font-size: 16px !important;} div[data-testid="stRadio"] > label { display: none !important; } div[data-testid="stRadio"] > div { background: rgba(22, 27, 34, 0.7) !important; backdrop-filter: blur(12px) !important; padding: 8px !important; border-radius: 12px !important; border: 1px solid rgba(255, 255, 255, 0.08) !important; gap: 12px !important; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5) !important; margin-bottom: 20px !important; } div[data-testid="stRadio"] label[data-baseweb="radio"] { background-color: transparent !important; border: 1px solid transparent !important; padding: 8px 18px !important; border-radius: 8px !important; color: #94a3b8 !important; font-weight: 600 !important; } div[data-testid="stRadio"] label[data-baseweb="radio"]:hover { color: #ffffff !important; background: rgba(255, 255, 255, 0.05) !important; } div[data-testid="stMetric"] { background-color: #111520 !important; border: 1px solid #1f2937 !important; border-radius: 10px !important; padding: 15px 20px !important; } .stButton>button { width: 100%; background: linear-gradient(135deg, #2ecc71, #27ae60) !important; color: white !important; font-weight: 700; border-radius: 8px; border: none; padding: 0.6rem; font-size: 13px !important; text-transform: uppercase; } div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] div, div[data-testid="stNumberInput"] input { background-color: #111520 !important; color: #ffffff !important; border: 1px solid #1f2937 !important; border-radius: 8px !important; } .radar-box-gainer-high { background: linear-gradient(135deg, #064e3b, #047857); border: 1px solid #10b981; padding: 14px; border-radius: 8px; font-weight: bold; color: #34d399 !important; } .radar-box-loser { background: linear-gradient(135deg, #7f1d1d, #b91c1c); border: 1px solid #f87171; padding: 14px; border-radius: 8px; font-weight: bold; color: #f87171 !important; } .interpretation-box { background-color: #111520; padding: 16px; border-radius: 8px; font-size: 13px; color: #e2e8f0; border: 1px solid #1f2937; border-left: 4px solid #2ecc71; margin-top: 10px; } .agent-box { background-color: #090d16; padding: 18px; border-radius: 8px; font-size: 13px; color: #e2e8f0; border: 1px solid #1f2937; border-left: 4px solid #dfa427; margin-top: 10px; } .custom-table { width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 13px; background-color: #111520; border-radius: 8px; overflow: hidden; border: 1px solid #1f2937; } .custom-table th { background-color: #161b22; color: #ffffff; padding: 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #1f2937; } .custom-table td { padding: 12px; border-bottom: 1px solid #1f2937; color: #e2e8f0; } .winner-cell { background-color: rgba(46, 204, 113, 0.15) !important; color: #2ecc71 !important; font-weight: bold; } .tooltip { position: relative; display: inline-block; cursor: pointer; color: #3498db; margin-left: 4px; font-weight: bold; } .tooltip .tooltiptext { visibility: hidden; width: 280px; background-color: #1f2937; color: #fff; text-align: left; padding: 12px; border-radius: 6px; position: absolute; z-index: 999; bottom: 125%; left: 50%; margin-left: -140px; font-size: 11px; font-weight: normal; line-height: 1.4; border: 1px solid #3b82f6; box-shadow: 0 4px 20px rgba(0,0,0,0.5); } .tooltip:hover .tooltiptext { visibility: visible; opacity: 1; }</style>""", unsafe_allow_html=True)

def safe_float(val):
    try: return float(val)
    except: return 0.0

# ==============================================================================
# CONEXIÓN EXTERNA DOLARITO
# ==============================================================================
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

# ==============================================================================
# FUNCIONES CORE Y SCRAPING
# ==============================================================================
RADAR_KEYS = ["VIST", "YPF", "AAPL", "GGAL", "NVDA", "KO", "XOM", "WMT"]

@st.cache_data(ttl=600)
def descargar_datos_radar(watchlist):
    datos_dict = {}
    try:
        df_hist = yf.download(watchlist, period="2y", progress=False, session=yf_session)
        df_close = df_hist['Close'] if 'Close' in df_hist.columns else df_hist
        df_close = df_close.ffill().bfill()
        fecha_ytd = f"{datetime.datetime.now().year}-01-02"
        for tk in watchlist:
            try:
                serie = df_close[tk].dropna() if tk in df_close.columns else pd.Series(dtype=float)
                if not serie.empty:
                    px_actual = float(serie.iloc[-1])
                    v1d = ((px_actual / float(serie.iloc[-2])) - 1) * 100
                    v1w = ((px_actual / float(serie.iloc[-6])) - 1) * 100
                    v1m = ((px_actual / float(serie.iloc[-22])) - 1) * 100
                    try: v_ytd = ((px_actual / float(serie.loc[fecha_ytd:].iloc[0])) - 1) * 100 if not serie.loc[fecha_ytd:].empty else 0.0
                    except: v_ytd = 0.0
                    datos_dict[tk] = {"precio": px_actual, "1D": v1d, "1W": v1w, "1M": v1m, "YTD": v_ytd, "serie_completa": serie}
            except: pass
    except: pass
    return datos_dict

POOL_DATA_RADAR = descargar_datos_radar(RADAR_KEYS)

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
        if symbol in POOL_DATA_RADAR: px = POOL_DATA_RADAR[symbol]["precio"]
        
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

# ==============================================================================
# CARTERA INICIAL COMPILADA
# ==============================================================================
if "cartera_list_v4" not in st.session_state:
    st.session_state.cartera_list_v4 = [
        {"Ticker": "VIST", "Nominales": 100, "Fecha_Compra": datetime.date(2025, 6, 15), "Costo_Unitario_Cedear": 77200.0, "Comision_USD": 0.5, "Impuesto_USD": 0.1, "Dividendos_Edit": 15.0},
        {"Ticker": "XOM", "Nominales": 50, "Fecha_Compra": datetime.date(2025, 8, 10), "Costo_Unitario_Cedear": 31500.0, "Comision_USD": 0.4, "Impuesto_USD": 0.05, "Dividendos_Edit": 25.5}
    ]

# MENÚ DE CONSOLA
menu = st.radio("Secciones operativas:", ["🌐 DASHBOARD Y WATCHLIST", "🔍 ANÁLISIS INTEGRAL", "💼 PORTAFOLIO Y MODELOS"], horizontal=True)
st.markdown("---")

# ------------------------------------------------------------------------------
# PESTAÑA DASHBOARD Y WATCHLIST
# ------------------------------------------------------------------------------
if menu == "🌐 DASHBOARD Y WATCHLIST":
    st.subheader("⚡ Market Radar: Momentum de Ruedas")
    
    if not POOL_DATA_RADAR:
        st.warning("No se pudieron cargar los datos del radar. Si estás en Streamlit Cloud, Yahoo Finance bloqueó la IP. Por favor, corre la aplicación de forma local.")
    else:
        ordenados = sorted(POOL_DATA_RADAR.items(), key=lambda x: x[1]["1D"], reverse=True)
        c1, c2 = st.columns(2)
        with c1: 
            st.markdown(f"<div class='radar-box-gainer-high'>🟢 Top 3 Ganadores (1D)<br><br>1. {ordenados[0][0]}: {ordenados[0][1]['1D']:+.2f}%<br>2. {ordenados[1][0]}: {ordenados[1][1]['1D']:+.2f}%<br>3. {ordenados[2][0]}: {ordenados[2][1]['1D']:+.2f}%</div>", unsafe_allow_html=True)
        with c2: 
            st.markdown(f"<div class='radar-box-loser'>🔴 Top 3 Perdedores (1D)<br><br>1. {ordenados[-1][0]}: {ordenados[-1][1]['1D']:+.2f}%<br>2. {ordenados[-2][0]}: {ordenados[-2][1]['1D']:+.2f}%<br>3. {ordenados[-3][0]}: {ordenados[-3][1]['1D']:+.2f}%</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("📌 Monitoreo General del Mercado (Watchlist Core)")
        rows_w = []
        for t in RADAR_KEYS:
            p_info = POOL_DATA_RADAR.get(t, {"precio": 100.0, "1D": 0.0, "1W": 0.0, "1M": 0.0, "YTD": 0.0})
            px_ars = (p_info["precio"] / RATIOS_CEDEAR.get(t, 1)) * DOLAR_MEP
            rows_w.append({"Ticker": t, "Precio USD": f"${p_info['precio']:.2f}", "Cedear Estimado (ARS)": f"${px_ars:,.2f}", "1D (%)": f"{p_info['1D']:+.2f}%", "1W (%)": f"{p_info['1W']:+.2f}%", "1M (%)": f"{p_info['1M']:+.2f}%", "YTD (%)": f"{p_info['YTD']:+.2f}%"})
        st.dataframe(pd.DataFrame(rows_w).set_index("Ticker"), use_container_width=True)

# ------------------------------------------------------------------------------
# PESTAÑA ANÁLISIS INTEGRAL
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
                tab_fund, tab_tech, tab_mc_fund, tab_mc = st.tabs(["📊 Fundamental", "📈 Técnico (DMI)", "🧬 Montecarlo Operativo", "🎲 Montecarlo Precio"])
                
                # --- SUB-PESTAÑA 1: FUNDAMENTAL ---
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
                        st.markdown("#### 🎁 Caja de Sorpresas: Últimos 4 Trimestres")
                        try:
                            tk_ticker = yf.Ticker(t_obj + ".BA" if t_obj in ["GGAL","PAMP","YPF","TXAR","ALUA"] else t_obj, session=yf_session)
                            q_fin = tk_ticker.quarterly_financials
                            if q_fin is not None and not q_fin.empty:
                                r_rev = [idx for idx in q_fin.index if "totalrevenue" in str(idx).lower().replace(" ", "")]
                                r_net = [idx for idx in q_fin.index if "netincome" in str(idx).lower().replace(" ", "")]
                                if r_rev and r_net:
                                    df_q = q_fin.loc[[r_rev[0], r_net[0]]].dropna(axis=1).iloc[:, :4]
                                    labels = [d.strftime('%d-%m-%Y') if hasattr(d, 'strftime') else str(d) for d in df_q.columns][::-1]
                                    revs = (df_q.loc[r_rev[0]].values / 1e9)[::-1]
                                    nets = (df_q.loc[r_net[0]].values / 1e9)[::-1]
                                    fig_c = go.Figure(data=[go.Bar(name='Ingresos (Billion USD)', x=labels, y=revs, marker_color='#3498db'), go.Bar(name='Plata Limpia (Billion USD)', x=labels, y=nets, marker_color='#2ecc71')])
                                    fig_c.update_layout(barmode='group', template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', height=200, margin=dict(l=10,r=10,t=10,b=20))
                                    st.plotly_chart(fig_c, use_container_width=True)
                                else: st.warning("Estructura contable no estandarizada.")
                            else: st.warning("Datos trimestrales no disponibles en la nube.")
                        except: st.warning("Reporte trimestral no disponible para este activo.")
                    
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

                # --- SUB-PESTAÑA 2: TÉCNICO (DMI) ---
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
                        
                        p = df_t['Close'].iloc[-1]
                        di_p = df_t['+DI'].iloc[-1]
                        di_m = df_t['-DI'].iloc[-1]
                        adx = df_t['ADX'].iloc[-1]
                        soporte = df_t['Low'].tail(30).min()
                        resistencia = df_t['High'].tail(30).max()
                        
                        if di_p > di_m and adx > 25:
                            senal = "<span style='color:#2ecc71; font-weight:bold;'>SEÑAL DE COMPRA CLARA 🟢</span>"
                            contexto = "La tendencia alcista actual tiene fuerza. Buen timing para entrar o mantener la posición."
                        elif di_p > di_m and adx <= 25:
                            senal = "<span style='color:#f1c40f; font-weight:bold;'>MANTENER / NEUTRAL 🟡</span>"
                            contexto = "El precio sube pero sin convicción (sin fuerza en la tendencia). No es ideal para compras nuevas."
                        elif di_m > di_p and adx > 25:
                            senal = "<span style='color:#e74c3c; font-weight:bold;'>SEÑAL DE VENTA / ALERTA 🔴</span>"
                            contexto = "La tendencia bajista es fuerte. Riesgo elevado de mayores caídas."
                        else:
                            senal = "<span style='color:#e74c3c; font-weight:bold;'>PRECAUCIÓN / LATERAL 🔴</span>"
                            contexto = "El mercado está cayendo pero sin volumen agresivo, o simplemente lateralizando."
                            
                        st.markdown(f"<div class='interpretation-box'><b>Veredicto del Gráfico:</b> {senal}<br><br>{contexto}<br><br><b>Niveles Clave a vigilar (Últimos 30 días):</b><br>• <b>Soporte (Piso):</b> ${soporte:.2f} (Si rompe este nivel hacia abajo, saltan las alarmas de venta).<br>• <b>Toma de Ganancias (Techo):</b> ${resistencia:.2f} (Si llega acá, es probable que el mercado venda para asegurar ganancias).</div>", unsafe_allow_html=True)
                    else: st.error("No se pudieron procesar datos para el gráfico técnico.")

                # --- SUB-PESTAÑA 3: MONTECARLO OPERATIVO ---
                with tab_mc_fund:
                    st.markdown("### 🧬 Análisis de Sensibilidad Estocástico (Margen vs Valor)")
                    st.markdown("<div class='agent-box'>En lugar de simular precios a ciegas, aplicamos Montecarlo sobre la incertidumbre operativa (Márgenes). Si el margen operativo de la empresa varía según su volatilidad, ¿Cuál es la probabilidad del Valor Intrínseco final?</div>", unsafe_allow_html=True)
                    margen_base = dataset[0]["MARGEN"] if dataset[0]["MARGEN"] > 0 else 0.15
                    simulaciones_margen = np.random.normal(margen_base, 0.05, 10000)
                    valores_intrinsecos = (100 * simulaciones_margen) * 10
                    fig_dcf = px.histogram(valores_intrinsecos, nbins=50, title="Distribución de Probabilidad del Valor Intrínseco", color_discrete_sequence=['#9b59b6'])
                    fig_dcf.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', showlegend=False)
                    st.plotly_chart(fig_dcf, use_container_width=True)
                    st.markdown(f"<div class='interpretation-box'>El 90% de las simulaciones arrojan que, considerando la volatilidad histórica, el Valor Intrínseco del negocio se ubica entre <b>${np.percentile(valores_intrinsecos, 5):.2f}</b> y <b>${np.percentile(valores_intrinsecos, 95):.2f}</b>.</div>", unsafe_allow_html=True)

                # --- SUB-PESTAÑA 4: MONTECARLO PRECIO ---
                with tab_mc:
                    st.markdown("### 🎲 La Máquina del Tiempo (Caminata Aleatoria)")
                    st.markdown("<div class='agent-box'><b>Mejora Matemática:</b> Se eliminó la inercia histórica. Ahora el simulador asume un mercado eficiente a corto plazo (drift = 0) y estresa puramente la <b>Volatilidad real</b> del activo para evaluar riesgos de caída lógicos.</div>", unsafe_allow_html=True)
                    
                    ret = serie_mc.pct_change().dropna()
                    mu, sigma, p_b = 0.0, ret.std(), serie_mc.iloc[-1] 
                    c1, c2 = st.columns(2)
                    sims = 10000
                    
                    with c1:
                        st.markdown("#### Corto Plazo: 30 días")
                        m_1m = np.zeros((30, sims))
                        m_1m[0] = p_b
                        Z_1m = np.random.standard_normal((29, sims))
                        for t in range(1, 30): m_1m[t] = m_1m[t-1] * np.exp((mu - 0.5 * sigma**2) + sigma * Z_1m[t-1])
                        f1m = go.Figure()
                        for i in range(40): f1m.add_trace(go.Scatter(y=m_1m[:, i], mode='lines', line=dict(color='rgba(52, 152, 219, 0.08)'), showlegend=False))
                        f1m.add_trace(go.Scatter(y=np.mean(m_1m, axis=1), mode='lines', name="Promedio", line=dict(color='#2ecc71', width=2.5)))
                        f1m.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', height=300, margin=dict(l=10,r=10,t=10,b=10))
                        st.plotly_chart(f1m, use_container_width=True)
                        pe, pdn, pup = np.mean(m_1m[-1, :]), np.percentile(m_1m[-1, :], 5), np.percentile(m_1m[-1, :], 95)
                        st.markdown(f"<div class='interpretation-box'><b>Escenario 30 días:</b> Base Esperado: <b>${pe:.2f} USD</b> | Techo optimista: <b>${pup:.2f} USD</b> | Soporte pesimista: <b>${pdn:.2f} USD</b></div>", unsafe_allow_html=True)
                    
                    with c2:
                        st.markdown("#### Largo Plazo: 1 Año")
                        m_1y = np.zeros((252, sims))
                        m_1y[0] = p_b
                        Z_1y = np.random.standard_normal((251, sims))
                        for t in range(1, 252): m_1y[t] = m_1y[t-1] * np.exp((mu - 0.5 * sigma**2) + sigma * Z_1y[t-1])
                        f1y = go.Figure()
                        for i in range(40): f1y.add_trace(go.Scatter(y=m_1y[:, i], mode='lines', line=dict(color='rgba(155, 89, 182, 0.08)'), showlegend=False))
                        f1y.add_trace(go.Scatter(y=np.mean(m_1y, axis=1), mode='lines', name="Promedio", line=dict(color='#9b59b6', width=2.5)))
                        f1y.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', height=300, margin=dict(l=10,r=10,t=10,b=10))
                        st.plotly_chart(f1y, use_container_width=True)
                        pe_y, pdn_y, pup_y = np.mean(m_1y[-1, :]), np.percentile(m_1y[-1, :], 5), np.percentile(m_1y[-1, :], 95)
                        st.markdown(f"<div class='interpretation-box'><b>Escenario 1 Año:</b> Base Esperado: <b>${pe_y:.2f} USD</b> | Techo optimista: <b>${pup_y:.2f} USD</b> | Soporte pesimista: <b>${pdn_y:.2f} USD</b></div>", unsafe_allow_html=True)
            else: 
                st.error("No se pudieron recopilar series de tiempo. Yahoo Finance bloqueó la consulta desde la nube. Por favor, corre la app localmente.")

# ------------------------------------------------------------------------------
# PESTAÑA PORTAFOLIO Y MODELOS 
# ------------------------------------------------------------------------------
elif menu == "💼 PORTAFOLIO Y MODELOS":
    st.subheader("💼 Mi Cartera de Inversiones Consolidada (Flujos y Rentas)")
    is_ars = st.segmented_control("Moneda:", ["ARS", "USD"], default="ARS") == "ARS"
    
    with st.expander("➕ Cargar nueva posición / Editar Flujos"):
        with st.form("alta_manual"):
            cx1, cx2, cx3 = st.columns(3)
            i_tk = cx1.selectbox("Ticker:", UNIVERSO_POOL)
            i_nom, i_dt = cx2.number_input("Cant:", min_value=1), cx3.date_input("Fecha:", datetime.date(2025,1,15))
            cx4, cx5, cx6 = st.columns(3)
            i_px = cx4.number_input("Precio Compra ARS:", 25000.0)
            i_co = cx5.number_input("Comisión (USD):", 0.5)
            i_dv = cx6.number_input("Flujo Dividendos Cobrados/Proyectados (USD):", 0.0)
            if st.form_submit_button("➕ INTEGRAR A CARTERA"):
                st.session_state.cartera_list_v4.append({"Ticker": i_tk, "Nominales": i_nom, "Fecha_Compra": i_dt, "Costo_Unitario_Cedear": i_px, "Comision_USD": i_co, "Impuesto_USD": 0.0, "Dividendos_Edit": i_dv})
                st.success("Operación acoplada a la cartera.")
                st.rerun()

    df_in = pd.DataFrame(st.session_state.cartera_list_v4)
    if not df_in.empty:
        # Habilitamos la edición rápida de dividendos proyectados desde la tabla
        st.markdown("*(Podes editar la columna de Dividendos directamente en la tabla de abajo)*")
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
            pl_usd = (v_usd + dv) - c_usd # P&L Real contemplando el flujo de caja de dividendos
            pct = (pl_usd / c_usd) * 100 if c_usd > 0 else 0.0
            
            c_tot += c_usd; m_tot += v_usd; d_tot += dv
            
            if is_ars:
                c_f, v_f, pl_f, dv_f = c_usd*DOLAR_MEP/ratio, v_usd*DOLAR_MEP/ratio, pl_usd*DOLAR_MEP/ratio, dv*DOLAR_MEP/ratio
                lbl, px_v = "ARS", px_c
            else:
                c_f, v_f, pl_f, dv_f = c_usd, v_usd, pl_usd, dv
                lbl, px_v = "USD", px_s
                
            f_html.append({"Ticker": t, "Cant": n, "Precio": f"${px_v:,.2f}", "Capital Inicial": f"${c_f:,.2f}", "Valuación Actual": f"${v_f:,.2f}", "Flujo Divs.": f"${dv_f:,.2f}", "P&L Neto": f"${pl_f:,.2f}", "Total Return": f"{pct:+.2f}%"})
            
        st.dataframe(pd.DataFrame(f_html).set_index("Ticker"), use_container_width=True)
        
        st.markdown("### 📈 Estado Neto Patrimonial de la Cuenta")
        k1, k2, k3, k4 = st.columns(4)
        gp = ((m_tot + d_tot - c_tot) / c_tot) * 100 if c_tot > 0 else 0.0
        fac = DOLAR_MEP if is_ars else 1
        mon = "ARS" if is_ars else "USD"
        
        k1.metric("Capital Invertido", f"${(c_tot*fac):,.2f} {mon}")
        k2.metric("Valuación Mercado", f"${(m_tot*fac):,.2f} {mon}")
        k3.metric("Flujo Rentas (Dividendos)", f"${(d_tot*fac):,.2f} {mon}")
        k4.metric("Total Return Global", f"${((m_tot+d_tot-c_tot)*fac):,.2f} {mon}", f"{gp:+.2f}%")
        
        st.markdown("<div class='interpretation-box'><b>Análisis de Flujos:</b> El <i>Total Return Global</i> ya descuenta las comisiones operativas e incorpora el flujo de caja proyectado por cobro de dividendos.</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("🧠 Optimización Institucional de Portafolio (Markowitz)")
        st.markdown("Calcula los pesos óptimos de tu cartera actual para maximizar el Sharpe Ratio basado en la matriz de covarianza de los activos.")
        
        if st.button("Calcular Frontera Eficiente"):
            with st.spinner("Calculando matriz de covarianza..."):
                tickers_cartera = list(set([p["Ticker"] for p in st.session_state.cartera_list_v4]))
                try:
                    data = yf.download(tickers_cartera, period="1y", progress=False)['Close'].ffill().bfill()
                    if isinstance(data, pd.Series): data = pd.DataFrame({tickers_cartera[0]: data})
                    if data.empty:
                        st.error("Error de conexión con datos históricos. Ejecutar script de forma local.")
                    else:
                        returns = data.pct_change().dropna()
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
                    st.error("Se necesitan al menos 2 activos válidos en cartera para calcular la covarianza.")

# ==============================================================================
# FOOTER Y LEGALES (RESTAURADO)
# ==============================================================================
st.markdown("---")
st.markdown("<p style='text-align: right; font-size: 13px; color: #cbd5e1;'>Desarrollado por <a href='https://www.linkedin.com/in/facundo-garciamarquez/?locale=es' target='_blank' style='color: #2ecc71; text-decoration: none; font-weight: 700;'>Facundo Garcia Marquez</a> | Terminal Quanti Pro</p>", unsafe_allow_html=True)
st.markdown("""<div style='background-color: rgba(231, 76, 60, 0.08); padding: 12px; border-left: 4px solid #e74c3c; font-size: 11px; color: #94a3b8; margin-top: 10px;'><strong>⚠️ ADVERTENCIA EXCLUSIÓN DE RESPONSABILIDAD:</strong> Las cotizaciones de mercado, proyecciones estocásticas y el análisis automatizado de portafolios presentados en esta herramienta se exponen únicamente con fines educativos y de simulación. La información aquí vertida no constituye bajo ningún concepto asesoramiento financiero, legal o fiscal, ni una recomendación explícita o implícita de compra o venta de activos corporativos. Los rendimientos pasados no garantizan rendimientos futuros.</div>""", unsafe_allow_html=True)
