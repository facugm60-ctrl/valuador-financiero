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
# INTEGRACIÓN GOOGLE GEMINI AI
# ------------------------------------------------------------------------------
try:
    import google.generativeai as genai
    HAS_GEMINI_LIB = True
except ImportError:
    HAS_GEMINI_LIB = False

GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", None) if hasattr(st, "secrets") else None
if HAS_GEMINI_LIB and GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

def generar_descripcion_empresa_gemini(ticker, nombre, info_dict):
    """Genera resumen ejecutivo de negocio, guidance y solvencia (máx 5 renglones)."""
    if not (HAS_GEMINI_LIB and GEMINI_KEY):
        return f"**{nombre} ({ticker}):** Compañía líder en su sector. Opera con un ratio Deuda Neta/EBITDA de {info_dict.get('deuda', 0):.2f}x y margen neto de {info_dict.get('margen', 0)*100:.1f}%. Metas orientadas a expansión operativa y disciplina de capital según consensos del mercado."
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""
        Actúa como un Senior Research Analyst de Wall Street.
        Redacta una síntesis ejecutiva y rigurosa para {nombre} ({ticker}) con un MÁXIMO ESTRICTO de 5 renglones en total:
        - Renglones 1-2: Core business y ventajas competitivas del modelo de negocio.
        - Renglones 3-4: Guidance corporativo reciente (proyectos estratégicos, metas de crecimiento o CapEx).
        - Renglón 5: Situación de solvencia y cobertura (Deuda Neta/EBITDA: {info_dict.get('deuda', 0):.2f}x, Margen Neto: {info_dict.get('margen', 0)*100:.1f}%, ROE: {info_dict.get('roe', 0)*100:.1f}%).
        Sé directo, profesional e institucional. No uses introducciones vacías.
        """
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error al generar síntesis con IA: {e}"

def generar_tesis_gemini(ticker, nombre, precio, pe, roe, deuda, margen, dcf_valor):
    if not (HAS_GEMINI_LIB and GEMINI_KEY):
        return "⚠️ Clave `GEMINI_API_KEY` no configurada en los Secrets de Streamlit o librería no instalada."
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        upside = ((dcf_valor - precio) / precio) * 100 if precio > 0 else 0
        prompt = f"""
        Actúa como Portfolio Manager Senior de Equity Research.
        Elabora una tesis de inversión ejecutiva, técnica y concisa para {nombre} ({ticker}):
        - Precio actual: ${precio:.2f} USD | DCF Estocástico: ${dcf_valor:.2f} USD (Upside/Downside: {upside:+.1f}%)
        - P/E: {pe:.2f}x | ROE: {roe*100:.1f}% | Margen Neto: {margen*100:.1f}% | Deuda Neta/EBITDA: {deuda:.2f}x

        Estructura tu respuesta exactamente en tres secciones:
        1. 🏛️ Calidad del Negocio y Solvencia: Evaluación de retorno sobre capital y sostenibilidad de la estructura de deuda.
        2. ⚖️ Valuación Intrínseca vs. Mercado: Diagnóstico sobre si el precio actual ofrece margen de seguridad frente al DCF.
        3. 🎯 Veredicto Fundamental: Calificación taxativa (Compra / Mantener / Venta) con su principal catalizador y riesgo clave.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error al generar la tesis con Gemini: {e}"

# ------------------------------------------------------------------------------
# CONEXIÓN Y DATOS
# ------------------------------------------------------------------------------
yf_session = requests.Session()
yf_session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
})

WATCHLIST_CORE = ["VIST", "YPF", "AAPL", "GGAL", "NVDA", "KO", "XOM", "WMT"]

RATIOS_CEDEAR = {
    "VIST": 1, "YPF": 1, "AAPL": 10, "GGAL": 1, "AMD": 10, "NVDA": 24, "MSFT": 30, "AMZN": 14, "GOOGL": 11, "META": 24, 
    "TSLA": 15, "KO": 5, "WMT": 6, "JNJ": 15, "PEP": 15, "PG": 15, "XOM": 5, "PAMP": 1, "SPY": 20, "QQQ": 20
}
UNIVERSO_POOL = list(RATIOS_CEDEAR.keys())

st.set_page_config(page_title="Terminal Quanti Pro", layout="wide", initial_sidebar_state="collapsed")

