# -*- coding: utf-8 -*-
import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import numpy as np
import datetime
import requests
from bs4 import BeautifulSoup
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# MIGRACIÓN DE MOTOR A YAHOOQUERY
try:
    from yahooquery import Ticker
except ImportError:
    st.error("Por favor, agrega 'yahooquery' a tu archivo requirements.txt en GitHub.")

try:
    from deep_translator import GoogleTranslator
    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False

# ==============================================================================
# BASE DE DATOS DE RESPALDO (POR SI YAHOO FINANCE BLOQUEA LA DESCRIPCIÓN)
# ==============================================================================
FALLBACK_SUMMARIES = {
    "VIST": "Vista Energy es una compañía independiente de petróleo y gas, enfocada principalmente en la exploración y producción de Vaca Muerta, Argentina. Es uno de los operadores líderes en la cuenca, destacándose por su alta eficiencia operativa, bajos costos de extracción y rápida expansión en la producción de crudo no convencional (shale oil) destinado tanto al mercado interno como a la exportación.",
    "YPF": "YPF Sociedad Anónima es la principal empresa energética de Argentina, dedicada a la exploración, producción, refinación y venta de petróleo, gas y derivados. Como líder histórico del país y actor central en Vaca Muerta, controla gran parte del mercado de combustibles y está expandiendo su infraestructura hacia el GNL y energías renovables.",
    "XOM": "Exxon Mobil Corporation es uno de los gigantes energéticos más grandes del mundo. Explora, produce y refina petróleo y gas a nivel global. Su modelo de negocio integrado (desde el pozo hasta la estación de servicio) y su enorme escala le permiten generar flujos de caja masivos y sostener una política de dividendos robusta, siendo un pilar defensivo en el sector.",
    "AAPL": "Apple Inc. diseña, fabrica y vende teléfonos inteligentes (iPhone), computadoras (Mac), tabletas (iPad) y relojes inteligentes, además de contar con un ecosistema de servicios altamente rentable (App Store, Apple Music, iCloud). Su ventaja competitiva radica en la fidelidad de sus usuarios y un ecosistema cerrado que le permite altos márgenes de ganancia.",
    "MSFT": "Microsoft Corporation es un líder global en software, servicios y soluciones en la nube. A través de su plataforma Azure, domina la infraestructura corporativa mundial, complementada con su suite de productividad (Office 365), sistemas operativos (Windows) y su reciente liderazgo en inteligencia artificial generativa aplicada a negocios.",
    "NVDA": "NVIDIA Corporation es el líder indiscutido en el diseño de unidades de procesamiento gráfico (GPUs). Originalmente enfocada en videojuegos, hoy es la columna vertebral de la revolución de la Inteligencia Artificial, proveyendo los chips esenciales para los centros de datos que entrenan y operan los modelos algorítmicos más avanzados del mundo.",
    "KO": "The Coca-Cola Company es la empresa de bebidas no alcohólicas más grande del planeta. Posee una cartera diversificada de marcas y una red de distribución global inigualable. Es considerada una acción puramente defensiva, valorada por su capacidad de trasladar la inflación a precios y su historial ininterrumpido de pago de dividendos."
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
    h1 {font-weight: 800; color: #ffffff !important; font-size: 30px !important; letter-spacing: -0.8px;}
    h2 {font-weight: 700; color: #f8fafc !important; font-size: 21px !important; margin-top: 15px;}
    h3 {font-weight: 600; color: #f1f5f9 !important; font-size: 16px !important;}
    
    div[data-testid="stRadio"] > label { display: none !important; }
    div[data-testid="stRadio"] > div { background: rgba(22, 27, 34, 0.7) !important; backdrop-filter: blur(12px) !important; padding: 8px !important; border-radius: 12px !important; border: 1px solid rgba(255, 255, 255, 0.08) !important; gap: 12px !important; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5) !important; margin-bottom: 20px !important; }
    div[data-testid="stRadio"] label[data-baseweb="radio"] { background-color: transparent !important; border: 1px solid transparent !important; padding: 8px 18px !important; border-radius: 8px !important; color: #94a3b8 !important; font-weight: 600 !important; }
    div[data-testid="stRadio"] label[data-baseweb="radio"]:hover { color: #ffffff !important; background: rgba(255, 255, 255, 0.05) !important; }
    
    div[data-testid="stMetric"] { background-color: #111520 !important; border: 1px solid #1f2937 !important; border-radius: 10px !important; padding: 15px 20px !important; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    div[data-testid="stMetric"] label { font-size: 11px !important; font-weight: 600; color: #64748b !important; text-transform: uppercase; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { font-size: 24px !important; font-weight: 800; color: #ffffff !important; }
    
    .stButton>button { width: 100%; background: linear-gradient(135deg, #2ecc71, #27ae60) !important; color: white !important; font-weight: 700; border-radius: 8px; border: none; padding: 0.6rem; font-size: 13px !important; text-transform: uppercase; }
    .stButton>button:hover { background: linear-gradient(135deg, #27ae60, #219653) !important; transform: translateY(-1px); }
    
    div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] div, div[data-testid="stNumberInput"] input, div[data-testid="stDateInput"] input { background-color: #111520 !important; color: #ffffff !important; border: 1px solid #1f2937 !important; border-radius: 8px !important; }
    
    .radar-box-gainer-high { background: linear-gradient(135deg, #064e3b, #047857); border: 1px solid #10b981; padding: 14px; border-radius: 8px; font-weight: bold; color: #34d399 !important; }
    .radar-box-loser { background: linear-gradient(135deg, #7f1d1d, #b91c1c); border: 1px solid #f87171; padding: 14px; border-radius: 8px; font-weight: bold; color: #f87171 !important; }
    .interpretation-box { background-color: #111520; padding: 16px; border-radius: 8px; font-size: 13px; color: #e2e8f0; line-height: 1.6; border: 1px solid #1f2937; border-left: 4px solid #2ecc71; margin-top: 10px; }
    .agent-box { background-color: #090d16; padding: 18px; border-radius: 8px; font-size: 13px; color: #e2e8f0; border: 1px solid #1f2937; border-left: 4px solid #dfa427; line-height: 1.6; margin-top: 10px; }
    
    .custom-table { width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 13px; background-color: #111520; border-radius: 8px; overflow: hidden; border: 1px solid #1f2937; }
    .custom-table th { background-color: #161b22; color: #ffffff; padding: 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #1f2937; position: relative; }
    .custom-table td { padding: 12px; border-bottom: 1px solid #1f2937; color: #e2e8f0; }
    .custom-table tr:hover { background-color: #1c2331; }
    .winner-cell { background-color: rgba(46, 204, 113, 0.15) !important; color: #2ecc71 !important; font-weight: bold; }
    
    .tooltip { position: relative; display: inline-block; cursor: pointer; color: #3498db; margin-left: 4px; font-weight: bold; }
    .tooltip .tooltiptext { visibility: hidden; width: 280px; background-color: #1f2937; color: #fff; text-align: left; padding: 12px; border-radius: 6px; position: absolute; z-index: 999; bottom: 125%; left: 50%; margin-left: -140px; opacity: 0; transition: opacity 0.3s; font-size: 11px; font-weight: normal; line-height: 1.4; border: 1px solid #3b82f6; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }
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

EXPLICACIONES_TECNICAS = {
    "PE": "<b>P/E (Precio sobre Ganancias):</b><br>Te dice cuántos años tardarías en recuperar la inversión si la empresa sigue ganando lo mismo siempre. Un número bajo significa que estás comprando barato.",
    "EV": "<b>EV/EBITDA:</b><br>Mide cuánto cuesta comprar la empresa entera (con deudas incluidas) en relación al efectivo limpio que genera. Si es bajo, la empresa se paga sola rápidamente.",
    "DEUDA": "<b>Deuda / EBITDA:</b><br>Compara lo que debe la empresa con lo que genera en un año. Como ver si debés 1 o 5 sueldos enteros. Valores muy altos son luz roja.",
    "LIQUIDEZ": "<b>Liquidez Corriente:</b><br>Compara el efectivo rápido que tiene la empresa contra las deudas que tiene que pagar ya mismo. Mayor a 1 significa que está tranquila.",
    "MARGEN": "<b>Margen Neto:</b><br>De cada $100 que vende la empresa, ¿cuántos billetes le quedan limpios en el bolsillo después de pagar todos los gastos e impuestos?",
    "ROE": "<b>ROE (Retorno sobre Patrimonio):</b><br>Muestra qué tan buenos son los dueños para hacer rendir la plata que invirtieron. Cuanto más alto, más jugo le sacan al capital."
}

# ==============================================================================
# 3. MOTOR YAHOOQUERY
# ==============================================================================
@st.cache_data(ttl=600)
def descargar_datos_historicos_unificados(universo):
    datos_dict = {}
    try:
        tickers_str = " ".join(universo)
        t_inst = Ticker(tickers_str, asynchronous=True)
        df_hist = t_inst.history(period="2y")
        año_actual = datetime.datetime.now().year
        fecha_ytd = f"{año_actual}-01-02"
        
        for tk in universo:
            try:
                if isinstance(df_hist.index, pd.MultiIndex) and tk in df_hist.index.levels[0]:
                    sub_df = df_hist.loc[tk].ffill().bfill()
                    serie = sub_df['adjclose'] if 'adjclose' in sub_df.columns else sub_df['close']
                    
                    if not serie.empty and len(serie) >= 30:
                        px_actual = float(serie.iloc[-1])
                        var_1d = ((px_actual / float(serie.iloc[-2])) - 1) * 100
                        var_1w = ((px_actual / float(serie.iloc[-6])) - 1) * 100
                        var_1m = ((px_actual / float(serie.iloc[-22])) - 1) * 100
                        try:
                            serie_ytd = serie.loc[fecha_ytd:]
                            var_ytd = ((px_actual / float(serie_ytd.iloc[0])) - 1) * 100 if not serie_ytd.empty else 0.0
                        except: var_ytd = 0.0
                        
                        datos_dict[tk] = {"precio": px_actual, "1D": var_1d, "1W": var_1w, "1M": var_1m, "YTD": var_ytd, "serie_completa": serie, "df_completo": sub_df}
                        continue
                datos_dict[tk] = {"precio": 100.0, "1D": 0.0, "1W": 0.0, "1M": 0.0, "YTD": 0.0, "serie_completa": pd.Series(dtype=float), "df_completo": pd.DataFrame()}
            except: datos_dict[tk] = {"precio": 100.0, "1D": 0.0, "1W": 0.0, "1M": 0.0, "YTD": 0.0, "serie_completa": pd.Series(dtype=float), "df_completo": pd.DataFrame()}
    except:
        for tk in universo: datos_dict[tk] = {"precio": 100.0, "1D": 0.0, "1W": 0.0, "1M": 0.0, "YTD": 0.0, "serie_completa": pd.Series(dtype=float), "df_completo": pd.DataFrame()}
    return datos_dict

POOL_DATA = descargar_datos_historicos_unificados(UNIVERSO_POOL)

def safe_float(val, default=0.0):
    try: return float(val) if val is not None and not pd.isna(val) else default
    except: return default

def obtener_fundamental_completo(symbol):
    try:
        t = Ticker(symbol)
        sum_det = t.summary_detail.get(symbol, {}) if isinstance(t.summary_detail, dict) else {}
        k_stats = t.key_stats.get(symbol, {}) if isinstance(t.key_stats, dict) else {}
        f_data = t.financial_data.get(symbol, {}) if isinstance(t.financial_data, dict) else {}
        p_data = t.price.get(symbol, {}) if isinstance(t.price, dict) else {}
        profile = t.summary_profile.get(symbol, {}) if isinstance(t.summary_profile, dict) else {}
        
        px = POOL_DATA.get(symbol, {}).get("precio", safe_float(p_data.get("regularMarketPrice"), 50.0))
        pe = safe_float(sum_det.get("forwardPE", sum_det.get("trailingPE", 0.0)))
        ev = safe_float(k_stats.get("enterpriseToEbitda", 0.0))
        td = safe_float(f_data.get("totalDebt", 0.0))
        caj = safe_float(f_data.get("totalCash", 0.0))
        eb = safe_float(f_data.get("ebitda", 1.0))
        liq = safe_float(f_data.get("currentRatio", 0.0))
        marg = safe_float(f_data.get("profitMargins", 0.0))
        roe = safe_float(f_data.get("returnOnEquity", 0.0))
        
        ratio_deuda = (td - caj) / eb if eb != 0 else 0.0
        
        return {
            "Ticker": symbol, "Nombre": p_data.get("longName", symbol), "Precio": px,
            "PE": pe, "EV": ev, "DEUDA": ratio_deuda, "LIQUIDEZ": liq, "MARGEN": marg, "ROE": roe,
            "RAW_INFO": profile, "REC": f_data.get("recommendationKey", "hold")
        }
    except: return None

def filtrar_peers_por_sector(ticker_raiz, lista_ingresada):
    try: sec_raiz = Ticker(ticker_raiz).summary_profile.get(ticker_raiz, {}).get("sector", "")
    except: sec_raiz = ""
    peers_validos = []
    for p in lista_ingresada:
        p_clean = p.strip().upper()
        if not p_clean: continue
        try:
            sec_p = Ticker(p_clean).summary_profile.get(p_clean, {}).get("sector", "")
            if sec_p == sec_raiz or not sec_raiz: peers_validos.append(p_clean)
        except: peers_validos.append(p_clean)
    return peers_validos

# ==============================================================================
# CARTERA E INTERFAZ
# ==============================================================================
if "cartera_list_v4" not in st.session_state:
    st.session_state.cartera_list_v4 = [
        {"Ticker": "VIST", "Nominales": 100, "Fecha_Compra": datetime.date(2025, 6, 15), "Costo_Unitario_Cedear": 77200.0, "Comision_USD": 0.5, "Impuesto_USD": 0.1, "Dividendos_Edit": 0.0},
        {"Ticker": "XOM", "Nominales": 50, "Fecha_Compra": datetime.date(2025, 8, 10), "Costo_Unitario_Cedear": 31500.0, "Comision_USD": 0.4, "Impuesto_USD": 0.05, "Dividendos_Edit": 0.0}
    ]

menu = st.radio("Secciones operativas:", ["🌐 DASHBOARD Y WATCHLIST", "🔍 ANÁLISIS INTEGRAL", "💼 PORTAFOLIO Y MODELOS"], horizontal=True)
st.markdown("---")

# ------------------------------------------------------------------------------
# DASHBOARD
# ------------------------------------------------------------------------------
if menu == "🌐 DASHBOARD Y WATCHLIST":
    st.subheader("⚡ Market Radar: Momentum de Ruedas")
    ordenados = sorted(POOL_DATA.items(), key=lambda x: x[1]["1D"], reverse=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='radar-box-gainer-high'>🟢 Liderando la Rueda<br><br>• {ordenados[0][0]}: {ordenados[0][1]['1D']:+.2f}%</div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='radar-box-loser'>🔴 Mayor Compresión<br><br>• {ordenados[-1][0]}: {ordenados[-1][1]['1D']:+.2f}%</div>", unsafe_allow_html=True)
    with c3: st.markdown("<div class='radar-box-gainer-high'>🚀 Impulso Factorial Continuo<br><br>• VIST: Flujo en Expansión</div>", unsafe_allow_html=True)
    with c4: st.markdown("<div class='radar-box-loser'>📉 Compresión de Margen<br><br>• KO: Estructura de Resguardo</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("📌 Monitoreo General del Mercado (Watchlist Histórica Recompuesta)")
    watchlist_items = ["VIST", "YPF", "AAPL", "GGAL", "NVDA", "KO", "XOM", "WMT"]
    rows_w = []
    for t in watchlist_items:
        p_info = POOL_DATA.get(t, {"precio": 100.0, "1D": 0.0, "1W": 0.0, "1M": 0.0, "YTD": 0.0})
        px_ars = (p_info["precio"] / RATIOS_CEDEAR.get(t, 1)) * DOLAR_MEP
        rows_w.append({"Ticker": t, "Precio Subyacente": f"${p_info['precio']:.2f} USD", "Cedear Estimado (ARS)": f"${px_ars:,.2f} ARS", "Retorno Diario (1D)": f"{p_info['1D']:+.2f}%", "Última Semana (1W)": f"{p_info['1W']:+.2f}%", "Último Mes (1M)": f"{p_info['1M']:+.2f}%", "Año a la Fecha (YTD)": f"{p_info['YTD']:+.2f}%"})
    st.dataframe(pd.DataFrame(rows_w).set_index("Ticker"), use_container_width=True)

# ------------------------------------------------------------------------------
# ANÁLISIS INTEGRAL
# ------------------------------------------------------------------------------
elif menu == "🔍 ANÁLISIS INTEGRAL":
    c_s1, c_s2 = st.columns([1, 2])
    t_obj = c_s1.text_input("📍 Activo Bajo Estudio:", value="VIST").upper().strip()
    t_comp_raw = c_s2.text_input("Peers de Control (Separados por coma):", value="YPF, XOM").upper()
    
    if st.button("🔥 Correr Análisis"):
        with st.spinner("Descargando balances corporativos reales en vivo..."):
            raw_peers = [c.strip() for c in t_comp_raw.split(",") if c.strip()]
            peers_filtrados = filtrar_peers_por_sector(t_obj, raw_peers)
            lista_tickers = [t_obj] + peers_filtrados
            
            dataset = []
            info_obj = {}
            for tk in lista_tickers:
                res_f = obtener_fundamental_completo(tk)
                if res_f:
                    dataset.append(res_f)
                    if tk == t_obj: info_obj = res_f
            
            if dataset:
                tab_fund, tab_tech, tab_mc = st.tabs(["📊 Análisis Fundamental", "📈 Análisis Técnico (DMI)", "🎲 Simulación Montecarlo Dual"])
                
                # --- PESTAÑA 1: FUNDAMENTAL ---
                with tab_fund:
                    st.markdown("### 🏢 ¿A qué se dedica esta empresa?")
                    desc_raw = info_obj.get("RAW_INFO", {}).get("longBusinessSummary", "")
                    
                    if not desc_raw:
                        desc_final = FALLBACK_SUMMARIES.get(t_obj, f"{t_obj} es una empresa que opera en el sector {info_obj.get('RAW_INFO', {}).get('sector', 'financiero/industrial')}. Los datos descriptivos profundos no están disponibles públicamente en este momento.")
                    else:
                        if HAS_TRANSLATOR:
                            try: desc_final = GoogleTranslator(source='en', target='es').translate(desc_raw)
                            except: desc_final = FALLBACK_SUMMARIES.get(t_obj, desc_raw + "\n*(Servicio de traducción temporalmente saturado)*")
                        else: desc_final = FALLBACK_SUMMARIES.get(t_obj, desc_raw + "\n*(Aviso: Instalar deep-translator para ver en español)*")
                    
                    st.info(desc_final)
                    
                    col_rel, col_caja = st.columns([1, 2])
                    with col_rel:
                        st.markdown("#### ¿Qué opina Wall Street?")
                        recom = str(info_obj.get("REC", "hold")).lower()
                        val = 5 if "strong buy" in recom else 4 if "buy" in recom else 2 if "sell" in recom else 3
                        fig_g = go.Figure(go.Indicator(mode="gauge+number", value=val, title={'text': "Consenso", 'font': {'size': 14}}, gauge={'axis': {'range': [1, 5], 'tickvals': [1,2,3,4,5], 'ticktext': ['Venta F.','Venta','Mantener','Compra','Compra F.']}, 'bar': {'color': "#ffffff"}, 'steps': [{'range': [1, 2.5], 'color': "#7f1d1d"}, {'range': [2.5, 3.5], 'color': "#111520"}, {'range': [3.5, 5], 'color': "#064e3b"}]}))
                        fig_g.update_layout(height=220, margin=dict(l=10,r=10,t=30,b=10), paper_bgcolor='#111520', font={'color': '#ffffff'})
                        st.plotly_chart(fig_g, use_container_width=True)
                        
                    with col_caja:
                        st.markdown("#### 🎁 Caja de Sorpresas: Últimos 4 Trimestres")
                        try:
                            q_fin = Ticker(t_obj).income_statement(frequency="q").iloc[-4:]
                            if not q_fin.empty and 'TotalRevenue' in q_fin.columns and 'NetIncome' in q_fin.columns:
                                labels = [p.strftime('%d-%m-%Y') if hasattr(p, 'strftime') else str(p) for p in q_fin.get('asOfDate', ["T-4", "T-3", "T-2", "T-1"])]
                                rev_vals = q_fin['TotalRevenue'].values / 1e9
                                net_vals = q_fin['NetIncome'].values / 1e9
                                fig_c = go.Figure(data=[go.Bar(name='Ingresos (Billion USD)', x=labels, y=rev_vals, marker_color='#3498db'), go.Bar(name='Plata Limpia (Billion USD)', x=labels, y=net_vals, marker_color='#2ecc71')])
                                fig_c.update_layout(barmode='group', template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', height=200, margin=dict(l=10,r=10,t=10,b=20))
                                st.plotly_chart(fig_c, use_container_width=True)
                            else: st.warning("Yahoo Finance bloqueó temporalmente el acceso a los datos trimestrales.")
                        except: st.warning("Estructura de balances no disponible temporalmente.")
                    
                    st.markdown("---")
                    st.markdown("#### Matriz de Comparación (Frente a sus competidores)")
                    g_pe = min(dataset, key=lambda x: x["PE"] if x["PE"] > 0 else float('inf'))["Ticker"]
                    g_roe = max(dataset, key=lambda x: x["ROE"])["Ticker"]
                    
                    html_tb = "<table class='custom-table'><thead><tr><th>Ticker</th><th>Razón Social</th>"
                    html_tb += f"<th>Precio/Ganancia (PE) <div class='tooltip'>ⓘ<span class='tooltiptext'>{EXPLICACIONES_TECNICAS['PE']}</span></div></th>"
                    html_tb += f"<th>Costo Empresa (EV) <div class='tooltip'>ⓘ<span class='tooltiptext'>{EXPLICACIONES_TECNICAS['EV']}</span></div></th>"
                    html_tb += f"<th>Nivel de Deuda <div class='tooltip'>ⓘ<span class='tooltiptext'>{EXPLICACIONES_TECNICAS['DEUDA']}</span></div></th>"
                    html_table += f"<th>Respaldo Efectivo <div class='tooltip'>ⓘ<span class='tooltiptext'>{EXPLICACIONES_TECNICAS['LIQUIDEZ']}</span></div></th>"
                    html_table += f"<th>Margen de Ganancia <div class='tooltip'>ⓘ<span class='tooltiptext'>{EXPLICACIONES_TECNICAS['MARGEN']}</span></div></th>"
                    html_table += f"<th>Retorno a Dueños <div class='tooltip'>ⓘ<span class='tooltiptext'>{EXPLICACIONES_TECNICAS['ROE']}</span></div></th></tr></thead><tbody>"
                    
                    for r in dataset:
                        html_tb += f"<tr><td><b>{r['Ticker']}</b></td><td>{r['Nombre']}</td><td {'class=winner-cell' if r['Ticker']==g_pe else ''}>{r['PE']:.2f}</td><td>{r['EV']:.2f}</td><td>{r['DEUDA']:.2f}x</td><td>{r['LIQUIDEZ']:.2f}x</td><td>{r['MARGEN']*100:.1f}%</td><td {'class=winner-cell' if r['Ticker']==g_roe else ''}>{r['ROE']*100:.1f}%</td></tr>"
                    html_tb += "</tbody></table>"
                    st.markdown(html_tb, unsafe_allow_html=True)
                    
                    st.markdown("### 📊 Conclusión de Inversión (Sencilla)")
                    st.markdown(f"<div class='interpretation-box'><b>¿Qué nos dicen los números?</b> Comparando con sus rivales, <strong>{g_roe}</strong> es la que mejor hace rendir la plata que tiene invertida. Por otro lado, si miramos qué tan barata está la acción hoy en relación a lo que gana, <strong>{g_pe}</strong> parece ser la mejor oferta en vitrina. Es un buen momento para sumar <strong>{t_obj}</strong> a la cartera si estás cómodo con su nivel de deudas actual.</div>", unsafe_allow_html=True)
                    
                    st.markdown("### 🐾 Datos Relevantes para no olvidar (El Sabueso)")
                    st.markdown(f"<div class='agent-box'><strong>🟢 Puntos a favor (Por qué subiría):</strong><br>• <b>Infraestructura y Venta:</b> Lograron acuerdos clave para que sus productos lleguen más rápido a los clientes que pagan mejor.<br>• <b>Protección del dinero:</b> Acuerdos en moneda fuerte, minimizando el impacto de devaluaciones locales.<br><br><strong>🔴 Puntos en contra (Por qué podría caer):</strong><br>• <b>Trabas de gobierno:</b> Al trabajar en mercados emergentes, sufren normativas trabadas para giros al exterior o regulaciones cambiarias.<br>• <b>Depende de otros:</b> Tienen dependencia de la logística troncal (midstream) operada por terceros.</div>", unsafe_allow_html=True)

                # --- PESTAÑA 2: TÉCNICO ---
                with tab_tech:
                    st.markdown(f"### 📈 El pulso del mercado (Gráfico DMI): {t_obj}")
                    st.markdown("**¿Cómo leer este gráfico fácilmente?**<br>* **Línea Verde (+DI - Fuerza Compradora):** Mide la motivación de compra. Si supera a la roja, compradores al mando.<br>* **Línea Roja (-DI - Fuerza Vendedora):** Mide la presión de venta. Si supera a la verde, pánico o toma de ganancias.<br>* **Línea Azul (ADX - Fuerza de Tendencia):** Te dice si el movimiento va en serio. Sobre 25 puntos, tendencia muy sólida.", unsafe_allow_html=True)
                    
                    df_t = POOL_DATA.get(t_obj, {}).get("df_completo", pd.DataFrame())
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
                        
                        fig_dmi = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.65, 0.35], vertical_spacing=0.04)
                        fig_dmi.add_trace(go.Scatter(x=df_t.index, y=df_t['close'], name="Precio Cierre", line=dict(color='#ffffff', width=2)), row=1, col=1)
                        fig_dmi.add_trace(go.Scatter(x=df_t.index, y=df_t['EMA30'], name="Promedio 30 días", line=dict(color='#f1c40f', dash='dash')), row=1, col=1)
                        fig_dmi.add_trace(go.Scatter(x=df_t.index, y=df_t['+DI'], name="+DI (Verde = Compras)", line=dict(color='#2ecc71')), row=2, col=1)
                        fig_dmi.add_trace(go.Scatter(x=df_t.index, y=df_t['-DI'], name="-DI (Rojo = Ventas)", line=dict(color='#e74c3c')), row=2, col=1)
                        fig_dmi.add_trace(go.Scatter(x=df_t.index, y=df_t['ADX'], name="ADX (Azul = Fuerza)", line=dict(color='#3498db')), row=2, col=1)
                        fig_dmi.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', height=450, margin=dict(l=20,r=20,t=10,b=10))
                        st.plotly_chart(fig_dmi, use_container_width=True)
                        
                        p, di_p, di_m, adx = df_t['close'].iloc[-1], df_t['+DI'].iloc[-1], df_t['-DI'].iloc[-1], df_t['ADX'].iloc[-1]
                        dom = "los COMPRADORES" if di_p > di_m else "los VENDEDORES"
                        tend = "con muchísimo impulso y tendencia clara." if adx > 25 else "pero el mercado está dudoso y lateral (sin rumbo)."
                        st.markdown(f"<div class='interpretation-box'><strong>¿QUIÉN TIENE EL VOLANTE HOY?</strong> Al precio actual de <b>${p:.2f} USD</b>, la fuerza compradora se encuentra en {di_p:.1f} puntos, frente a una fuerza vendedora de {di_m:.1f} puntos. Esto nos indica que actualmente <b>{dom}</b> tienen el control total del precio, {tend}</div>", unsafe_allow_html=True)
                    else: st.error("No hay suficientes datos en la bolsa para armar este gráfico hoy.")

                # --- PESTAÑA 3: MONTECARLO ---
                with tab_mc:
                    st.markdown("### 🎲 La Máquina del Tiempo (Simulador de Escenarios)")
                    st.markdown("**¿Qué es esto?** Tiramos los dados 100 veces para ver qué podría pasar con el precio, basándonos pura y exclusivamente en cómo se movió en el último año.")
                    serie_mc = POOL_DATA.get(t_obj, {}).get("serie_completa", pd.Series())
                    
                    if not serie_mc.empty and len(serie_mc) > 50:
                        ret = serie_mc.pct_change().dropna()
                        mu, sigma, p_b = ret.mean(), ret.std(), serie_mc.iloc[-1]
                        c1, c2 = st.columns(2)
                        
                        with c1:
                            st.markdown("#### Corto Plazo: ¿Qué pasará en 30 días?")
                            m_1m = np.zeros((30, 100))
                            m_1m[0] = p_b
                            for t in range(1, 30): m_1m[t] = m_1m[t-1] * np.exp((mu - 0.5 * sigma**2) + sigma * np.random.standard_normal(100))
                            f1m = go.Figure()
                            for i in range(40): f1m.add_trace(go.Scatter(y=m_1m[:, i], mode='lines', line=dict(color='rgba(52, 152, 219, 0.08)'), showlegend=False))
                            f1m.add_trace(go.Scatter(y=np.mean(m_1m, axis=1), mode='lines', name="Evolución Normal (Promedio)", line=dict(color='#2ecc71', width=2.5)))
                            f1m.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', height=300, margin=dict(l=10,r=10,t=10,b=10))
                            st.plotly_chart(f1m, use_container_width=True)
                            pe, pdn, pup = np.mean(m_1m[-1, :]), np.percentile(m_1m[-1, :], 5), np.percentile(m_1m[-1, :], 95)
                            st.markdown(f"<div class='agent-box' style='border-left: 4px solid #2ecc71;'><b>Traducción Sencilla:</b> Teniendo en cuenta el escenario vanilla (que mantenga la misma inercia), el <b>Precio Justo a 30 días</b> es <b>${pe:.2f} USD</b>. Si la bolsa se dispara, podría escalar a <b>${pup:.2f} USD</b>. Si entran en pánico, el piso es <b>${pdn:.2f} USD</b>.</div>", unsafe_allow_html=True)
                        
                        with c2:
                            st.markdown("#### Largo Plazo: ¿Qué pasará en 1 año (252 días)?")
                            m_1y = np.zeros((252, 100))
                            m_1y[0] = p_b
                            for t in range(1, 252): m_1y[t] = m_1y[t-1] * np.exp((mu - 0.5 * sigma**2) + sigma * np.random.standard_normal(100))
                            f1y = go.Figure()
                            for i in range(40): f1y.add_trace(go.Scatter(y=m_1y[:, i], mode='lines', line=dict(color='rgba(155, 89, 182, 0.08)'), showlegend=False))
                            f1y.add_trace(go.Scatter(y=np.mean(m_1y, axis=1), mode='lines', name="Evolución Normal (Promedio)", line=dict(color='#9b59b6', width=2.5)))
                            f1y.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', height=300, margin=dict(l=10,r=10,t=10,b=10))
                            st.plotly_chart(f1y, use_container_width=True)
                            pe_y, pdn_y, pup_y = np.mean(m_1y[-1, :]), np.percentile(m_1y[-1, :], 5), np.percentile(m_1y[-1, :], 95)
                            st.markdown(f"<div class='agent-box' style='border-left: 4px solid #9b59b6;'><b>Traducción Sencilla:</b> A un año, el <b>Precio Justo Esperado</b> escala a <b>${pe_y:.2f} USD</b>. Si tenemos un súper año alcista de suerte, la matemática avala los <b>${pup_y:.2f} USD</b>. Por el contrario, un mercado en recesión arrastraría el activo hasta los <b>${pdn_y:.2f} USD</b>.</div>", unsafe_allow_html=True)
            else: st.error("No se pudo construir la matriz de datos por demoras en Yahoo Finance.")

# ------------------------------------------------------------------------------
# PORTAFOLIO Y MODELOS (Restaurado completo)
# ------------------------------------------------------------------------------
elif menu == "💼 PORTAFOLIO Y MODELOS":
    st.subheader("🤖 Modelos Factoriales (Asignación Táctica)")
    
    FACTORES = {
        "Dividend Income (Flujo Defensivo)": {"desc": "Capturar firmas maduras con distribución predecible.", "activos": {"KO": "Resiliencia de consumo.", "XOM": "Protección energética.", "JNJ": "Sector salud inelástico.", "PEP": "Consumo masivo.", "PG": "Higiene y precios.", "WMT": "Retail defensivo.", "MCD": "Franquicia global."}},
        "Institutional Momentum (Inercia de Tendencia)": {"desc": "Replicar la inercia de compras institucionales.", "activos": {"VIST": "Aceleración en Vaca Muerta.", "NVDA": "Escalamiento en IA.", "MSFT": "SaaS integrado en nube.", "AAPL": "Ecosistema cerrado.", "AMD": "Procesamiento gráfico.", "META": "Conversión publicitaria."}},
        "Large Caps Alpha (Líderes de Mercado Core)": {"desc": "Consolidar el núcleo del portafolio.", "activos": {"MSFT": "Monopolio moderno integrado.", "AAPL": "Estructura de caja colosal.", "AMZN": "Líder en infraestructura cloud.", "GOOGL": "Foso de mercado insuperable.", "BRKB": "El holding más conservador."}},
        "Small & Mid Caps Growth (Expansión Temprana)": {"desc": "Compañías en fase de expansión temprana o nichos.", "activos": {"MELI": "Líder indiscutido en LATAM.", "PAMP": "Generación eléctrica y gas.", "TSLA": "Líder en transición energética.", "NFLX": "Escala global en streaming.", "VALE": "Gigante minero base."}}
    }
    
    cat_sel = st.selectbox("Estrategia Factorial a Evaluar:", list(FACTORES.keys()))
    st.markdown(f"**Objetivo del Factor:** *{FACTORES[cat_sel]['desc']}*")
    
    col1, col2 = st.columns([2, 1])
    tk_ele = col1.selectbox("Seleccionar activo sugerido para auditar:", list(FACTORES[cat_sel]["activos"].keys()))
    col1.markdown(f"💡 **Fundamento:** {FACTORES[cat_sel]['activos'][tk_ele]}")
    
    if col2.button("➕ ACOPLAR A MI CARTERA"):
        if not any(x["Ticker"] == tk_ele for x in st.session_state.cartera_list_v4):
            px_sub = POOL_DATA.get(tk_ele, {}).get("precio", 150.0)
            ratio = RATIOS_CEDEAR.get(tk_ele, 1)
            px_cedear = (px_sub / ratio) * DOLAR_MEP
            st.session_state.cartera_list_v4.append({"Ticker": tk_ele, "Nominales": 10, "Fecha_Compra": datetime.date(2025, 1, 2), "Costo_Unitario_Cedear": round(px_cedear, 2), "Comision_USD": 0.5, "Impuesto_USD": 0.05, "Dividendos_Edit": 0.0})
            st.success(f"Inyectado {tk_ele} en la plantilla.")
            st.rerun()

    st.markdown("---")
    st.subheader("💼 Mi Cartera de Inversiones Consolidada (Plaza BYMA)")
    is_ars = st.segmented_control("Moneda de Muestreo:", ["PESOS ARGENTINOS (ARS)", "DÓLARES SUBYACENTES (USD)"], default="PESOS ARGENTINOS (ARS)") == "PESOS ARGENTINOS (ARS)"
    
    with st.expander("➕ Cargar nueva posición manualmente"):
        with st.form("alta_manual"):
            cx1, cx2, cx3 = st.columns(3)
            ins_tk = cx1.text_input("Ticker Activo:", value="AAPL").upper().strip()
            ins_nom = cx2.number_input("Cantidad CEDEARs:", min_value=1, value=10)
            ins_date = cx3.date_input("Fecha Compra:", value=datetime.date(2025,1,15))
            cx4, cx5, cx6 = st.columns(3)
            ins_px = cx4.number_input("Precio pagado (ARS):", value=25000.0)
            ins_com = cx5.number_input("Comisión Bróker (USD):", value=0.5)
            ins_imp = cx6.number_input("Impuestos (USD):", value=0.1)
            if st.form_submit_button("➕ INTEGRAR OPERACIÓN"):
                st.session_state.cartera_list_v4.append({"Ticker": ins_tk, "Nominales": ins_nom, "Fecha_Compra": ins_date, "Costo_Unitario_Cedear": ins_px, "Comision_USD": ins_com, "Impuesto_USD": ins_imp, "Dividendos_Edit": 0.0})
                st.success("Posición cargada.")
                st.rerun()

    df_in = pd.DataFrame(st.session_state.cartera_list_v4)
    if not df_in.empty:
        df_ed = st.data_editor(df_in, column_config={"Ticker": st.column_config.TextColumn(disabled=True), "Nominales": st.column_config.NumberColumn(disabled=True), "Fecha_Compra": st.column_config.DateColumn(disabled=True), "Costo_Unitario_Cedear": st.column_config.NumberColumn("Precio Compra (ARS)", disabled=True), "Comision_USD": st.column_config.NumberColumn(disabled=True), "Impuesto_USD": st.column_config.NumberColumn(disabled=True), "Dividendos_Edit": st.column_config.NumberColumn("Dividendos Devengados (USD)", disabled=False)}, use_container_width=True, hide_index=True)
        st.session_state.cartera_list_v4 = df_ed.to_dict(orient="records")
        
        filas_html, filas_pdf, filas_cf = [], [], []
        c_tot_u, m_tot_u, d_tot_u, cf_tot_u = 0.0, 0.0, 0.0, 0.0
        
        for p in st.session_state.cartera_list_v4:
            t, n, px_c, co, im, dv = p["Ticker"], p["Nominales"], p["Costo_Unitario_Cedear"], p["Comision_USD"], p["Impuesto_USD"], p["Dividendos_Edit"]
            ratio = RATIOS_CEDEAR.get(t, 1)
            px_sub = POOL_DATA.get(t, {"precio": (px_c * ratio) / DOLAR_MEP})["precio"]
            costo_usd = ((n * px_c) / DOLAR_MEP) * ratio + co + im
            val_usd = n * px_sub
            pl_usd = (val_usd + dv) - costo_usd
            pl_pct = (pl_usd / costo_usd) * 100 if costo_usd > 0 else 0.0
            cf_proy = 0.0 # Placeholder
            
            c_tot_u += costo_usd; m_tot_u += val_usd; d_tot_u += dv; cf_tot_u += cf_proy
            
            if is_ars:
                f_costo, f_actual, f_div, f_pl, f_cf = costo_usd * DOLAR_MEP / ratio, val_usd * DOLAR_MEP / ratio, dv * DOLAR_MEP / ratio, pl_usd * DOLAR_MEP / ratio, cf_proy * DOLAR_MEP / ratio
                simb, lbl_px, px_vis = "ARS", "Precio CEDEAR ARS", px_c
            else:
                f_costo, f_actual, f_div, f_pl, f_cf = costo_usd, val_usd, dv, pl_usd, cf_proy
                simb, lbl_px, px_vis = "USD", "Precio Subyacente USD", px_sub
                
            filas_html.append({"Ticker": t, "Cantidad": n, "Ratio": f"{ratio}:1", lbl_px: f"${px_vis:,.2f}", f"Capital ({simb})": f"${f_costo:,.2f}", f"Mercado ({simb})": f"${f_actual:,.2f}", f"Rentas ({simb})": f"${f_div:,.2f}", f"P&L ({simb})": f"${f_pl:,.2f}", "Retorno (%)": f"{pl_pct:+.2f}%"})
            filas_pdf.append({"Ticker": t, "Cantidad": n, "Ratio": f"{ratio}:1", "Precio": f"${px_vis:,.2f}", "Mercado": f"${f_actual:,.2f}", "PL": f"{pl_pct:+.2f}%"})
            filas_cf.append({"Ticker": t, "Cantidad": n, "Ratio": f"{ratio}:1", "Flujo": f"${f_cf:,.2f} {simb}"})
            
        st.dataframe(pd.DataFrame(filas_html).set_index("Ticker"), use_container_width=True)
        
        st.markdown("### 📈 Estado Neto Patrimonial")
        k1, k2, k3, k4 = st.columns(4)
        gp = ((m_tot_u + d_tot_u - c_tot_u) / c_tot_u) * 100 if c_tot_u > 0 else 0.0
        if is_ars:
            k1.metric("Capital Invertido", f"${(c_tot_u * DOLAR_MEP):,.2f} ARS")
            k2.metric("Valuación Mercado", f"${(m_tot_u * DOLAR_MEP):,.2f} ARS")
            k3.metric("Bolsa Rentas", f"${(d_tot_u * DOLAR_MEP):,.2f} ARS")
            k4.metric("Total Return", f"${((m_tot_u + d_tot_u - c_tot_u) * DOLAR_MEP):,.2f} ARS ({gp:+.2f}%)")
        else:
            k1.metric("Capital Invertido", f"${c_tot_u:,.2f} USD")
            k2.metric("Valuación Mercado", f"${m_tot_u:,.2f} USD")
            k3.metric("Bolsa Rentas", f"${d_tot_u:,.2f} USD")
            k4.metric("Total Return", f"${(m_tot_u + d_tot_u - c_tot_u):,.2f} USD ({gp:+.2f}%)")

        st.markdown("---")
        st.subheader("📐 Benchmarking Institucional")
        bench_sel = st.selectbox("Benchmark:", ["SPY", "QQQ", "DIA"])
        fechas_c = pd.date_range(start="2025-06-01", end=datetime.date.today(), freq="B")
        curva_p = pd.Series(0.0, index=fechas_c)
        for pos in st.session_state.cartera_list_v4:
            serie_tk = POOL_DATA.get(pos["Ticker"], {}).get("serie_completa", pd.Series(dtype=float))
            if not serie_tk.empty: curva_p = curva_p.add(serie_tk.reindex(fechas_c).ffill().bfill(), fill_value=0)
        curva_p = curva_p.dropna()
        if not curva_p.empty:
            curva_p = (curva_p / curva_p.iloc[0]) * 100
            s_bench = POOL_DATA.get(bench_sel, {}).get("serie_completa", pd.Series(dtype=float))
            curva_b = (s_bench.reindex(curva_p.index).ffill().bfill() / s_bench.reindex(curva_p.index).ffill().bfill().iloc[0]) * 100 if not s_bench.empty else curva_p * 0.94
            fig_b = go.Figure()
            fig_b.add_trace(go.Scatter(x=curva_p.index, y=curva_p.values, name="Mi Cuenta", line=dict(color='#2ecc71', width=3)))
            fig_b.add_trace(go.Scatter(x=curva_b.index, y=curva_b.values, name=f"Benchmark {bench_sel}", line=dict(color='#3498db', width=2, dash='dash')))
            fig_b.update_layout(template="plotly_dark", paper_bgcolor='#111520', plot_bgcolor='#0c0f16', height=380, margin=dict(l=20,r=20,t=30,b=20))
            st.plotly_chart(fig_b, use_container_width=True)

# ==============================================================================
# PIE DE PÁGINA
# ==============================================================================
st.markdown("---")
st.markdown("<p style='text-align: right; font-size: 12px; color: #2ecc71; font-weight: 600;'>Facundo Garcia Marquez | Terminal Quanti Pro</p>", unsafe_allow_html=True)
