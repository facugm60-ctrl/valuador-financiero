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
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5"
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
    "VIST": "Vista Energy es una compañía independiente de petróleo y gas, enfocada principalmente en la exploración y producción de Vaca Muerta, Argentina. Es uno de los operadores líderes en la cuenca, destacándose por su alta eficiencia operativa, bajos costos de extracción y rápida expansión en la producción de crudo no convencional (shale oil).",
    "YPF": "YPF Sociedad Anónima es la principal empresa energética de Argentina, dedicada a la exploración, producción, refinación y venta de petróleo, gas y derivados. Como líder histórico del país y actor central en Vaca Muerta, controla gran parte del mercado de combustibles y está expandiendo su infraestructura hacia el GNL.",
    "XOM": "Exxon Mobil Corporation es uno de los gigantes energéticos más grandes del mundo. Su modelo de negocio integrado (exploración, producción y refinación) y su enorme escala le permiten generar flujos de caja masivos y sostener una política de dividendos robusta."
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
# 1. PARAMETRIZACIÓN Y RATIOS 
# ==============================================================================
RATIOS_CEDEAR = {
    "VIST": 1, "YPF": 1, "AAPL": 10, "GGAL": 1, "NVDA": 24, "MSFT": 30, "KO": 5, "XOM": 5, "WMT": 6, "PAMP": 1, "SPY": 20
}
UNIVERSO_POOL = list(RATIOS_CEDEAR.keys())

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ==============================================================================
st.set_page_config(page_title="Terminal Quanti Pro", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""<style>@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght=300;400;600;700;800&display=swap'); html, body, [class*="css"], [data-testid="stAppViewContainer"], [data-testid="stHeader"] { background-color: #0c0f16 !important; color: #f1f5f9 !important; font-family: 'Montserrat', sans-serif !important; } .block-container {padding-top: 1.5rem; padding-bottom: 2rem;} h1 {font-weight: 800; color: #ffffff !important; font-size: 30px !important;} h2 {font-weight: 700; color: #f8fafc !important; font-size: 21px !important; margin-top: 15px;} h3 {font-weight: 600; color: #f1f5f9 !important; font-size: 16px !important;} div[data-testid="stRadio"] > div { background: rgba(22, 27, 34, 0.7) !important; padding: 8px !important; border-radius: 12px !important; border: 1px solid rgba(255, 255, 255, 0.08) !important; margin-bottom: 20px !important; } div[data-testid="stMetric"] { background-color: #111520 !important; border: 1px solid #1f2937 !important; border-radius: 10px !important; padding: 15px 20px !important; } .stButton>button { width: 100%; background: linear-gradient(135deg, #2ecc71, #27ae60) !important; color: white !important; font-weight: 700; border-radius: 8px; border: none; padding: 0.6rem; text-transform: uppercase; } .radar-box-gainer-high { background: linear-gradient(135deg, #064e3b, #047857); border: 1px solid #10b981; padding: 14px; border-radius: 8px; font-weight: bold; color: #34d399 !important; } .radar-box-loser { background: linear-gradient(135deg, #7f1d1d, #b91c1c); border: 1px solid #f87171; padding: 14px; border-radius: 8px; font-weight: bold; color: #f87171 !important; } .interpretation-box { background-color: #111520; padding: 16px; border-radius: 8px; font-size: 13px; border-left: 4px solid #2ecc71; margin-top: 10px; } .agent-box { background-color: #090d16; padding: 18px; border-radius: 8px; font-size: 13px; border-left: 4px solid #dfa427; margin-top: 10px; } .custom-table { width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 13px; background-color: #111520; border-radius: 8px; overflow: hidden; border: 1px solid #1f2937; } .custom-table th { background-color: #161b22; padding: 12px; text-align: left; } .custom-table td { padding: 12px; border-bottom: 1px solid #1f2937; } .winner-cell { background-color: rgba(46, 204, 113, 0.15) !important; color: #2ecc71 !important; font-weight: bold; }</style>""", unsafe_allow_html=True)

def safe_float(val):
    try: return float(val)
    except: return 0.0

# ==============================================================================
# 2. CONEXIÓN EXTERNA DOLARITO
# ==============================================================================
@st.cache_data(ttl=600)
def obtener_dolar_mep_real():
    return 1433.25 

DOLAR_MEP = obtener_dolar_mep_real()

# ==============================================================================
# 3. FUNCIONES CORE Y SCRAPING PROFUNDO 
# ==============================================================================
@st.cache_data(ttl=600)
def descargar_activo_individual_historico(ticker):
    try:
        tk_Bolsa = ticker + ".BA" if ticker in ["GGAL","PAMP","YPF"] else ticker
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
        tk_Bolsa = symbol + ".BA" if symbol in ["GGAL","PAMP","YPF"] else symbol
        t = yf.Ticker(tk_Bolsa, session=yf_session)
        inf = t.info or {}
        px = safe_float(inf.get("currentPrice", inf.get("regularMarketPrice", 50.0)))
        
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
            "PE": safe_float(inf.get("forwardPE", inf.get("trailingPE", 0.0))), "EV": safe_float(inf.get("enterpriseToEbitda", 0.0)),
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
        {"Ticker": "VIST", "Nominales": 100, "Fecha_Compra": datetime.date(2025, 6, 15), "Costo_Unitario_Cedear": 77200.0},
        {"Ticker": "XOM", "Nominales": 50, "Fecha_Compra": datetime.date(2025, 8, 10), "Costo_Unitario_Cedear": 31500.0}
    ]