# CSS Institucional optimizado
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&display=swap');
html, body, [class*="css"], [data-testid="stAppViewContainer"], [data-testid="stHeader"] { background-color: #0c0f16 !important; color: #f1f5f9 !important; font-family: 'Montserrat', sans-serif !important; }
.block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
h1 {font-weight: 800; color: #ffffff !important; font-size: 28px !important;}
h2 {font-weight: 700; color: #f8fafc !important; font-size: 20px !important;}
h3 {font-weight: 600; color: #f1f5f9 !important; font-size: 16px !important;}

/* Fix Radio superior */
div[data-testid="stRadio"] > div { 
    background: rgba(22, 27, 34, 0.8) !important; 
    padding: 6px 12px !important; 
    border-radius: 10px !important; 
    border: 1px solid rgba(255, 255, 255, 0.1) !important; 
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 8px !important; 
    margin-bottom: 15px !important; 
}
div[data-testid="stRadio"] label[data-baseweb="radio"] { 
    padding: 6px 16px !important; 
    border-radius: 6px !important; 
    color: #cbd5e1 !important; 
    font-weight: 600 !important; 
    font-size: 13px !important;
}

/* Fix métricas para evitar números cortados */
div[data-testid="stMetricValue"] > div {
    font-size: 19px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
div[data-testid="stMetricLabel"] > div {
    font-size: 12px !important;
    color: #94a3b8 !important;
}
div[data-testid="stMetric"] { background-color: #111520 !important; border: 1px solid #1f2937 !important; border-radius: 8px !important; padding: 10px 14px !important; }

.stButton>button { width: 100%; background: linear-gradient(135deg, #10b981, #059669) !important; color: white !important; font-weight: 700; border-radius: 8px; border: none; padding: 0.6rem; font-size: 13px !important; }
.radar-box-gainer { background: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; padding: 12px; border-radius: 8px; color: #34d399 !important; font-size: 13px; }
.radar-box-loser { background: rgba(239, 68, 68, 0.1); border: 1px solid #ef4444; padding: 12px; border-radius: 8px; color: #f87171 !important; font-size: 13px; }
.interpretation-box { background-color: #111520; padding: 14px; border-radius: 8px; font-size: 13px; color: #e2e8f0; border-left: 4px solid #10b981; margin: 10px 0; border-top: 1px solid #1f2937; border-right: 1px solid #1f2937; border-bottom: 1px solid #1f2937;}
.gemini-box { background-color: #0b1329; padding: 16px; border-radius: 8px; font-size: 13px; color: #f1f5f9; border: 1px solid #3b82f6; border-left: 4px solid #60a5fa; margin-top: 12px; line-height: 1.6; }

/* Tablas estilizadas */
.custom-table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 12px; background-color: #111520; border-radius: 6px; border: 1px solid #1f2937; }
.custom-table th { background-color: #161b22; color: #f8fafc; padding: 10px; text-align: left; font-weight: 600; border-bottom: 2px solid #1f2937; }
.custom-table td { padding: 10px; border-bottom: 1px solid #1f2937; color: #e2e8f0; }
.winner-cell { background-color: rgba(16, 185, 129, 0.15) !important; color: #34d399 !important; font-weight: 700; }
</style>""", unsafe_allow_html=True)

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
                            if 1000 < val < 2500: return round(val, 2)
                        except: pass
        return 1420.0
    except: return 1420.0

DOLAR_MEP = obtener_dolar_mep_real()

@st.cache_data(ttl=900)
def descargar_datos_mercado(tickers):
    """Descarga serie de 1 año y calcula retornos periódicos reales (1D, 1M, 6M, 1Y, YTD)."""
    try:
        data = yf.download(tickers, period="1y", progress=False, session=yf_session)
        if isinstance(data.columns, pd.MultiIndex):
            close = data['Close'].ffill().bfill()
        else:
            close = data['Close'].to_frame() if 'Close' in data.columns else data.ffill().bfill()
        
        resultados = {}
        fecha_inicio_año = datetime.date(datetime.date.today().year, 1, 1)
        
        for tk in tickers:
            serie = close[tk].dropna() if tk in close.columns else pd.Series(dtype=float)
            if len(serie) >= 2:
                p_act = float(serie.iloc[-1])
                ret_1d = ((p_act / float(serie.iloc[-2])) - 1) * 100
                ret_1m = ((p_act / float(serie.iloc[-21])) - 1) * 100 if len(serie) >= 21 else ret_1d
                ret_6m = ((p_act / float(serie.iloc[-126])) - 1) * 100 if len(serie) >= 126 else ret_1m
                ret_1y = ((p_act / float(serie.iloc[0])) - 1) * 100
                
                serie_ytd = serie[serie.index.date >= fecha_inicio_año]
                ret_ytd = ((p_act / float(serie_ytd.iloc[0])) - 1) * 100 if len(serie_ytd) > 0 else ret_1d
                
                resultados[tk] = {
                    "precio": p_act, "1D": ret_1d, "1M": ret_1m, "6M": ret_6m, "1Y": ret_1y, "YTD": ret_ytd
                }
        return resultados, close
    except:
        return {}, pd.DataFrame()

DATOS_RADAR, DF_CLOSE_GLOBAL = descargar_datos_mercado(UNIVERSO_POOL)

@st.cache_data(ttl=600)
def descargar_activo_individual_historico(ticker):
    try:
        tk_bolsa = ticker + ".BA" if ticker in ["GGAL", "PAMP", "YPF", "TXAR", "ALUA", "BMA", "CEPU"] else ticker
        df = yf.download(tk_bolsa, period="2y", progress=False, session=yf_session)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.loc[:, ~df.columns.duplicated()]
        df_close = df['Close'].ffill().bfill()
        if isinstance(df_close, pd.DataFrame):
            df_close = df_close.iloc[:, 0]
        return df_close.dropna(), df
    except:
        return pd.Series(dtype=float), pd.DataFrame()

def obtener_fundamental_completo(symbol):
    try:
        t = yf.Ticker(symbol, session=yf_session)
        inf = t.info or {}
        px = safe_float(inf.get("currentPrice", inf.get("regularMarketPrice", 50.0)))
        if symbol in DATOS_RADAR:
            px = DATOS_RADAR[symbol]["precio"]
            
        pe = safe_float(inf.get("trailingPE", inf.get("forwardPE", 0.0)))
        eb = safe_float(inf.get("ebitda", 1.0))
        td = safe_float(inf.get("totalDebt", 0.0))
        caj = safe_float(inf.get("totalCash", 0.0))
        deuda_ebitda = (td - caj) / eb if eb > 0 else 0.0
        
        return {
            "Ticker": symbol, "Nombre": inf.get("longName", symbol), "Precio": px,
            "PE": pe, "EV": safe_float(inf.get("enterpriseToEbitda", 0.0)),
            "DEUDA": deuda_ebitda, "LIQUIDEZ": safe_float(inf.get("currentRatio", 0.0)),
            "MARGEN": safe_float(inf.get("profitMargins", 0.0)), "ROE": safe_float(inf.get("returnOnEquity", 0.0)),
            "RAW": inf
        }
    except:
        return {"Ticker": symbol, "Nombre": symbol, "Precio": 50.0, "PE": 0.0, "EV": 0.0, "DEUDA": 0.0, "LIQUIDEZ": 0.0, "MARGEN": 0.0, "ROE": 0.0, "RAW": {}}

# Session state para portafolio y persistencia de análisis
if "cartera" not in st.session_state:
    st.session_state.cartera = [
        {"Ticker": "VIST", "Nominales": 100, "Costo_Unitario_Cedear": 77200.0, "Comision_USD": 0.5, "Dividendos_USD": 15.0},
        {"Ticker": "XOM", "Nominales": 50, "Costo_Unitario_Cedear": 31500.0, "Comision_USD": 0.4, "Dividendos_USD": 25.5}
    ]

if "activo_analizado" not in st.session_state:
    st.session_state.activo_analizado = "VIST"
if "peers_analizados" not in st.session_state:
    st.session_state.peers_analizados = "YPF, XOM"

menu = st.radio("Secciones operativas:", ["🌐 DASHBOARD Y WATCHLIST", "🔍 ANÁLISIS INTEGRAL", "💼 PORTAFOLIO Y MODELOS"], horizontal=True)
st.markdown("---")

# ==============================================================================
# 1. DASHBOARD Y WATCHLIST
# ==============================================================================
if menu == "🌐 DASHBOARD Y WATCHLIST":
    st.subheader("⚡ Market Radar: Momentum y Retornos Periódicos")
    
    if not DATOS_RADAR:
        st.warning("Sincronizando feed de mercado... Por favor recargar si persiste.")
    else:
        ordenados = sorted(DATOS_RADAR.items(), key=lambda x: x[1]["1D"], reverse=True)
        g1, g2 = st.columns(2)
        with g1:
            st.markdown(f"<div class='radar-box-gainer'>🟢 <b>Líderes de la Rueda (1D)</b><br>1. {ordenados[0][0]}: {ordenados[0][1]['1D']:+.2f}% | 2. {ordenados[1][0]}: {ordenados[1][1]['1D']:+.2f}% | 3. {ordenados[2][0]}: {ordenados[2][1]['1D']:+.2f}%</div>", unsafe_allow_html=True)
        with g2:
            st.markdown(f"<div class='radar-box-loser'>🔴 <b>Rezagados de la Rueda (1D)</b><br>1. {ordenados[-1][0]}: {ordenados[-1][1]['1D']:+.2f}% | 2. {ordenados[-2][0]}: {ordenados[-2][1]['1D']:+.2f}% | 3. {ordenados[-3][0]}: {ordenados[-3][1]['1D']:+.2f}%</div>", unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📌 Monitoreo Integral (Watchlist Core con Retornos Históricos)")
        filas_w = []
        for t in WATCHLIST_CORE:
            d = DATOS_RADAR.get(t, {"precio": 0.0, "1D": 0.0, "1M": 0.0, "6M": 0.0, "1Y": 0.0, "YTD": 0.0})
            px_ars = (d["precio"] / RATIOS_CEDEAR.get(t, 1)) * DOLAR_MEP
            filas_w.append({
                "Ticker": t,
                "Precio USD": f"${d['precio']:.2f}",
                "Cedear ARS": f"${px_ars:,.2f}",
                "Var. 1D": f"{d['1D']:+.2f}%",
                "Var. 1M": f"{d['1M']:+.2f}%",
                "Var. 6M": f"{d['6M']:+.2f}%",
                "Var. 1Y": f"{d['1Y']:+.2f}%",
                "Var. YTD": f"{d['YTD']:+.2f}%"
            })
        st.dataframe(pd.DataFrame(filas_w).set_index("Ticker"), use_container_width=True)

# ==============================================================================
# 2. ANÁLISIS INTEGRAL (FUNDAMENTAL + TÉCNICO + DCF + IA)
# ==============================================================================
elif menu == "🔍 ANÁLISIS INTEGRAL":
    c_s1, c_s2 = st.columns([1, 2])
    t_obj = c_s1.selectbox("📍 Activo Bajo Estudio:", UNIVERSO_POOL, index=UNIVERSO_POOL.index(st.session_state.activo_analizado)).upper().strip()
    t_comp_raw = c_s2.text_input("Peers de Control (Separados por coma):", value=st.session_state.peers_analizados).upper()
    
    if st.button("🔥 Correr Análisis"):
        st.session_state.activo_analizado = t_obj
        st.session_state.peers_analizados = t_comp_raw
        st.rerun()

    # Se mantiene la visualización estable
    t_obj = st.session_state.activo_analizado
    peers = [c.strip() for c in st.session_state.peers_analizados.split(",") if c.strip()]
    lista_tickers = [t_obj] + peers
    
    dataset = [obtener_fundamental_completo(tk) for tk in lista_tickers]
    d_obj = dataset[0]
    info_raiz = d_obj["RAW"]
    serie_mc, df_raw = descargar_activo_individual_historico(t_obj)
    
    # Pre-cálculo de DCF Estocástico
    shares = safe_float(info_raiz.get("sharesOutstanding", 0.20 * 1e9))
    ingresos = safe_float(info_raiz.get("totalRevenue", 10.0 * 1e9)) / 1e9
    wacc_base, g_terminal = 0.115, 0.02
    margen_base = d_obj["MARGEN"] if d_obj["MARGEN"] > 0 else 0.15
    precio_mkt = d_obj["Precio"]
    
    sims = 5000
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

    tab_fund, tab_tech, tab_dcf, tab_monte = st.tabs(["📊 Fundamental & IA", "📈 Técnico (DMI)", "🧬 DCF Estocástico", "🎲 Montecarlo Precio"])
    
    # --- PESTAÑA FUNDAMENTAL ---
    with tab_fund:
        st.markdown(f"### 🏢 Perfil y Diagnóstico Operativo: {d_obj['Nombre']}")
        
        # Resumen estructurado por Gemini (máx 5 renglones)
        with st.spinner("Sintetizando modelo de negocio y solvencia..."):
            desc_ia = generar_descripcion_empresa_gemini(
                t_obj, d_obj["Nombre"], 
                {"deuda": d_obj["DEUDA"], "margen": d_obj["MARGEN"], "roe": d_obj["ROE"]}
            )
            st.markdown(f"<div class='gemini-box'>{desc_ia}</div>", unsafe_allow_html=True)
        
        c_w1, c_w2 = st.columns([1, 2])
        with c_w1:
            st.markdown("#### Consenso Sell-Side Wall Street")
            recom = str(info_raiz.get("recommendationKey", "hold")).lower()
            val_gauge = 5 if "strong_buy" in recom or "strong buy" in recom else 4 if "buy" in recom else 2 if "sell" in recom else 3
            
            fig_g = go.Figure(go.Indicator(
                mode="gauge+number", value=val_gauge,
                title={'text': "Escala 1 (Venta) a 5 (Compra)", 'font': {'size': 12}},
                gauge={'axis': {'range': [1, 5], 'tickvals': [1, 2, 3, 4, 5], 'ticktext': ['Venta F.', 'Venta', 'Mantener', 'Compra', 'Compra F.']},
                       'bar': {'color': "#ffffff"},
                       'steps': [{'range': [1, 2.5], 'color': "#ef4444"}, {'range': [2.5, 3.5], 'color': "#1e293b"}, {'range': [3.5, 5], 'color': "#10b981"}]}
            ))
            fig_g.update_layout(height=210, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor='#111520', font={'color': '#ffffff'})
            st.plotly_chart(fig_g, use_container_width=True)
            st.caption("ℹ️ *Fuente: Consenso estandarizado de analistas institucionales vía Yahoo Finance / LSEG.*")
        
        with c_w2:
            st.markdown("#### 📑 Calidad de Balances (Últimos 12M vs Proyección)")
            eps_trail = safe_float(info_raiz.get("trailingEps", 0.0))
            eps_fwd = safe_float(info_raiz.get("forwardEps", eps_trail))
            rev_tot = safe_float(info_raiz.get("totalRevenue", 0.0)) / 1e9
            gross_prof = safe_float(info_raiz.get("grossProfits", rev_tot * 0.4 * 1e9)) / 1e9
            
            tabla_balances = f"""
            <table class='custom-table'>
                <thead>
                    <tr>
                        <th>Métrica Contable ℹ️</th>
                        <th>Últimos 12M (Reportado)</th>
                        <th>Consenso Próximo Ejercicio</th>
                        <th>Variación / Eficiencia</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><b>EPS (Ganancia Neta por Acción)</b></td>
                        <td>${eps_trail:.2f}</td>
                        <td>${eps_fwd:.2f}</td>
                        <td style='color: {"#34d399" if eps_fwd >= eps_trail else "#f87171"}; font-weight:bold;'>{(((eps_fwd/eps_trail)-1)*100 if eps_trail > 0 else 0.0):+.2f}%</td>
                    </tr>
                    <tr>
                        <td><b>Ingresos Totales (Revenue)</b></td>
                        <td>${rev_tot:.2f} B</td>
                        <td>${gross_prof:.2f} B (Beneficio Bruto)</td>
                        <td style='color: #34d399; font-weight:bold;'>{(gross_prof/rev_tot*100 if rev_tot>0 else 0):.1f}% Margen Bruto</td>
                    </tr>
                </tbody>
            </table>
            """
            st.markdown(tabla_balances, unsafe_allow_html=True)
            st.caption("ℹ️ *EPS: Beneficio atribuible por título emitido. Margen Bruto: Rentabilidad tras descontar costos directos de ventas.*")

        st.markdown("---")
        st.markdown("#### 📊 Matriz de Comparación Relativa vs Peers")
        
        # Detección de líderes
        validos_pe = [d for d in dataset if d["PE"] > 0]
        g_pe = min(validos_pe, key=lambda x: x["PE"])["Ticker"] if validos_pe else ""
        g_roe = max(dataset, key=lambda x: x["ROE"])["Ticker"] if dataset else ""
        
        html_mat = "<table class='custom-table'><thead><tr>"
        html_mat += "<th>Ticker</th><th>Nombre</th><th>P/E (Valuación)</th><th>EV/EBITDA</th><th>Deuda Neta/EBITDA</th><th>Liquidez Corr.</th><th>Margen Neto</th><th>ROE (Eficiencia)</th></tr></thead><tbody>"
        for r in dataset:
            c_pe = "class='winner-cell'" if r["Ticker"] == g_pe and g_pe != "" else ""
            c_roe = "class='winner-cell'" if r["Ticker"] == g_roe and g_roe != "" else ""
            html_mat += f"<tr><td><b>{r['Ticker']}</b></td><td>{r['Nombre']}</td><td {c_pe}>{r['PE']:.2f}x</td><td>{r['EV']:.2f}x</td><td>{r['DEUDA']:.2f}x</td><td>{r['LIQUIDEZ']:.2f}x</td><td>{r['MARGEN']*100:.1f}%</td><td {c_roe}>{r['ROE']*100:.1f}%</td></tr>"
        html_mat += "</tbody></table>"
        st.markdown(html_mat, unsafe_allow_html=True)
        
        # Conclusión dinámica sin redundancias
        if g_pe == g_roe and g_pe != "":
            diag = f"<b>{g_pe}</b> lidera integralmente el grupo: ofrece la mayor rentabilidad sobre capital (ROE) combinada con el múltiplo de valuación más comprimido (menor P/E). Esto representa una oportunidad de valor si los márgenes son sostenibles, aunque se debe vigilar el perfil de apalancamiento."
        else:
            diag = f"<b>{g_roe}</b> exhibe la mayor eficiencia operativa y retorno sobre patrimonio (ROE), mientras que <b>{g_pe}</b> presenta el múltiplo P/E más bajo del lote, otorgando un mayor margen de seguridad en valuación relativa frente a sus competidores."
        st.markdown(f"<div class='interpretation-box'><b>Conclusión de Múltiplos:</b> {diag}</div>", unsafe_allow_html=True)
        
        # Generación de tesis con persistencia
        st.markdown("---")
        st.markdown("#### 🤖 Tesis de Inversión Automatizada (Powered by Gemini AI)")
        if st.button(f"✨ Redactar Tesis Ejecutiva para {t_obj}"):
            with st.spinner("Procesando balances con Gemini..."):
                tesis_res = generar_tesis_gemini(
                    t_obj, d_obj["Nombre"], d_obj["Precio"], d_obj["PE"],
                    d_obj["ROE"], d_obj["DEUDA"], d_obj["MARGEN"], dcf_mediano
                )
                st.session_state[f"tesis_{t_obj}"] = tesis_res
        
        if f"tesis_{t_obj}" in st.session_state:
            st.markdown(f"<div class='gemini-box'>{st.session_state[f'tesis_{t_obj}']}</div>", unsafe_allow_html=True)

    # --- PESTAÑA TÉCNICA (DMI) ---
    with tab_tech:
        st.markdown(f"### 📈 Análisis Direccional (DMI / ADX): {t_obj}")
        st.markdown("""<div class='interpretation-box'>
        <b>Marco Conceptual DMI (Directional Movement Index):</b> Evalúa la fuerza e intencionalidad del precio mediante el cruce de presiones compradoras (+DI) y vendedoras (-DI). Un ADX superior a 25 puntos valida una tendencia institucional definida con volumen sostenido, mientras que lecturas inferiores reflejan consolidación lateral o indecisión técnica.
        </div>""", unsafe_allow_html=True)
        
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
            fig_d.add_trace(go.Scatter(x=df_t.index, y=df_t['Close'], name="Precio", line=dict(color='#ffffff')), row=1, col=1)
            fig_d.add_trace(go.Scatter(x=df_t.index, y=df_t['EMA30'], name="EMA 30", line=dict(color='#f1c40f', dash='dash')), row=1, col=1)
            fig_d.add_trace(go.Scatter(x=df_t.index, y=df_t['+DI'], name="+DI (Compradores)", line=dict(color='#10b981')), row=2, col=1)
            fig_d.add_trace(go.Scatter(x=df_t.index, y=df_t['-DI'], name="-DI (Vendedores)", line=dict(color='#ef4444')), row=2, col=1)
            fig_d.add_trace(go.Scatter(x=df_t.index, y=df_t['ADX'], name="ADX (Fuerza)", line=dict(color='#3b82f6')), row=2, col=1)
            fig_d.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', height=400, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_d, use_container_width=True)
            
            di_p, di_m, adx_val = df_t['+DI'].iloc[-1], df_t['-DI'].iloc[-1], df_t['ADX'].iloc[-1]
            soporte = df_t['Low'].tail(30).min()
            resistencia = df_t['High'].tail(30).max()
            
            estado = "TENDENCIA ALCISTA SÓLIDA 🟢" if (di_p > di_m and adx_val > 25) else "NEUTRAL / LATERAL 🟡" if (adx_val <= 25) else "TENDENCIA BAJISTA ACTIVA 🔴"
            st.markdown(f"<div class='interpretation-box'><b>Señal Técnica Actual:</b> {estado} | <b>Soporte (30D):</b> ${soporte:.2f} | <b>Resistencia (30D):</b>${resistencia:.2f}</div>", unsafe_allow_html=True)

    # --- PESTAÑA DCF ESTOCÁSTICO ---
    with tab_dcf:
        st.markdown("### 🧬 Valuación por Flujos Descontados (DCF Estocástico)")
        st.markdown("""<div class='interpretation-box'>
        <b>Fundamento Teórico:</b> Modela el valor intrínseco por acción proyectando el Flujo de Caja Libre (FCF) a 5 años más valor terminal perpetuo. A diferencia del DCF estático, ejecuta 5.000 simulaciones Monte Carlo asignando distribuciones de probabilidad al crecimiento de ingresos y márgenes operativos netos, descontados a una tasa WACC exigida.
        </div>""", unsafe_allow_html=True)
        
        fig_dcf = px.histogram(vals_dcf, nbins=50, title=f"Distribución del Valor Justo vs Mercado (${precio_mkt:.2f} USD)", color_discrete_sequence=['#10b981'])
        fig_dcf.add_vline(x=precio_mkt, line_width=3, line_dash="dash", line_color="#ef4444", annotation_text="Precio Mercado")
        fig_dcf.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', showlegend=False)
        st.plotly_chart(fig_dcf, use_container_width=True)
        
        margen_seguridad = ((dcf_mediano - precio_mkt) / dcf_mediano) * 100
        veredicto_dcf = "SUBVALUADO (Margen de Seguridad Favorable) 🟢" if margen_seguridad > 0 else "SOBREVALUADO (Sin Margen de Seguridad) 🔴"
        st.markdown(f"<div class='interpretation-box'><b>Diagnóstico DCF:</b> {veredicto_dcf}<br>• Precio Mercado: <b>${precio_mkt:.2f} USD</b> | Mediana Intrínseca Estimada: <b>${dcf_mediano:.2f} USD</b> (Diferencia: {margen_seguridad:+.1f}%)</div>", unsafe_allow_html=True)

    # --- PESTAÑA MONTECARLO PRECIO ---
    with tab_monte:
        st.markdown("### 🎲 Simulación Estocástica de Precios (Movimiento Browniano Geométrico)")
        st.markdown("""<div class='interpretation-box'>
        <b>Fundamento Teórico:</b> El Movimiento Browniano Geométrico (GBM) modela la dinámica estocástica de cotizaciones asumiendo retornos logarítmicos normales con deriva ($\mu$) y volatilidad histórica ($\sigma$). Computa 5.000 senderos aleatorios para mapear zonas de densidad y conos de probabilidad a 30 y 252 ruedas operativas.
        </div>""", unsafe_allow_html=True)
        
        if not serie_mc.empty:
            ret = serie_mc.pct_change().dropna()
            sigma = ret.std()
            mu_d = ret.mean() - 0.5 * (sigma ** 2)
            px_0 = float(serie_mc.iloc[-1])
            
            mc1, mc2 = st.columns(2)
            with mc1:
                st.markdown("#### Cono de Corto Plazo (30 Ruedas)")
                m_30 = np.zeros((30, 1000))
                m_30[0] = px_0
                z_30 = np.random.standard_normal((29, 1000))
                for t in range(1, 30):
                    m_30[t] = m_30[t-1] * np.exp(mu_d + sigma * z_30[t-1])
                
                f30 = go.Figure()
                for i in range(25): f30.add_trace(go.Scatter(y=m_30[:, i], mode='lines', line=dict(color='rgba(59, 130, 246, 0.08)'), showlegend=False))
                f30.add_trace(go.Scatter(y=np.median(m_30, axis=1), mode='lines', line=dict(color='#10b981', width=2), name="Mediana"))
                f30.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', height=280, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(f30, use_container_width=True)
                
            with mc2:
                st.markdown("#### Cono de Largo Plazo (1 Año - 252 Ruedas)")
                m_252 = np.zeros((252, 1000))
                m_252[0] = px_0
                z_252 = np.random.standard_normal((251, 1000))
                for t in range(1, 252):
                    m_252[t] = m_252[t-1] * np.exp(mu_d + sigma * z_252[t-1])
                
                f252 = go.Figure()
                for i in range(25): f252.add_trace(go.Scatter(y=m_252[:, i], mode='lines', line=dict(color='rgba(168, 85, 247, 0.08)'), showlegend=False))
                f252.add_trace(go.Scatter(y=np.median(m_252, axis=1), mode='lines', line=dict(color='#a855f7', width=2), name="Mediana"))
                f252.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', height=280, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(f252, use_container_width=True)

# ==============================================================================
# 3. PORTAFOLIO Y MODELOS INSTITUCIONALES
# ==============================================================================
elif menu == "💼 PORTAFOLIO Y MODELOS":
    st.subheader("💼 Portafolio Consolidado (Tracking de Posiciones y Benchmark)")
    is_ars = st.radio("Moneda de visualización:", ["ARS", "USD"], horizontal=True) == "ARS"
    
    df_cartera = pd.DataFrame(st.session_state.cartera)
    filas_p = []
    c_tot_usd, v_tot_usd, div_tot_usd = 0.0, 0.0, 0.0
    
    for pos in st.session_state.cartera:
        tk, nom, px_c, com, divs = pos["Ticker"], pos["Nominales"], pos["Costo_Unitario_Cedear"], pos["Comision_USD"], pos.get("Dividendos_USD", 0.0)
        ratio = RATIOS_CEDEAR.get(tk, 1)
        px_actual_usd = DATOS_RADAR.get(tk, {}).get("precio", (px_c * ratio / DOLAR_MEP))
        
        costo_usd = ((nom * px_c) / DOLAR_MEP) * ratio + com
        val_usd = nom * px_actual_usd
        pl_usd = (val_usd + divs) - costo_usd
        ret_pct = (pl_usd / costo_usd) * 100 if costo_usd > 0 else 0.0
        
        c_tot_usd += costo_usd
        v_tot_usd += val_usd
        div_tot_usd += divs
        
        fac = (DOLAR_MEP / ratio) if is_ars else 1.0
        filas_p.append({
            "Ticker": tk, "Nominales": nom,
            "Costo Unitario": f"${(px_c if is_ars else (px_c*ratio/DOLAR_MEP)):,.2f}",
            "Precio Actual": f"${(px_actual_usd*DOLAR_MEP/ratio if is_ars else px_actual_usd):,.2f}",
            "Capital Invertido": f"${costo_usd * (DOLAR_MEP if is_ars else 1):,.2f}",
            "Valuación": f"${val_usd * (DOLAR_MEP if is_ars else 1):,.2f}",
            "Dividendos": f"${divs * (DOLAR_MEP if is_ars else 1):,.2f}",
            "P&L Neto": f"${pl_usd * (DOLAR_MEP if is_ars else 1):,.2f}",
            "Total Return": f"{ret_pct:+.2f}%"
        })
    
    st.dataframe(pd.DataFrame(filas_p).set_index("Ticker"), use_container_width=True)
    
    # Métricas patrimoniales con tipografía balanceada
    st.markdown("#### Métricas Consolidadas")
    k1, k2, k3, k4, k5 = st.columns(5)
    ret_total_cartera = ((v_tot_usd + div_tot_usd - c_tot_usd) / c_tot_usd) * 100 if c_tot_usd > 0 else 0.0
    mon_lbl = "ARS" if is_ars else "USD"
    conv = DOLAR_MEP if is_ars else 1.0
    
    # Benchmarks SPY y QQQ
    spy_ret = DATOS_RADAR.get("SPY", {}).get("YTD", 0.0)
    qqq_ret = DATOS_RADAR.get("QQQ", {}).get("YTD", 0.0)
    alpha_spy = ret_total_cartera - spy_ret
    
    k1.metric("Capital Invertido", f"${(c_tot_usd*conv):,.0f} {mon_lbl}")
    k2.metric("Valuación Actual", f"${(v_tot_usd*conv):,.0f} {mon_lbl}")
    k3.metric("Rentas/Divs", f"${(div_tot_usd*conv):,.0f} {mon_lbl}")
    k4.metric("Total Return", f"{ret_total_cartera:+.2f}%")
    k5.metric("Alpha vs SPY", f"{alpha_spy:+.2f}%", delta_color="normal" if alpha_spy >= 0 else "inverse")
    
    # Gráfico Benchmark Portfolio vs SPY vs QQQ
    st.markdown("---")
    st.markdown("#### 📊 Curva de Rendimiento Relativo: Cartera vs. SPY vs. QQQ (Base 100)")
    try:
        tks_bench = list(set([p["Ticker"] for p in st.session_state.cartera] + ["SPY", "QQQ"]))
        _, df_b = descargar_datos_mercado(tks_bench)
        if not df_b.empty and 'SPY' in df_b.columns and 'QQQ' in df_b.columns:
            # Simulación ponderada de cartera
            weights = {p["Ticker"]: (p["Nominales"] * DATOS_RADAR.get(p["Ticker"], {}).get("precio", 100)) for p in st.session_state.cartera}
            w_sum = sum(weights.values())
            weights = {k: v / w_sum for k, v in weights.items()}
            
            df_norm = pd.DataFrame(index=df_b.index)
            cartera_serie = sum(df_b[tk] / df_b[tk].iloc[0] * weights[tk] for tk in weights if tk in df_b.columns)
            
            df_norm["Mi Cartera"] = (cartera_serie - 1) * 100
            df_norm["S&P 500 (SPY)"] = ((df_b["SPY"] / df_b["SPY"].iloc[0]) - 1) * 100
            df_norm["Nasdaq 100 (QQQ)"] = ((df_b["QQQ"] / df_b["QQQ"].iloc[0]) - 1) * 100
            
            fig_bench = px.line(df_norm, y=["Mi Cartera", "S&P 500 (SPY)", "Nasdaq 100 (QQQ)"],
                                color_discrete_map={"Mi Cartera": "#10b981", "S&P 500 (SPY)": "#3b82f6", "Nasdaq 100 (QQQ)": "#a855f7"})
            fig_bench.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', height=360, yaxis_title="Retorno Acumulado (%)")
            st.plotly_chart(fig_bench, use_container_width=True)
    except Exception as e:
        st.caption(f"Curva de benchmark en sincronización: {e}")

    # --- SECCIÓN IDEAS INSTITUCIONALES LIMPIAS ---
    st.markdown("---")
    st.subheader("🎯 Ideas de Inversión Institucionales (Desglosadas por Fundamentos)")
    
    ideas = {
        "💰 Income & Dividendos": [
            ("KO", "**Coca-Cola:** Payout ratio predecible, flujo de caja global inelástico y bajo riesgo de refinanciación."),
            ("PEP", "**PepsiCo:** Fuerte diversificación en snacks/alimentos que amortigua la volatilidad de insumos."),
            ("XOM", "**ExxonMobil:** Breakeven operativo líder (<$35/barril) permitiendo recompras continuas.")
        ],
        "🏢 Calidad & Wide Moat": [
            ("ASML", "**ASML:** Monopolio absoluto en litografía ultravioleta extrema (EUV), fijación de precios asegurada."),
            ("V", "**Visa:** Red transaccional con márgenes operativos sobre el 55% y mínimo requerimiento de CapEx."),
            ("MSFT", "**Microsoft:** Foso defensivo B2B en software corporativo e infraestructura cloud.")
        ],
        "🚀 Crecimiento Estructural": [
            ("NVDA", "**Nvidia:** Dominio absoluto de arquitecturas de cómputo para centros de datos de IA."),
            ("PLTR", "**Palantir:** Expansión acelerada de márgenes comerciales y contratos corporativos de software.")
        ]
    }
    
    tabs_id = st.tabs(list(ideas.keys()))
    for idx, (cat, items) in enumerate(ideas.items()):
        with tabs_id[idx]:
            for tk, desc in items:
                st.markdown(f"• {desc}")

    # --- OPTIMIZACIÓN MARKOWITZ ---
    st.markdown("---")
    st.subheader("🧠 Optimización de Portafolio (Markowitz - Max Sharpe Ratio)")
    if st.button("Calcular Asignación Eficiente"):
        tks_port = list(set([p["Ticker"] for p in st.session_state.cartera]))
        if len(tks_port) < 2:
            st.error("Se necesitan al menos 2 activos distintos para calcular la matriz de covarianza.")
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
            
            fig_pie = px.pie(values=res.x, names=tks_port, title="Pesos Sugeridos (Máximo Sharpe)", hole=0.4, color_discrete_sequence=px.colors.sequential.Teal)
            fig_pie.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16')
            st.plotly_chart(fig_pie, use_container_width=True)

# ==============================================================================
# FOOTER
# ==============================================================================
st.markdown("---")
st.markdown("<p style='text-align: right; font-size: 12px; color: #94a3b8;'>Desarrollado por <a href='https://www.linkedin.com/in/facundo-garciamarquez/?locale=es' target='_blank' style='color: #10b981; text-decoration: none; font-weight: 700;'>Facundo Garcia Marquez</a> | Terminal Quanti Pro</p>", unsafe_allow_html=True)
st.markdown("""<div style='background-color: rgba(239, 68, 68, 0.08); padding: 10px; border-left: 3px solid #ef4444; font-size: 11px; color: #94a3b8;'>
<strong>⚠️ Exclusión de Responsabilidad:</strong> Herramienta con fines analíticos y de simulación académica. No representa asesoramiento financiero ni recomendación directa de compra o venta.
</div>""", unsafe_allow_html=True)
