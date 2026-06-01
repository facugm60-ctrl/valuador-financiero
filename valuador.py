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
# 1. CONFIGURACIÓN Y ESTILOS
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
    .stButton>button { width: 100%; background: linear-gradient(135deg, #2ecc71, #27ae60) !important; color: white !important; font-weight: 700; border-radius: 8px; border: none; padding: 0.6rem; font-size: 13px !important; }
    div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] div, div[data-testid="stNumberInput"] input { background-color: #111520 !important; color: #ffffff !important; border: 1px solid #1f2937 !important; border-radius: 8px !important; }
    .radar-box-gainer-high { background: linear-gradient(135deg, #064e3b, #047857); border: 1px solid #10b981; padding: 14px; border-radius: 8px; font-weight: bold; color: #34d399 !important; }
    .radar-box-loser { background: linear-gradient(135deg, #7f1d1d, #b91c1c); border: 1px solid #f87171; padding: 14px; border-radius: 8px; font-weight: bold; color: #f87171 !important; }
    .interpretation-box { background-color: #111520; padding: 16px; border-radius: 8px; font-size: 13px; color: #e2e8f0; border: 1px solid #1f2937; border-left: 4px solid #2ecc71; margin-top: 10px; }
    .agent-box { background-color: #090d16; padding: 18px; border-radius: 8px; font-size: 13px; color: #e2e8f0; border: 1px solid #1f2937; border-left: 4px solid #dfa427; margin-top: 10px; }
    .custom-table { width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 13px; background-color: #111520; border-radius: 8px; overflow: hidden; border: 1px solid #1f2937; }
    .custom-table th { background-color: #161b22; color: #ffffff; padding: 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #1f2937; }
    .custom-table td { padding: 12px; border-bottom: 1px solid #1f2937; color: #e2e8f0; }
    .winner-cell { background-color: rgba(46, 204, 113, 0.15) !important; color: #2ecc71 !important; font-weight: bold; }
    .tooltip { position: relative; display: inline-block; cursor: pointer; color: #3498db; margin-left: 4px; font-weight: bold; }
    .tooltip .tooltiptext { visibility: hidden; width: 280px; background-color: #1f2937; color: #fff; padding: 12px; border-radius: 6px; position: absolute; z-index: 999; bottom: 125%; left: 50%; margin-left: -140px; font-size: 11px; border: 1px solid #3b82f6; }
    .tooltip:hover .tooltiptext { visibility: visible; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. FUNCIONES DE DATOS Y SCRAPING
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
UNIVERSO_POOL = ["VIST", "YPF", "AAPL", "GGAL", "AMD", "NVDA", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "KO", "WMT", "XOM", "SPY", "QQQ", "JNJ", "PEP", "PG", "MO", "CVX", "MCD", "BRKB", "MELI", "BABA", "PYPL", "NFLX", "DESP", "VALE"]

@st.cache_data(ttl=600)
def descargar_datos_historicos(universo):
    datos_dict = {}
    try:
        df_hist = yf.download(universo, period="2y", progress=False, session=yf_session)
        df_close = df_hist["Close"] if "Close" in df_hist.columns else df_hist
        df_close = df_close.ffill().bfill()
        fecha_ytd = f"{datetime.datetime.now().year}-01-02"
        for tk in universo:
            try:
                serie = df_close[tk].dropna() if isinstance(df_close, pd.DataFrame) and tk in df_close.columns else (df_close.dropna() if isinstance(df_close, pd.Series) else pd.Series(dtype=float))
                if not serie.empty and len(serie) >= 30:
                    px_actual = float(serie.iloc[-1])
                    v1d, v1w, v1m = ((px_actual / float(serie.iloc[-2])) - 1) * 100, ((px_actual / float(serie.iloc[-6])) - 1) * 100, ((px_actual / float(serie.iloc[-22])) - 1) * 100
                    v_ytd = ((px_actual / float(serie.loc[fecha_ytd:].iloc[0])) - 1) * 100 if not serie.loc[fecha_ytd:].empty else 0.0
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

def obtener_fundamental_completo(symbol):
    try:
        t = yf.Ticker(symbol, session=yf_session)
        inf = t.info or {}
        px = POOL_DATA.get(symbol, {}).get("precio", inf.get("currentPrice", 50.0))
        eb = safe_float(inf.get("ebitda"), 1.0)
        td, caj = safe_float(inf.get("totalDebt")), safe_float(inf.get("totalCash"))
        return {
            "Ticker": symbol, "Nombre": inf.get("longName", symbol), "Precio": px,
            "PE": safe_float(inf.get("forwardPE")), "EV": safe_float(inf.get("enterpriseToEbitda")),
            "DEUDA": (td - caj) / eb if eb != 0 else 0.0, "LIQUIDEZ": safe_float(inf.get("currentRatio")),
            "MARGEN": safe_float(inf.get("profitMargins")), "ROE": safe_float(inf.get("returnOnEquity")), "RAW": inf
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
# 3. INTERFAZ PRINCIPAL Y DASHBOARD
# ==============================================================================
if "cartera_list_v4" not in st.session_state: st.session_state.cartera_list_v4 = []

menu = st.radio("Secciones operativas:", ["🌐 DASHBOARD", "🔍 ANÁLISIS INTEGRAL", "💼 PORTAFOLIO"], horizontal=True)
st.markdown("---")

if menu == "🌐 DASHBOARD":
    st.subheader("⚡ Market Radar: Momentum de Ruedas")
    ordenados = sorted(POOL_DATA.items(), key=lambda x: x[1]["1D"], reverse=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='radar-box-gainer-high'>🟢 Liderando la Rueda<br><br>• {ordenados[0][0]}: {ordenados[0][1]['1D']:+.2f}%</div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='radar-box-loser'>🔴 Mayor Compresión<br><br>• {ordenados[-1][0]}: {ordenados[-1][1]['1D']:+.2f}%</div>", unsafe_allow_html=True)
    with c3: st.markdown("<div class='radar-box-gainer-high'>🚀 Impulso Factorial Continuo<br><br>• VIST: Flujo en Expansión</div>", unsafe_allow_html=True)
    with c4: st.markdown("<div class='radar-box-loser'>📉 Compresión de Margen<br><br>• KO: Estructura de Resguardo</div>", unsafe_allow_html=True)

elif menu == "🔍 ANÁLISIS INTEGRAL":
    c_s1, c_s2 = st.columns([1, 2])
    t_obj = c_s1.text_input("📍 Activo Bajo Estudio:", value="VIST").upper().strip()
    t_comp_raw = c_s2.text_input("Peers de Control (Separados por coma):", value="YPF, XOM").upper()
    
    if st.button("🔥 Correr Análisis"):
        with st.spinner("Descargando balances corporativos..."):
            peers = [c.strip() for c in t_comp_raw.split(",") if c.strip()]
            dataset = [obtener_fundamental_completo(tk) for tk in [t_obj] + filtrar_peers_por_sector(t_obj, peers) if obtener_fundamental_completo(tk)]
            info_raiz = next((d["RAW"] for d in dataset if d["Ticker"] == t_obj), {})
            
            if dataset:
                tab_fund, tab_tech, tab_mc = st.tabs(["📊 Fundamental", "📈 Técnico (DMI)", "🎲 Montecarlo"])
                
                with tab_fund:
                    st.markdown("### 🏢 ¿A qué se dedica esta empresa?")
                    desc = info_raiz.get("longBusinessSummary", "Resumen no disponible.")
                    if HAS_TRANSLATOR and desc != "Resumen no disponible.":
                        try: desc = GoogleTranslator(source='en', target='es').translate(desc)
                        except: pass
                    st.info(desc)
                    
                    col_rel, col_caja = st.columns([1, 2])
                    with col_rel:
                        st.markdown("#### ¿Qué opina Wall Street?")
                        recom = str(info_raiz.get("recommendationKey", "hold")).lower()
                        val = 5 if "strong buy" in recom else 4 if "buy" in recom else 2 if "sell" in recom else 3
                        fig_gauge = go.Figure(go.Indicator(mode="gauge+number", value=val, title={'text': "Consenso", 'font': {'size': 14}}, gauge={'axis': {'range': [1, 5]}, 'steps': [{'range': [1, 2.5], 'color': "#7f1d1d"}, {'range': [2.5, 3.5], 'color': "#111520"}, {'range': [3.5, 5], 'color': "#064e3b"}]}))
                        fig_gauge.update_layout(height=220, margin=dict(l=10,r=10,t=30,b=10), paper_bgcolor='#111520', font={'color': '#ffffff'})
                        st.plotly_chart(fig_gauge, use_container_width=True)
                        
                    with col_caja:
                        st.markdown("#### 🎁 Caja de Sorpresas: Últimos 4 Trimestres")
                        try:
                            q_fin = yf.Ticker(t_obj, session=yf_session).quarterly_financials
                            if not q_fin.empty:
                                r_rev = q_fin.index[q_fin.index.str.lower().str.replace(" ", "").str.contains("totalrevenue")][0]
                                r_net = q_fin.index[q_fin.index.str.lower().str.replace(" ", "").str.contains("netincome")][0]
                                df_q = q_fin.loc[[r_rev, r_net]].dropna(axis=1).iloc[:, :4]
                                labels = [d.strftime('%d-%m-%Y') for d in df_q.columns][::-1]
                                revs, nets = (df_q.loc[r_rev].values / 1e9)[::-1], (df_q.loc[r_net].values / 1e9)[::-1]
                                fig_c = go.Figure(data=[go.Bar(name='Ingresos (Billion USD)', x=labels, y=revs, marker_color='#3498db'), go.Bar(name='Ganancia Neta (Billion USD)', x=labels, y=nets, marker_color='#2ecc71')])
                                fig_c.update_layout(barmode='group', template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', height=200, margin=dict(l=10,r=10,t=10,b=20))
                                st.plotly_chart(fig_c, use_container_width=True)
                            else: st.warning("Datos trimestrales no públicos.")
                        except: st.warning("Error conectando con los reportes trimestrales.")
                    
                    st.markdown("---")
                    st.markdown("#### Matriz de Comparación")
                    g_pe, g_roe = min(dataset, key=lambda x: x["PE"])["Ticker"], max(dataset, key=lambda x: x["ROE"])["Ticker"]
                    html_tb = "<table class='custom-table'><thead><tr><th>Ticker</th><th>Razón Social</th><th>P/E</th><th>EV/EBITDA</th><th>Deuda</th><th>Liquidez</th><th>Margen</th><th>ROE</th></tr></thead><tbody>"
                    for r in dataset:
                        html_tb += f"<tr><td><b>{r['Ticker']}</b></td><td>{r['Nombre']}</td><td {'class=winner-cell' if r['Ticker']==g_pe else ''}>{r['PE']:.2f}</td><td>{r['EV']:.2f}</td><td>{r['DEUDA']:.2f}x</td><td>{r['LIQUIDEZ']:.2f}x</td><td>{r['MARGEN']*100:.1f}%</td><td {'class=winner-cell' if r['Ticker']==g_roe else ''}>{r['ROE']*100:.1f}%</td></tr>"
                    html_tb += "</tbody></table>"
                    st.markdown(html_tb, unsafe_allow_html=True)
                    st.markdown(f"<div class='interpretation-box'><b>Conclusión Sencilla:</b> Comparando con sus rivales, <b>{g_roe}</b> es la que mejor hace rendir la plata. Si miramos qué tan barata está, <b>{g_pe}</b> parece ser la mejor oferta en vitrina.</div>", unsafe_allow_html=True)

                with tab_tech:
                    st.markdown(f"### 📈 El pulso del mercado (Gráfico DMI): {t_obj}")
                    st.markdown("**¿Cómo leer esto?** Línea Verde (Compradores), Línea Roja (Vendedores), Línea Azul (Fuerza de Tendencia).")
                    hist_raw = yf.download(t_obj, period="1y", progress=False, session=yf_session)
                    df_t = pd.DataFrame({"High": hist_raw["High"].iloc[:,0] if isinstance(hist_raw.columns, pd.MultiIndex) else hist_raw["High"], "Low": hist_raw["Low"].iloc[:,0] if isinstance(hist_raw.columns, pd.MultiIndex) else hist_raw["Low"], "Close": hist_raw["Close"].iloc[:,0] if isinstance(hist_raw.columns, pd.MultiIndex) else hist_raw["Close"]}).ffill().bfill()
                    if not df_t.empty:
                        df_t['EMA30'] = df_t['Close'].ewm(span=30, adjust=False).mean()
                        up, down = df_t['High'].diff(), -df_t['Low'].diff()
                        pdm, mdm = np.where((up > down) & (up > 0), up, 0.0), np.where((down > up) & (down > 0), down, 0.0)
                        tr = pd.DataFrame({'tr1': df_t['High']-df_t['Low'], 'tr2': abs(df_t['High']-df_t['Close'].shift(1)), 'tr3': abs(df_t['Low']-df_t['Close'].shift(1))}).max(axis=1)
                        trs = tr.rolling(14).sum()
                        df_t['+DI'] = 100 * (pd.Series(pdm, index=df_t.index).rolling(14).sum() / trs)
                        df_t['-DI'] = 100 * (pd.Series(mdm, index=df_t.index).rolling(14).sum() / trs)
                        df_t['ADX'] = (100 * abs(df_t['+DI'] - df_t['-DI']) / (df_t['+DI'] + df_t['-DI'])).rolling(14).mean()
                        df_t = df_t.dropna()
                        
                        fig_dmi = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.65, 0.35], vertical_spacing=0.04)
                        fig_dmi.add_trace(go.Scatter(x=df_t.index, y=df_t['Close'], name="Precio Cierre", line=dict(color='#ffffff')), row=1, col=1)
                        fig_dmi.add_trace(go.Scatter(x=df_t.index, y=df_t['EMA30'], name="EMA 30", line=dict(color='#f1c40f', dash='dash')), row=1, col=1)
                        fig_dmi.add_trace(go.Scatter(x=df_t.index, y=df_t['+DI'], name="+DI (Verde)", line=dict(color='#2ecc71')), row=2, col=1)
                        fig_dmi.add_trace(go.Scatter(x=df_t.index, y=df_t['-DI'], name="-DI (Rojo)", line=dict(color='#e74c3c')), row=2, col=1)
                        fig_dmi.add_trace(go.Scatter(x=df_t.index, y=df_t['ADX'], name="ADX (Azul)", line=dict(color='#3498db')), row=2, col=1)
                        fig_dmi.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', height=450, margin=dict(l=20,r=20,t=10,b=10))
                        st.plotly_chart(fig_dmi, use_container_width=True)
                        
                        p, di_p, di_m, adx = df_t['Close'].iloc[-1], df_t['+DI'].iloc[-1], df_t['-DI'].iloc[-1], df_t['ADX'].iloc[-1]
                        dom = "los COMPRADORES" if di_p > di_m else "los VENDEDORES"
                        tend = "con muchísimo impulso y tendencia clara." if adx > 25 else "pero el mercado está dudoso y sin rumbo claro."
                        st.markdown(f"<div class='interpretation-box'><strong>¿QUIÉN TIENE EL VOLANTE HOY?</strong> Al precio de <b>${p:.2f}</b>, <b>{dom}</b> tienen el control total, {tend}</div>", unsafe_allow_html=True)
                    else: st.error("No hay datos para el gráfico.")

                with tab_mc:
                    st.markdown("### 🎲 La Máquina del Tiempo (Simulador de Escenarios)")
                    st.markdown("**¿Qué es esto?** Tiramos los dados 100 veces basándonos en cómo se movió el último año para ver los caminos posibles.")
                    df_mc = hist_raw["Close"].iloc[:,0] if isinstance(hist_raw.columns, pd.MultiIndex) else hist_raw["Close"]
                    ret = df_mc.pct_change().dropna()
                    mu, sigma, p_b = ret.mean(), ret.std(), df_mc.iloc[-1]
                    
                    cm1, cm2 = st.columns(2)
                    with cm1:
                        st.markdown("#### Corto Plazo: 30 días")
                        m_1m = np.zeros((30, 100))
                        m_1m[0] = p_b
                        for t in range(1, 30): m_1m[t] = m_1m[t-1] * np.exp((mu - 0.5 * sigma**2) + sigma * np.random.standard_normal(100))
                        f1m = go.Figure()
                        for i in range(40): f1m.add_trace(go.Scatter(y=m_1m[:, i], mode='lines', line=dict(color='rgba(52, 152, 219, 0.08)'), showlegend=False))
                        f1m.add_trace(go.Scatter(y=np.mean(m_1m, axis=1), mode='lines', name="Promedio", line=dict(color='#2ecc71', width=2.5)))
                        f1m.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', height=300, margin=dict(l=10,r=10,t=10,b=10))
                        st.plotly_chart(f1m, use_container_width=True)
                        
                        pe, pdn, pup = np.mean(m_1m[-1, :]), np.percentile(m_1m[-1, :], 5), np.percentile(m_1m[-1, :], 95)
                        st.markdown(f"<div class='agent-box'>Teniendo en cuenta el escenario vanilla (que mantenga la misma inercia), el <b>Fair Value (Precio Justo) a 30 días</b> es <b>${pe:.2f}</b>. Si hay euforia compradora subiría a <b>${pup:.2f}</b>, pero si hay pánico el soporte base caería a <b>${pdn:.2f}</b>.</div>", unsafe_allow_html=True)
                    
                    with cm2:
                        st.markdown("#### Largo Plazo: 1 Año (252 días)")
                        m_1y = np.zeros((252, 100))
                        m_1y[0] = p_b
                        for t in range(1, 252): m_1y[t] = m_1y[t-1] * np.exp((mu - 0.5 * sigma**2) + sigma * np.random.standard_normal(100))
                        f1y = go.Figure()
                        for i in range(40): f1y.add_trace(go.Scatter(y=m_1y[:, i], mode='lines', line=dict(color='rgba(155, 89, 182, 0.08)'), showlegend=False))
                        f1y.add_trace(go.Scatter(y=np.mean(m_1y, axis=1), mode='lines', name="Promedio", line=dict(color='#9b59b6', width=2.5)))
                        f1y.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', height=300, margin=dict(l=10,r=10,t=10,b=10))
                        st.plotly_chart(f1y, use_container_width=True)
                        
                        pe_y, pdn_y, pup_y = np.mean(m_1y[-1, :]), np.percentile(m_1y[-1, :], 5), np.percentile(m_1y[-1, :], 95)
                        st.markdown(f"<div class='agent-box'>Teniendo en cuenta el escenario vanilla, el <b>Fair Value a 1 Año</b> es <b>${pe_y:.2f}</b>. Por el factor tiempo, en un mercado ultra alcista tocaría los <b>${pup_y:.2f}</b>, o frente a una crisis recesiva el soporte frenaría en los <b>${pdn_y:.2f}</b>.</div>", unsafe_allow_html=True)

elif menu == "💼 PORTAFOLIO":
    st.markdown("### 💼 Módulo de Portafolio en Mantenimiento Táctico")
    st.info("La matriz de la cartera se está ajustando en esta versión simplificada anti-cortes.")
    
st.markdown("---")
st.markdown("<p style='text-align: right; font-size: 12px; color: #2ecc71; font-weight: 600;'>Facundo Garcia Marquez | Terminal Quanti Pro</p>", unsafe_allow_html=True)