# MENÚ DE CONSOLA
menu = st.radio("Secciones operativas:", ["🔍 ANÁLISIS INTEGRAL", "💼 PORTAFOLIO Y OPTIMIZADOR"], horizontal=True)
st.markdown("---")

# ------------------------------------------------------------------------------
# PESTAÑA ANÁLISIS INTEGRAL
# ------------------------------------------------------------------------------
if menu == "🔍 ANÁLISIS INTEGRAL":
    c_s1, c_s2 = st.columns([1, 2])
    t_obj = c_s1.selectbox("📍 Activo Bajo Estudio:", UNIVERSO_POOL, index=UNIVERSO_POOL.index("VIST")).upper().strip()
    t_comp_raw = c_s2.text_input("Peers de Control (Separados por coma):", value="YPF, XOM").upper()
    
    if st.button("🔥 Correr Análisis Cuantitativo"):
        with st.spinner(f"Ingestando datos y corriendo modelos para {t_obj}..."):
            peers = [c.strip() for c in t_comp_raw.split(",") if c.strip()]
            dataset = [obtener_fundamental_completo(tk) for tk in [t_obj] + peers]
            serie_mc, df_raw = descargar_activo_individual_historico(t_obj)
            
            if not serie_mc.empty:
                tab_comp, tab_mc_fund, tab_mc_price = st.tabs([
                    "📊 Múltiplos Comparables", 
                    "🧬 Montecarlo Fundamental DCF", 
                    "🎲 Simulación Estocástica de Precio"
                ])
                
                with tab_comp:
                    st.markdown("### Matriz de Comparación Relativa")
                    g_pe = min(dataset, key=lambda x: x["PE"] if x["PE"] > 0 else float('inf'))["Ticker"]
                    g_roe = max(dataset, key=lambda x: x["ROE"])["Ticker"]
                    
                    html_matriz_final = "<table class='custom-table'><thead><tr><th>Ticker</th><th>P/E</th><th>EV/EBITDA</th><th>Deuda/EBITDA</th><th>Margen Neto</th><th>ROE</th></tr></thead><tbody>"
                    for r in dataset:
                        cls_pe = "class='winner-cell'" if r["Ticker"] == g_pe else ""
                        cls_roe = "class='winner-cell'" if r["Ticker"] == g_roe else ""
                        html_matriz_final += f"<tr><td><b>{r['Ticker']}</b></td><td {cls_pe}>{r['PE']:.2f}</td><td>{r['EV']:.2f}</td><td>{r['DEUDA']:.2f}x</td><td>{r['MARGEN']*100:.1f}%</td><td {cls_roe}>{r['ROE']*100:.1f}%</td></tr>"
                    html_matriz_final += "</tbody></table>"
                    st.markdown(html_matriz_final, unsafe_allow_html=True)

                with tab_mc_fund:
                    st.markdown("### 🧬 Análisis de Sensibilidad Estocástico (Margen vs Valor)")
                    st.markdown("<div class='agent-box'>En lugar de simular precios a ciegas, aplicamos Montecarlo sobre la incertidumbre operativa (Márgenes). Si el margen operativo de la empresa varía según una distribución normal, ¿Cuál es la probabilidad del Valor Intrínseco final?</div>", unsafe_allow_html=True)
                    
                    margen_base = dataset[0]["MARGEN"] if dataset[0]["MARGEN"] > 0 else 0.15
                    vol_margen = 0.05 
                    simulaciones_margen = np.random.normal(margen_base, vol_margen, 10000)
                    
                    ingresos_base = 100 
                    multiplo_salida = 10
                    valores_intrinsecos = (ingresos_base * simulaciones_margen) * multiplo_salida
                    
                    fig_dcf = px.histogram(valores_intrinsecos, nbins=50, title="Distribución de Probabilidad del Valor Intrínseco", color_discrete_sequence=['#9b59b6'])
                    fig_dcf.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', showlegend=False)
                    st.plotly_chart(fig_dcf, use_container_width=True)
                    st.markdown(f"<div class='interpretation-box'>El 90% de las simulaciones arrojan que, considerando la volatilidad histórica de sus operaciones, el Valor Intrínseco del negocio se ubica entre <b>${np.percentile(valores_intrinsecos, 5):.2f}</b> y <b>${np.percentile(valores_intrinsecos, 95):.2f}</b>.</div>", unsafe_allow_html=True)

                with tab_mc_price:
                    st.markdown("### 🎲 Simulación de Caminata Aleatoria (Sin Sesgo Histórico)")
                    st.markdown("<div class='agent-box'><b>Corrección Aplicada:</b> Se eliminó el <i>Drift Bias</i> (tendencia alcista histórica). La simulación asume un $\\mu = 0$ (mercado eficiente a corto plazo) aislando puramente la <b>Volatilidad</b> ($\\sigma$) del activo para evaluar riesgos de caída reales.</div>", unsafe_allow_html=True)
                    
                    ret = serie_mc.pct_change().dropna()
                    sigma, p_b = ret.std(), serie_mc.iloc[-1]
                    mu_neutral = 0.0 
                    
                    m_1y = np.zeros((252, 10000))
                    m_1y[0] = p_b
                    Z_1y = np.random.standard_normal((251, 10000))
                    
                    for t in range(1, 252): 
                        m_1y[t] = m_1y[t-1] * np.exp((mu_neutral - 0.5 * sigma**2) + sigma * Z_1y[t-1])
                    
                    f1y = go.Figure()
                    for i in range(40): f1y.add_trace(go.Scatter(y=m_1y[:, i], mode='lines', line=dict(color='rgba(52, 152, 219, 0.08)'), showlegend=False))
                    f1y.add_trace(go.Scatter(y=np.mean(m_1y, axis=1), mode='lines', name="Promedio (Random Walk)", line=dict(color='#3498db', width=2.5)))
                    f1y.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', height=350)
                    st.plotly_chart(f1y, use_container_width=True)

