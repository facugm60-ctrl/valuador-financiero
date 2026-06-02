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
# DISFRAZ ANTI-BLOQUEO PARA YAHOO FINANCE
# ------------------------------------------------------------------------------
yf_session = requests.Session()
yf_session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
})

try:
    from deep_translator import GoogleTranslator
    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False

# ==============================================================================
# BASE DE DATOS DE RESPALDO (POR SI FALLA LA NUBE)
# ==============================================================================
FALLBACK_SUMMARIES = {
    "VIST": "Vista Energy es una compañía independiente de petróleo y gas, enfocada principalmente en la exploración y producción de Vaca Muerta, Argentina. Es uno de los operadores líderes en la cuenca, destacándose por su alta eficiencia operativa, bajos costos de extracción y rápida expansión en la producción de crudo no convencional (shale oil).",
    "YPF": "YPF Sociedad Anónima es la principal empresa energética de Argentina, dedicada a la exploración, producción, refinación y venta de petróleo, gas y derivados. Como líder histórico del país y actor central en Vaca Muerta, controla gran parte del mercado de combustibles y está expandiendo su infraestructura hacia el GNL.",
    "XOM": "Exxon Mobil Corporation es uno de los giants energéticos más grandes del mundo. Su modelo de negocio integrado (exploración, producción y refinación) y su enorme escala le permiten generar flujos de caja masivos y sostener una política de dividendos robusta.",
    "AAPL": "Apple Inc. diseña, fabrica y vende tecnología de consumo, además de contar con un ecosistema de servicios altamente rentable (App Store, iCloud). Su ventaja competitiva radica en la fidelidad de sus usuarios y un ecosistema cerrado que le permite altos márgenes.",
    "MSFT": "Microsoft Corporation es un líder global en software y computación en la nube (Azure). Domina la infraestructura corporativa mundial, complementada con su suite Office 365, Windows y su fuerte liderazgo actual en inteligencia artificial aplicada a negocios.",
    "NVDA": "NVIDIA Corporation es el líder indiscutido en el diseño de unidades de procesamiento gráfico (GPUs). Es la columna vertebral tecnológica de la revolución de la Inteligencia Artificial, proveyendo los chips esenciales para los centros de datos.",
    "KO": "The Coca-Cola Company es la empresa de bebidas no alcohólicas más grande del planeta. Posee una cartera diversificada y una red de distribución inigualable. Es una acción puramente defensiva, valorada por su capacidad para protegerse de la inflación."
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
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ==============================================================================
st.set_page_config(page_title="Terminal Quanti Pro", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght=300;400;600;700;800&display=swap');
    html, body, [class*="css"], [data-testid="stAppViewContainer"], [data-testid="stHeader"] { background-color: #0c0f16 !important; color: #f1f5f9 !important; font-family: 'Montserrat', sans-serif !important; }
    .stMarkdown, p, span, label, li { color: #cbd5e1 !important; }
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    h1 {font-weight: 800; color: #ffffff !important; font-size: 30px !important;}
    h2 {font-weight: 700; color: #f8fafc !important; font-size: 21px !important; margin-top: 15px;}
    h3 {font-weight: 600; color: #f1f5f9 !important; font-size: 16px !important;}
    div[data-testid="stRadio"] > label { display: none !important; }
    div[data-testid="stRadio"] > div { background: rgba(22, 27, 34, 0.7) !important; backdrop-filter: blur(12px) !important; padding: 8px !important; border-radius: 12px !important; border: 1px solid rgba(255, 255, 255, 0.08) !important; gap: 12px !important; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5) !important; margin-bottom: 20px !important; }
    div[data-testid="stRadio"] label[data-baseweb="radio"] { background-color: transparent !important; border: 1px solid transparent !important; padding: 8px 18px !important; border-radius: 8px !important; color: #94a3b8 !important; font-weight: 600 !important; }
    div[data-testid="stRadio"] label[data-baseweb="radio"]:hover { color: #ffffff !important; background: rgba(255, 255, 255, 0.05) !important; }
    div[data-testid="stMetric"] { background-color: #111520 !important; border: 1px solid #1f2937 !important; border-radius: 10px !important; padding: 15px 20px !important; }
    .stButton>button { width: 100%; background: linear-gradient(135deg, #2ecc71, #27ae60) !important; color: white !important; font-weight: 700; border-radius: 8px; border: none; padding: 0.6rem; font-size: 13px !important; text-transform: uppercase; }
    .stButton>button:hover { background: linear-gradient(135deg, #27ae60, #219653) !important; transform: translateY(-1px); }
    div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] div, div[data-testid="stNumberInput"] input { background-color: #111520 !important; color: #ffffff !important; border: 1px solid #1f2937 !important; border-radius: 8px !important; }
    .radar-box-gainer-high { background: linear-gradient(135deg, #064e3b, #047857); border: 1px solid #10b981; padding: 14px; border-radius: 8px; font-weight: bold; color: #34d399 !important; }
    .radar-box-loser { background: linear-gradient(135deg, #7f1d1d, #b91c1c); border: 1px solid #f87171; padding: 14px; border-radius: 8px; font-weight: bold; color: #f87171 !important; }
    .interpretation-box { background-color: #111520; padding: 16px; border-radius: 8px; font-size: 13px; color: #e2e8f0; border: 1px solid #1f2937; border-left: 4px solid #2ecc71; margin-top: 10px; }
    .agent-box { background-color: #090d16; padding: 18px; border-radius: 8px; font-size: 13px; color: #e2e8f0; border: 1px solid #1f2937; border-left: 4px solid #dfa427; margin-top: 10px; }
    .custom-table { width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 13px; background-color: #111520; border-radius: 8px; overflow: hidden; border: 1px solid #1f2937; }
    .custom-table th { background-color: #161b22; color: #ffffff; padding: 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #1f2937; position:relative; }
    .custom-table td { padding: 12px; border-bottom: 1px solid #1f2937; color: #e2e8f0; }
    .winner-cell { background-color: rgba(46, 204, 113, 0.15) !important; color: #2ecc71 !important; font-weight: bold; }
    .tooltip { position: relative; display: inline-block; cursor: pointer; color: #3498db; margin-left: 4px; font-weight: bold; }
    .tooltip .tooltiptext { visibility: hidden; width: 280px; background-color: #1f2937; color: #fff; text-align: left; padding: 12px; border-radius: 6px; position: absolute; z-index: 999; bottom: 125%; left: 50%; margin-left: -140px; font-size: 11px; font-weight: normal; line-height: 1.4; border: 1px solid #3b82f6; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }
    .tooltip:hover .tooltiptext { visibility: visible; opacity: 1; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. DOLAR MEP Y DATOS ESTRUCTURALES
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

RATIOS_CEDEAR = {
    "VIST": 1, "YPF": 1, "AAPL": 10, "GGAL": 1, "AMD": 10, "NVDA": 24, "MSFT": 30, "AMZN": 14, "GOOGL": 11, "META": 24, "TSLA": 15, "KO": 5, "WMT": 6, "JNJ": 15, "PEP": 15, "PG": 15, "XOM": 5, "PAMP": 1, "SPY": 20, "QQQ": 20, "DIA": 20, "MO": 4, "CVX": 8, "MCD": 24, "BRKB": 22, "MELI": 60, "BABA": 9, "PYPL": 3, "NFLX": 16, "DESP": 1, "VALE": 2
}
UNIVERSO_POOL = list(RATIOS_CEDEAR.keys())

# ==============================================================================
# 3. MOTOR YFINANCE
# ==============================================================================
@st.cache_data(ttl=600)
def descargar_datos_historicos(universo):
    datos_dict = {}
    try:
        df_hist = yf.download(universo, period="2y", progress=False, session=yf_session)
        if isinstance(df_hist.columns, pd.MultiIndex):
            df_close = df_hist['Close']
        else:
            df_close = df_hist['Close'] if 'Close' in df_hist.columns else df_hist
            
        df_close = df_close.ffill().bfill()
        fecha_ytd = f"{datetime.datetime.now().year}-01-02"
        
        for tk in universo:
            try:
                if tk in df_close.columns:
                    serie = df_close[tk].dropna()
                else:
                    serie = pd.Series(dtype=float)

                if not serie.empty and len(serie) >= 30:
                    px_actual = float(serie.iloc[-1])
                    v1d = ((px_actual / float(serie.iloc[-2])) - 1) * 100
                    v1w = ((px_actual / float(serie.iloc[-6])) - 1) * 100
                    v1m = ((px_actual / float(serie.iloc[-22])) - 1) * 100
                    try: v_ytd = ((px_actual / float(serie.loc[fecha_ytd:].iloc[0])) - 1) * 100 if not serie.loc[fecha_ytd:].empty else 0.0
                    except: v_ytd = 0.0
                    datos_dict[tk] = {"precio": px_actual, "1D": v1d, "1W": v1w, "1M": v1m, "YTD": v_ytd, "serie_completa": serie}
                else: datos_dict[tk] = {"precio": 100.0, "1D": 0.0, "1W": 0.0, "1M": 0.0, "YTD": 0.0, "serie_completa": pd.Series(dtype=float)}
            except: datos_dict[tk] = {"precio": 100.0, "1D": 0.0, "1W": 0.0, "1M": 0.0, "YTD": 0.0, "serie_completa": pd.Series(dtype=float)}
    except:
        for tk in universo: datos_dict[tk] = {"precio": 100.0, "1D": 0.0, "1W": 0.0, "1M": 0.0, "YTD": 0.0, "serie_completa": pd.Series(dtype=float)}
    return datos_dict

POOL_DATA = descargar_datos_historicos(UNIVERSO_POOL)

def safe_float(val, default=0.0):
    try: return float(val) if val is not None and not pd.isna(val) else default
    except: return default

def scrape_finviz_fallback(symbol):
    try:
        url = f"https://finviz.com/quote.ashx?t={symbol}"
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
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
        t = yf.Ticker(symbol, session=yf_session)
        inf = t.info or {}
        px = POOL_DATA.get(symbol, {}).get("precio", safe_float(inf.get("currentPrice", 50.0)))
        
        if not inf or safe_float(inf.get("forwardPE", 0.0)) == 0.0:
            fv_data = scrape_finviz_fallback(symbol)
            return {
                "Ticker": symbol, "Nombre": symbol, "Precio": px,
                "PE": fv_data.get("PE", 0.0), "EV": fv_data.get("EV", 0.0),
                "DEUDA": fv_data.get("DEUDA", 0.0), "LIQUIDEZ": fv_data.get("LIQUIDEZ", 0.0),
                "MARGEN": fv_data.get("MARGEN", 0.0), "ROE": fv_data.get("ROE", 0.0), "RAW": {}
            }
            
        eb = safe_float(inf.get("ebitda", 1.0))
        td = safe_float(inf.get("totalDebt", 0.0))
        caj = safe_float(inf.get("totalCash", 0.0))
        
        return {
            "Ticker": symbol, "Nombre": inf.get("longName", symbol), "Precio": px,
            "PE": safe_float(inf.get("forwardPE", 0.0)), "EV": safe_float(inf.get("enterpriseToEbitda", 0.0)),
            "DEUDA": (td - caj) / eb if eb != 0 else 0.0, "LIQUIDEZ": safe_float(inf.get("currentRatio", 0.0)),
            "MARGEN": safe_float(inf.get("profitMargins", 0.0)), "ROE": safe_float(inf.get("returnOnEquity", 0.0)),
            "RAW": inf
        }
    except:
        return {"Ticker": symbol, "Nombre": symbol, "Precio": POOL_DATA.get(symbol, {}).get("precio", 50.0), "PE": 0.0, "EV": 0.0, "DEUDA": 0.0, "LIQUIDEZ": 0.0, "MARGEN": 0.0, "ROE": 0.0, "RAW": {}}

def filtrar_peers_por_sector(ticker_raiz, lista_ingresada):
    try: sec_raiz = yf.Ticker(ticker_raiz, session=yf_session).info.get("sector", "")
    except: sec_raiz = ""
    peers_validos = []
    for p in lista_ingresada:
        p_clean = p.strip().upper()
        if not p_clean: continue
        try:
            sec_p = yf.Ticker(p_clean, session=yf_session).info.get("sector", "")
            if sec_p == sec_raiz or not sec_raiz: peers_validos.append(p_clean)
        except: peers_validos.append(p_clean)
    return peers_validos

# ==============================================================================
# 4. INTERFAZ Y DASHBOARD
# ==============================================================================
menu = st.radio("Secciones operativas:", ["🌐 DASHBOARD Y WATCHLIST", "🔍 ANÁLISIS INTEGRAL", "💼 PORTAFOLIO Y MODELOS"], horizontal=True)
st.markdown("---")

if menu == "🌐 DASHBOARD Y WATCHLIST":
    st.subheader("⚡ Market Radar: Momentum de Ruedas")
    ordenados = sorted(POOL_DATA.items(), key=lambda x: x[1]["1D"], reverse=True)
    c1, c2 = st.columns(2)
    
    with c1: 
        st.markdown(f"""
        <div class='radar-box-gainer-high'>
            🟢 Top 3 Ganadores (1D)<br><br>
            1. {ordenados[0][0]}: {ordenados[0][1]['1D']:+.2f}%<br>
            2. {ordenados[1][0]}: {ordenados[1][1]['1D']:+.2f}%<br>
            3. {ordenados[2][0]}: {ordenados[2][1]['1D']:+.2f}%
        </div>
        """, unsafe_allow_html=True)
        
    with c2: 
        st.markdown(f"""
        <div class='radar-box-loser'>
            🔴 Top 3 Perdedores (1D)<br><br>
            1. {ordenados[-1][0]}: {ordenados[-1][1]['1D']:+.2f}%<br>
            2. {ordenados[-2][0]}: {ordenados[-2][1]['1D']:+.2f}%<br>
            3. {ordenados[-3][0]}: {ordenados[-3][1]['1D']:+.2f}%
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("📌 Monitoreo General del Mercado (Watchlist)")
    rows_w = []
    for t in ["VIST", "YPF", "AAPL", "GGAL", "NVDA", "KO", "XOM", "WMT"]:
        p_info = POOL_DATA.get(t, {"precio": 100.0, "1D": 0.0, "1W": 0.0, "1M": 0.0, "YTD": 0.0})
        px_ars = (p_info["precio"] / RATIOS_CEDEAR.get(t, 1)) * DOLAR_MEP
        rows_w.append({"Ticker": t, "Precio USD": f"${p_info['precio']:.2f}", "Cedear Estimado (ARS)": f"${px_ars:,.2f}", "1D (%)": f"{p_info['1D']:+.2f}%", "1W (%)": f"{p_info['1W']:+.2f}%", "1M (%)": f"{p_info['1M']:+.2f}%", "YTD (%)": f"{p_info['YTD']:+.2f}%"})
    st.dataframe(pd.DataFrame(rows_w).set_index("Ticker"), use_container_width=True)

# ------------------------------------------------------------------------------
# ANÁLISIS INTEGRAL
# ------------------------------------------------------------------------------
elif menu == "🔍 ANÁLISIS INTEGRAL":
    c_s1, c_s2 = st.columns([1, 2])
    t_obj = c_s1.text_input("📍 Activo Bajo Estudio:", value="VIST").upper().strip()
    t_comp_raw = c_s2.text_input("Peers de Control (Separados por coma):", value="YPF, XOM").upper()
    
    if st.button("🔥 Correr Análisis"):
        with st.spinner("Descargando balances corporativos mediante yfinance..."):
            peers = [c.strip() for c in t_comp_raw.split(",") if c.strip()]
            lista_tickers = [t_obj] + filtrar_peers_por_sector(t_obj, peers)
            
            dataset = []
            info_raiz = {}
            for tk in lista_tickers:
                res_f = obtener_fundamental_completo(tk)
                if res_f:
                    dataset.append(res_f)
                    if tk == t_obj: info_raiz = res_f["RAW"]
            
            if dataset:
                tab_fund, tab_tech, tab_mc = st.tabs(["📊 Fundamental", "📈 Técnico (DMI)", "🎲 Montecarlo"])
                
                with tab_fund:
                    st.markdown("### 🏢 ¿A qué se dedica esta empresa?")
                    desc_raw = info_raiz.get("longBusinessSummary", "")
                    if not desc_raw:
                        desc_final = FALLBACK_SUMMARIES.get(t_obj, f"{t_obj} opera en el sector corporativo. (Yahoo Finance bloqueó la descripción extendida temporalmente).")
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
                        st.markdown("*Ingresos (ventas) vs Plata limpia (beneficio neto)*")
                        try:
                            q_fin = yf.Ticker(t_obj, session=yf_session).quarterly_financials
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
                                else: st.warning("Datos de ingresos no estandarizados.")
                            else: st.warning("Datos trimestrales bloqueados por Yahoo en la nube.")
                        except: st.warning("Estructura de balances no disponible temporalmente.")
                    
                    st.markdown("---")
                    st.markdown("#### Matriz de Comparación (Frente a sus competidores)")
                    g_pe = min(dataset, key=lambda x: x["PE"] if x["PE"] > 0 else float('inf'))["Ticker"]
                    g_roe = max(dataset, key=lambda x: x["ROE"])["Ticker"]
                    
                    html_matriz_final = "<table class='custom-table'><thead><tr>"
                    html_matriz_final += "<th>Ticker</th><th>Razón Social</th>"
                    html_matriz_final += f"<th>P/E <div class='tooltip'>ⓘ<span class='tooltiptext'>{EXPLICACIONES_TECNICAS['PE']}</span></div></th>"
                    html_matriz_final += f"<th>EV/EBITDA <div class='tooltip'>ⓘ<span class='tooltiptext'>{EXPLICACIONES_TECNICAS['EV']}</span></div></th>"
                    html_matriz_final += f"<th>Deuda <div class='tooltip'>ⓘ<span class='tooltiptext'>{EXPLICACIONES_TECNICAS['DEUDA']}</span></div></th>"
                    html_matriz_final += f"<th>Respaldo <div class='tooltip'>ⓘ<span class='tooltiptext'>{EXPLICACIONES_TECNICAS['LIQUIDEZ']}</span></div></th>"
                    html_matriz_final += f"<th>Margen <div class='tooltip'>ⓘ<span class='tooltiptext'>{EXPLICACIONES_TECNICAS['MARGEN']}</span></div></th>"
                    html_matriz_final += f"<th>ROE <div class='tooltip'>ⓘ<span class='tooltiptext'>{EXPLICACIONES_TECNICAS['ROE']}</span></div></th></tr></thead><tbody>"
                    
                    for r in dataset:
                        cls_pe = "class='winner-cell'" if r["Ticker"] == g_pe else ""
                        cls_roe = "class='winner-cell'" if r["Ticker"] == g_roe else ""
                        html_matriz_final += f"<tr><td><b>{r['Ticker']}</b></td><td>{r['Nombre']}</td><td {cls_pe}>{r['PE']:.2f}</td><td>{r['EV']:.2f}</td><td>{r['DEUDA']:.2f}x</td><td>{r['LIQUIDEZ']:.2f}x</td><td>{r['MARGEN']*100:.1f}%</td><td {cls_roe}>{r['ROE']*100:.1f}%</td></tr>"
                    html_matriz_final += "</tbody></table>"
                    st.markdown(html_matriz_final, unsafe_allow_html=True)
                    
                    st.markdown(f"<div class='interpretation-box'><b>Conclusión Sencilla:</b> Comparando con sus rivales, <strong>{g_roe}</strong> es la que mejor hace rendir la plata que tiene invertida. Por otro lado, si miramos qué tan barata está la acción hoy en relación a lo que gana, <strong>{g_pe}</strong> parece ser la mejor oferta en vitrina.</div>", unsafe_allow_html=True)

                with tab_tech:
                    st.markdown(f"### 📈 El pulso del mercado (Gráfico DMI): {t_obj}")
                    st.markdown("**¿Cómo leer este gráfico fácilmente?**<br>* **Línea Verde (+DI - Fuerza Compradora):** Mide la motivación de compra. Si supera a la roja, compradores al mando.<br>* **Línea Roja (-DI - Fuerza Vendedora):** Mide la presión de venta. Si supera a la verde, pánico o toma de ganancias.<br>* **Línea Azul (ADX - Fuerza de Tendencia):** Te dice si el movimiento va en serio. Sobre 25, tendencia sólida.", unsafe_allow_html=True)
                    
                    h_raw = yf.download(t_obj, period="1y", progress=False, session=yf_session)
                    if isinstance(h_raw.columns, pd.MultiIndex):
                        df_t = h_raw.xs(t_obj, axis=1, level=1) if t_obj in h_raw.columns.levels[1] else h_raw.iloc[:, :6]
                        df_t.columns = [c.lower() for c in df_t.columns]
                    else:
                        df_t = h_raw.copy()
                        df_t.columns = [c.lower() for c in df_t.columns]

                    if not df_t.empty and 'high' in df_t.columns:
                        df_t['EMA30'] = df_t['close'].ewm(span=30, adjust=False).mean()
                        up, down = df_t['high'].diff(), -df_t['low'].diff()
                        pdm, mdm = np.where((up > down) & (up > 0), up, 0.0), np.where((down > up) & (down > 0), down, 0.0)
                        tr = pd.DataFrame({'tr1': df_t['high']-df_t['low'], 'tr2': abs(df_t['high']-df_t['close'].shift(1)), 'tr3': abs(df_t['low']-df_t['close'].shift(1))}).max(axis=1)
                        trs = tr.rolling(14).sum()
                        df_t['+DI'] = 100 * (pd.Series(pdm, index=df_t.index).rolling(14).sum() / trs)
                        df_t['-DI'] = 100 * (pd.Series(mdm, index=df_t.index).rolling(14).sum() / trs)
                        df_t['ADX'] = (100 * abs(df_t['+DI'] - df_t['-DI']) / (df_t['+DI'] + df_t['-DI'])).rolling(14).mean()
                        df_t = df_t.dropna()
                        
                        fig_d = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.65, 0.35], vertical_spacing=0.04)
                        fig_d.add_trace(go.Scatter(x=df_t.index, y=df_t['close'], name="Precio", line=dict(color='#ffffff', width=2)), row=1, col=1)
                        fig_d.add_trace(go.Scatter(x=df_t.index, y=df_t['EMA30'], name="Promedio 30", line=dict(color='#f1c40f', dash='dash')), row=1, col=1)
                        fig_d.add_trace(go.Scatter(x=df_t.index, y=df_t['+DI'], name="+DI (Verde)", line=dict(color='#2ecc71', width=1.5)), row=2, col=1)
                        fig_d.add_trace(go.Scatter(x=df_t.index, y=df_t['-DI'], name="-DI (Rojo)", line=dict(color='#e74c3c', width=1.5)), row=2, col=1)
                        fig_d.add_trace(go.Scatter(x=df_t.index, y=df_t['ADX'], name="ADX (Azul)", line=dict(color='#3498db', width=2)), row=2, col=1)
                        fig_d.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', height=450, margin=dict(l=20,r=20,t=10,b=10))
                        st.plotly_chart(fig_d, use_container_width=True)
                        
                        p, di_p, di_m, adx = df_t['close'].iloc[-1], df_t['+DI'].iloc[-1], df_t['-DI'].iloc[-1], df_t['ADX'].iloc[-1]
                        dom = "los COMPRADORES" if di_p > di_m else "los VENDEDORES"
                        tend = "con muchísimo impulso." if adx > 25 else "pero el mercado está lateral y con dudas."
                        st.markdown(f"<div class='interpretation-box'><strong>¿QUIÉN TIENE EL VOLANTE HOY?</strong> Al precio actual de <b>${p:.2f}</b>, <b>{dom}</b> tienen el control, {tend}</div>", unsafe_allow_html=True)
                    else: st.error("No hay datos técnicos suficientes.")

                with tab_mc:
                    st.markdown("### 🎲 La Máquina del Tiempo (Simulador Estocástico)")
                    st.markdown("""<div class='agent-box'><strong>¿Qué tiene en cuenta este modelo matemático?</strong> Es un modelo puramente estadístico. Solo toma <b>la inercia</b> (el rendimiento promedio diario) y <b>el nerviosismo</b> (la volatilidad) que tuvo el activo durante el último año.<br><br><strong>¿Qué NO tiene en cuenta?</strong> Es "ciego" al mundo real. No evalúa balances de la empresa, la inflación, el tipo de cambio, el precio del barril de petróleo, ni las decisiones de la FED.<br><br><strong>¿Cómo saca los números finales?</strong> La computadora simula <b>10.000 caminos posibles</b> (tira los dados 10.000 veces) para proyectar el precio. <br>• <i>Escenario Base:</i> Es el promedio exacto de esas 10.000 simulaciones.<br>• <i>Escenario Optimista:</i> Es la zona donde caen el 5% de los mejores resultados (techo matemático de euforia).<br>• <i>Escenario Pesimista:</i> Es la zona del 5% de los peores resultados posibles (piso de pánico o soporte).</div>""", unsafe_allow_html=True)
                    
                    df_mc = POOL_DATA.get(t_obj, {}).get("serie_completa", pd.Series(dtype=float))
                    if not df_mc.empty and len(df_mc) > 50:
                        ret = df_mc.pct_change().dropna()
                        mu, sigma, p_b = ret.mean(), ret.std(), df_mc.iloc[-1]
                        c1, c2 = st.columns(2)
                        sims = 10000 
                        
                        with c1:
                            st.markdown("#### Corto Plazo: 30 días")
                            m_1m = np.zeros((30, sims))
                            m_1m[0] = p_b
                            Z_1m = np.random.standard_normal((29, sims))
                            for t in range(1, 30): m_1m[t] = m_1m[t-1] * np.exp((mu - 0.5 * sigma**2) + sigma * Z_1m[t-1])
                            f1m = go.Figure()
                            for i in range(50): f1m.add_trace(go.Scatter(y=m_1m[:, i], mode='lines', line=dict(color='rgba(52, 152, 219, 0.08)'), showlegend=False))
                            f1m.add_trace(go.Scatter(y=np.mean(m_1m, axis=1), mode='lines', name="Promedio", line=dict(color='#2ecc71', width=2.5)))
                            f1m.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', height=300, margin=dict(l=10,r=10,t=10,b=10))
                            st.plotly_chart(f1m, use_container_width=True)
                            pe, pdn, pup = np.mean(m_1m[-1, :]), np.percentile(m_1m[-1, :], 5), np.percentile(m_1m[-1, :], 95)
                            st.markdown(f"<div class='interpretation-box' style='border-left: 4px solid #2ecc71;'><b>Traducción Sencilla:</b> En un escenario normal (vanilla), el <b>Precio Justo a 30 días</b> promedia los <b>${pe:.2f} USD</b>. En caso de euforia estadística, el techo roza los <b>${pup:.2f} USD</b>. Frente al pánico, el piso es <b>${pdn:.2f} USD</b>.</div>", unsafe_allow_html=True)
                        
                        with c2:
                            st.markdown("#### Largo Plazo: 1 Año (252 días hábiles)")
                            m_1y = np.zeros((252, sims))
                            m_1y[0] = p_b
                            Z_1y = np.random.standard_normal((251, sims))
                            for t in range(1, 252): m_1y[t] = m_1y[t-1] * np.exp((mu - 0.5 * sigma**2) + sigma * Z_1y[t-1])
                            f1y = go.Figure()
                            for i in range(50): f1y.add_trace(go.Scatter(y=m_1y[:, i], mode='lines', line=dict(color='rgba(155, 89, 182, 0.08)'), showlegend=False))
                            f1y.add_trace(go.Scatter(y=np.mean(m_1y, axis=1), mode='lines', name="Promedio", line=dict(color='#9b59b6', width=2.5)))
                            f1y.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', height=300, margin=dict(l=10,r=10,t=10,b=10))
                            st.plotly_chart(f1y, use_container_width=True)
                            pe_y, pdn_y, pup_y = np.mean(m_1y[-1, :]), np.percentile(m_1y[-1, :], 5), np.percentile(m_1y[-1, :], 95)
                            st.markdown(f"<div class='interpretation-box' style='border-left: 4px solid #9b59b6;'><b>Traducción Sencilla:</b> A un año, el <b>Precio Justo Esperado</b> escala a <b>${pe_y:.2f} USD</b>. En un mercado ultra alcista tocaría los <b>${pup_y:.2f} USD</b>, y frente a una crisis el soporte frenaría en <b>${pdn_y:.2f} USD</b>.</div>", unsafe_allow_html=True)
                    else: st.error("No hay datos históricos suficientes para correr el modelo Montecarlo.")
            else: st.error("No se pudo obtener información fundamental de los activos. Intenta nuevamente.")

# ------------------------------------------------------------------------------
# PORTAFOLIO Y MODELOS FACTORIALES
# ------------------------------------------------------------------------------
elif menu == "💼 PORTAFOLIO Y MODELOS":
    st.subheader("🤖 Modelos Factoriales (Asignación Táctica)")
    FACTORES = {
        "Dividend Income": {"desc": "Empresas maduras con dividendos predecibles.", "activos": {"KO": "Resiliencia.", "XOM": "Energía.", "JNJ": "Salud.", "PEP": "Consumo.", "PG": "Higiene.", "WMT": "Retail."}},
        "Momentum Institucional": {"desc": "Inercia de compras y volumen a mediano plazo.", "activos": {"VIST": "Vaca Muerta.", "NVDA": "IA.", "MSFT": "SaaS.", "AAPL": "Hardware.", "AMD": "Procesadores.", "META": "Redes."}},
        "Large Caps Alpha": {"desc": "Núcleo de portafolio con corporaciones de escala global.", "activos": {"MSFT": "Monopolio moderno.", "AAPL": "Caja colosal.", "AMZN": "Líder cloud.", "GOOGL": "Foso de búsqueda.", "BRKB": "Value investing."}}
    }
    cat_sel = st.selectbox("Estrategia a Evaluar:", list(FACTORES.keys()))
    col1, col2 = st.columns([2, 1])
    tk_ele = col1.selectbox("Seleccionar activo sugerido:", list(FACTORES[cat_sel]["activos"].keys()))
    col1.markdown(f"💡 **Fundamento:** {FACTORES[cat_sel]['activos'][tk_ele]}")
    if col2.button("➕ ACOPLAR A MI CARTERA"):
        if not any(x["Ticker"] == tk_ele for x in st.session_state.cartera_list_v4):
            px_sub = POOL_DATA.get(tk_ele, {}).get("precio", 150.0)
            ratio = RATIOS_CEDEAR.get(tk_ele, 1)
            px_c = (px_sub / ratio) * DOLAR_MEP
            st.session_state.cartera_list_v4.append({"Ticker": tk_ele, "Nominales": 10, "Fecha_Compra": datetime.date(2025, 1, 2), "Costo_Unitario_Cedear": round(px_c, 2), "Comision_USD": 0.5, "Impuesto_USD": 0.05, "Dividendos_Edit": 0.0})
            st.success(f"Inyectado {tk_ele}.")
            st.rerun()

    st.markdown("---")
    st.subheader("💼 Mi Cartera de Inversiones Consolidada (BYMA)")
    is_ars = st.segmented_control("Moneda:", ["ARS", "USD"], default="ARS") == "ARS"
    with st.expander("➕ Cargar nueva posición"):
        with st.form("alta_manual"):
            cx1, cx2, cx3 = st.columns(3)
            i_tk, i_nom, i_dt = cx1.text_input("Ticker:", "AAPL").upper(), cx2.number_input("Cant:", min_value=1), cx3.date_input("Fecha:", datetime.date(2025,1,15))
            cx4, cx5, cx6 = st.columns(3)
            i_px, i_co, i_im = cx4.number_input("Precio ARS:", 25000.0), cx5.number_input("Com USD:", 0.5), cx6.number_input("Imp USD:", 0.1)
            if st.form_submit_button("➕ INTEGRAR"):
                st.session_state.cartera_list_v4.append({"Ticker": i_tk, "Nominales": i_nom, "Fecha_Compra": i_dt, "Costo_Unitario_Cedear": i_px, "Comision_USD": i_co, "Impuesto_USD": i_im, "Dividendos_Edit": 0.0})
                st.success("Cargada exitosamente.")
                st.rerun()

    df_in = pd.DataFrame(st.session_state.cartera_list_v4)
    if not df_in.empty:
        df_ed = st.data_editor(df_in, column_config={"Ticker": st.column_config.TextColumn(disabled=True), "Nominales": st.column_config.NumberColumn(disabled=True), "Fecha_Compra": st.column_config.DateColumn(disabled=True), "Costo_Unitario_Cedear": st.column_config.NumberColumn("Precio ARS", disabled=True), "Comision_USD": st.column_config.NumberColumn(disabled=True), "Impuesto_USD": st.column_config.NumberColumn(disabled=True), "Dividendos_Edit": st.column_config.NumberColumn("Divs (USD)", disabled=False)}, use_container_width=True, hide_index=True)
        st.session_state.cartera_list_v4 = df_ed.to_dict(orient="records")
        f_html, f_pdf = [], []
        c_tot, m_tot, d_tot = 0.0, 0.0, 0.0
        for p in st.session_state.cartera_list_v4:
            t, n, px_c, co, im, dv = p["Ticker"], p["Nominales"], p["Costo_Unitario_Cedear"], p["Comision_USD"], p["Impuesto_USD"], p["Dividendos_Edit"]
            ratio = RATIOS_CEDEAR.get(t, 1)
            px_s = POOL_DATA.get(t, {"precio": (px_c * ratio) / DOLAR_MEP})["precio"]
            c_usd, v_usd = ((n * px_c) / DOLAR_MEP) * ratio + co + im, n * px_s
            pl_usd = (v_usd + dv) - c_usd
            pct = (pl_usd / c_usd) * 100 if c_usd > 0 else 0.0
            c_tot += c_usd; m_tot += v_usd; d_tot += dv
            if is_ars:
                c_f, v_f, pl_f = c_usd*DOLAR_MEP/ratio, v_usd*DOLAR_MEP/ratio, pl_usd*DOLAR_MEP/ratio
                lbl, px_v = "ARS", px_c
            else:
                c_f, v_f, pl_f = c_usd, v_usd, pl_usd
                lbl, px_v = "USD", px_s
            f_html.append({"Ticker": t, "Cant": n, "Ratio": f"{ratio}:1", f"Precio": f"${px_v:,.2f}", f"Capital": f"${c_f:,.2f}", f"Mercado": f"${v_f:,.2f}", f"P&L": f"${pl_f:,.2f}", "Retorno": f"{pct:+.2f}%"})
            f_pdf.append({"Ticker": t, "Cant": n, "Precio": f"${px_v:,.2f}", "Mercado": f"${v_f:,.2f}", "Retorno": f"{pct:+.2f}%"})
        st.dataframe(pd.DataFrame(f_html).set_index("Ticker"), use_container_width=True)
        
        st.markdown("### 📈 Estado Neto Patrimonial")
        k1, k2, k3, k4 = st.columns(4)
        gp = ((m_tot + d_tot - c_tot) / c_tot) * 100 if c_tot > 0 else 0.0
        fac = DOLAR_MEP if is_ars else 1
        mon = "ARS" if is_ars else "USD"
        k1.metric("Capital Invertido", f"${(c_tot*fac):,.2f} {mon}")
        k2.metric("Valuación Mercado", f"${(m_tot*fac):,.2f} {mon}")
        k3.metric("Bolsa Rentas", f"${(d_tot*fac):,.2f} {mon}")
        k4.metric("Total Return", f"${((m_tot+d_tot-c_tot)*fac):,.2f} {mon} ({gp:+.2f}%)")

        st.markdown("---")
        st.subheader("📐 Benchmarking Institucional")
        bench = st.selectbox("Benchmark:", ["SPY", "QQQ", "DIA"])
        fechas = pd.date_range(start="2025-06-01", end=datetime.date.today(), freq="B")
        c_p = pd.Series(0.0, index=fechas)
        for pos in st.session_state.cartera_list_v4:
            s_tk = POOL_DATA.get(pos["Ticker"], {}).get("serie_completa", pd.Series(dtype=float))
            if not s_tk.empty: c_p = c_p.add(s_tk.reindex(fechas).ffill().bfill(), fill_value=0)
        c_p = c_p.dropna()
        if not c_p.empty:
            c_p = (c_p / c_p.iloc[0]) * 100
            s_b = POOL_DATA.get(bench, {}).get("serie_completa", pd.Series(dtype=float))
            c_b = (s_b.reindex(c_p.index).ffill().bfill() / s_b.reindex(c_p.index).ffill().bfill().iloc[0]) * 100 if not s_b.empty else c_p * 0.94
            fig_b = go.Figure(data=[go.Scatter(x=c_p.index, y=c_p.values, name="Mi Cuenta", line=dict(color='#2ecc71', width=3)), go.Scatter(x=c_b.index, y=c_b.values, name=f"Benchmark {bench}", line=dict(color='#3498db', width=2, dash='dash'))])
            fig_b.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', height=380, margin=dict(l=20,r=20,t=30,b=20))
            st.plotly_chart(fig_b, use_container_width=True)

        st.markdown("---")
        st.subheader("📥 Exportación Institucional")
        asesor = st.text_input("Asesor Firmante:", value="Facundo Garcia Marquez")
        h_rep = "".join([f"<tr><td>{x['Ticker']}</td><td>{x['Cant']}</td><td>{x['Precio']}</td><td>{x['Mercado']}</td><td>{x['Retorno']}</td></tr>" for x in f_pdf])
        doc = f"<html><head><meta charset='utf-8'><style>body{{font-family:Arial; color:#2c3e50;}} h1{{color:#2ecc71;}} table{{width:100%; border-collapse:collapse; font-size:12px;}} th,td{{padding:8px; border:1px solid #ddd; text-align:left;}}</style></head><body><h1>Reporte de Portafolio</h1><p><b>Asesor:</b> {asesor}</p><p><b>Retorno:</b> {gp:+.2f}%</p><table><thead><tr><th>Ticker</th><th>Cant</th><th>Precio</th><th>Mercado</th><th>Retorno</th></tr></thead><tbody>{h_rep}</tbody></table></body></html>"
        st.download_button("📥 DESCARGAR REPORTE", data=doc.encode('utf-8'), file_name=f"Reporte_{asesor.replace(' ','_')}.html", mime="text/html")

st.markdown("---")
st.markdown("<p style='text-align: right; font-size: 12px; color: #cbd5e1;'>Desarrollado por <a href='https://www.linkedin.com/in/facundo-garciamarquez?utm_source=share_via&utm_content=profile&utm_medium=member_android' target='_blank' style='color: #2ecc71; text-decoration: none; font-weight: 600;'>Facundo Garcia Marquez</a> | Terminal Quanti Pro</p>", unsafe_allow_html=True)
st.markdown("""<div style='background-color: rgba(231, 76, 60, 0.08); padding: 12px; border-left: 4px solid #e74c3c; font-size: 11px; color: #94a3b8;'><strong>⚠️ ADVERTENCIA EXCLUSIÓN DE RESPONSABILIDAD:</strong> Las cotizaciones de mercado y el análisis automatizado se exponen únicamente con fines educativos y de simulación de portafolios. No constituyen bajo ningún concepto asesoramiento financiero ni una recomendación explícita de compra o venta de activos o instrumentos de inversión corporativos.</div>""", unsafe_allow_html=True)