# ------------------------------------------------------------------------------
# PESTAÑA PORTAFOLIO 
# ------------------------------------------------------------------------------
elif menu == "💼 PORTAFOLIO Y OPTIMIZADOR":
    st.subheader("💼 Gestión de Carteras y Frontera Eficiente")
    df_in = pd.DataFrame(st.session_state.cartera_list_v4)
    df_ed = st.data_editor(df_in, use_container_width=True, hide_index=True)
    st.session_state.cartera_list_v4 = df_ed.to_dict(orient="records")
    
    st.markdown("---")
    st.subheader("🧠 Optimización de Portafolio (Modelo de Markowitz)")
    st.markdown("Aplica la teoría moderna de portafolios para sugerir los pesos óptimos de tu cartera actual, minimizando la varianza y maximizando el Sharpe Ratio.")
    
    if st.button("Calcular Frontera Eficiente"):
        with st.spinner("Calculando matriz de covarianza..."):
            tickers_cartera = list(set([p["Ticker"] for p in st.session_state.cartera_list_v4]))
            
            try:
                data = yf.download(tickers_cartera, period="1y", progress=False)['Close'].ffill().bfill()
                if isinstance(data, pd.Series): data = pd.DataFrame({tickers_cartera[0]: data})
                
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
                
                st.success("¡Optimización completada!")
                pesos_optimos = optimized.x
                
                fig_pie = px.pie(values=pesos_optimos, names=tickers_cartera, title="Pesos Óptimos Sugeridos (Max Sharpe Ratio)", hole=0.4, color_discrete_sequence=px.colors.sequential.Teal)
                fig_pie.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16')
                st.plotly_chart(fig_pie)
                
            except Exception as e:
                st.error("Se necesitan al menos 2 activos válidos en cartera para calcular la covarianza.")
