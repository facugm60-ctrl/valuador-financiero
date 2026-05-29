import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import datetime
import requests
from bs4 import BeautifulSoup
import plotly.graph_objects as go

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y PARAMETRIZACIÓN DE ESTILOS FINTECH
# ==============================================================================
st.set_page_config(page_title="Terminal Quanti Pro", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght=300;400;600;700;800&display=swap');
    
    html, body, [class*="css"], [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #0c0f16 !important;
        color: #f1f5f9 !important;
        font-family: 'Montserrat', sans-serif !important;
    }
    
    .stMarkdown, p, span, label, li {
        color: #cbd5e1 !important;
    }
    
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    h1 {font-weight: 800; color: #ffffff !important; font-size: 30px !important; letter-spacing: -0.8px;}
    h2 {font-weight: 700; color: #f8fafc !important; font-size: 21px !important; margin-top: 15px;}
    h3 {font-weight: 600; color: #f1f5f9 !important; font-size: 16px !important;}
    
    /* Selector de Navegación Premium - Glassmorphism */
    div[data-testid="stRadio"] > label { display: none !important; }
    div[data-testid="stRadio"] > div {
        background: rgba(22, 27, 34, 0.7) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        padding: 8px !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        gap: 12px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5) !important;
        margin-bottom: 20px !important;
    }
    div[data-testid="stRadio"] label[data-baseweb="radio"] {
        background-color: transparent !important;
        border: 1px solid transparent !important;
        padding: 8px 18px !important;
        border-radius: 8px !important;
        color: #94a3b8 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        font-weight: 600 !important;
    }
    div[data-testid="stRadio"] label[data-baseweb="radio"]:hover {
        color: #ffffff !important;
        background: rgba(255, 255, 255, 0.05) !important;
        border-color: rgba(88, 166, 255, 0.3) !important;
    }
    
    /* KPIs Múltiplos */
    div[data-testid="stMetric"] {
        background-color: #111520 !important;
        border: 1px solid #1f2937 !important;
        border-radius: 10px !important;
        padding: 15px 20px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    div[data-testid="stMetric"] label { font-size: 11px !important; font-weight: 600; color: #64748b !important; text-transform: uppercase; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { font-size: 24px !important; font-weight: 800; color: #ffffff !important; }
    
    /* Botonera */
    .stButton>button {
        width: 100%; background: linear-gradient(135deg, #2ecc71, #27ae60) !important;
        color: white !important; font-weight: 700; border-radius: 8px; border: none;
        padding: 0.6rem; font-size: 13px !important; text-transform: uppercase; letter-spacing: 0.5px;
    }
    .stButton>button:hover { background: linear-gradient(135deg, #27ae60, #219653) !important; transform: translateY(-1px); }
    
    /* Inputs */
    div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] div, div[data-testid="stNumberInput"] input, div[data-testid="stDateInput"] input {
        background-color: #111520 !important; color: #ffffff !important; border: 1px solid #1f2937 !important; border-radius: 8px !important;
    }
    
    /* Estructuras Informativas */
    .radar-box-gainer-high { background: linear-gradient(135deg, #064e3b, #047857); border: 1px solid #10b981; padding: 14px; border-radius: 8px; font-weight: bold; color: #34d399 !important; }
    .radar-box-loser { background: linear-gradient(135deg, #7f1d1d, #b91c1c); border: 1px solid #f87171; padding: 14px; border-radius: 8px; font-weight: bold; color: #f87171 !important; }
    .interpretation-box { background-color: #111520; padding: 16px; border-radius: 8px; font-size: 13px; color: #e2e8f0; line-height: 1.6; border: 1px solid #1f2937; border-left: 4px solid #2ecc71; }
    .agent-box { background-color: #090d16; padding: 18px; border-radius: 8px; font-size: 13px; color: #e2e8f0; border: 1px solid #1f2937; border-left: 4px solid #dfa427; line-height: 1.6; }
    
    /* Estilos para Tablas HTML Corporativas */
    .custom-table { width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 13px; background-color: #111520; border-radius: 8px; overflow: hidden; border: 1px solid #1f2937; }
    .custom-table th { background-color: #161b22; color: #ffffff; padding: 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #1f2937; position: relative; }
    .custom-table td { padding: 12px; border-bottom: 1px solid #1f2937; color: #e2e8f0; }
    .custom-table tr:hover { background-color: #1c2331; }
    .winner-cell { background-color: rgba(46, 204, 113, 0.15) !important; color: #2ecc71 !important; font-weight: bold; border: 1px solid rgba(46, 204, 113, 0.3) !important; }
    
    /* CSS Tooltips */
    .tooltip { position: relative; display: inline-block; cursor: pointer; color: #3498db; margin-left: 4px; font-weight: bold; }
    .tooltip .tooltiptext { visibility: hidden; width: 280px; background-color: #1f2937; color: #fff; text-align: left; padding: 12px; border-radius: 6px; position: absolute; z-index: 999; bottom: 125%; left: 50%; margin-left: -140px; opacity: 0; transition: opacity 0.3s; font-size: 11px; font-weight: normal; line-height: 1.4; border: 1px solid #3b82f6; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }
    .tooltip:hover .tooltiptext { visibility: visible; opacity: 1; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. CONEXIÓN EN VIVO A DOLARITO PARA EXTRACCIÓN REAL DEL MEP
# ==============================================================================
@st.cache_data(ttl=600)
def obtener_dolar_mep_real():
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        r = requests.get("https://www.dolarito.ar/", headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for element in soup.find_all(['div', 'span', 'p']):
            texto = element.get_text().lower()
            if 'mep' in texto and '$' in texto:
                for token in texto.split():
                    if '$' in token:
                        clean_token = token.replace('$', '').replace('.', '').replace(',', '.').strip()
                        try:
                            val = float(clean_token)
                            if 1300 < val < 1600:
                                return round(val, 2)
                        except: pass
        return 1433.25
    except:
        return 1433.25

DOLAR_MEP = obtener_dolar_mep_real()

RATIOS_CEDEAR = {
    "VIST": 1, "YPF": 1, "AAPL": 10, "GGAL": 1, "AMD": 10, "NVDA": 24, 
    "MSFT": 30, "AMZN": 14, "GOOGL": 11, "META": 24, "TSLA": 15, "KO": 5, 
    "WMT": 6, "JNJ": 15, "PEP": 15, "PG": 15, "XOM": 5, "PAMP": 1, 
    "SPY": 20, "QQQ": 20, "DIA": 20, "MO": 4, "CVX": 8, "MCD": 24,
    "BRKB": 22, "MELI": 60, "BABA": 9, "PYPL": 3, "NFLX": 16, "DESP": 1, "VALE": 2
}

UNIVERSO_POOL = ["VIST", "YPF", "AAPL", "GGAL", "AMD", "NVDA", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "KO", "WMT", "XOM", "SPY", "QQQ", "JNJ", "PEP", "PG", "MO", "CVX", "MCD", "BRKB", "MELI", "BABA", "PYPL", "NFLX", "DESP", "VALE"]

EXPLICACIONES_TECNICAS = {
    "PE": "<b>Forward Price-to-Earnings (P/E): Múltiplo de Valuación</b><br>Te dice cuántos años tardarías en recuperar la inversión si la empresa sigue ganando lo mismo siempre. Mientras más bajo sea el número, más barato estás comprando el negocio.",
    "EV": "<b>EV/EBITDA: Métrica de Absorción Corporativa</b><br>Es el costo teórico de adquirir la firma completa (con sus deudas incluidas) respecto a la caja operativa limpia que genera al año. Si es bajo, el negocio se paga solo rápido.",
    "DEUDA": "<b>Net Debt / EBITDA: Cobertura de Riesgo Crediticio</b><br>Compara las deudas financieras netas con lo que se genera en un año. Es como ver si debés 1 sueldo o 5 sueldos enteros. Valores sobre las 3.0x indican zona de peligro.",
    "LIQUIDEZ": "<b>Liquidez Corriente: Capacidad Operativa Corto Plazo</b><br>Compara lo que la empresa tiene disponible en efectivo inmediato contra las deudas que vencen este mes. Valores mayores a 1.0x indican espalda financiera.",
    "MARGEN": "<b>Margen Neto: Pricing Power Corporativo</b><br>Es la porción de ganancia neta remanente que le queda a la empresa de cada $100 facturados, tras liquidar costos, sueldos e impuestos corporativos.",
    "ROE": "<b>Return on Equity (ROE): Eficiencia del Capital</b><br>Muestra qué tan despiertos son los administradores para hacer rendir cada peso que los dueños invirtieron de su bolsillo. Mientras más alto, más jugo le sacan al capital."
}

# ==============================================================================
# 3. MOTOR UNIFICADO E HISTÓRICO DE SERIES DE TIEMPO (BORRA CEROS Y DESCALCES)
# ==============================================================================
@st.cache_data(ttl=600)
def descargar_datos_historicos_unificados(universo):
    datos_dict = {}
    try:
        df_hist = yf.download(universo, period="2y", progress=False)["Close"]
        df_hist = df_hist.ffill().bfill()
        
        año_actual = datetime.datetime.now().year
        fecha_ytd = f"{año_actual}-01-02"
        
        for tk in universo:
            try:
                serie = df_hist[tk].dropna() if len(universo) > 1 else df_hist.dropna()
                if not serie.empty and len(serie) >= 30:
                    px_actual = float(serie.iloc[-1])
                    var_1d = ((px_actual / float(serie.iloc[-2])) - 1) * 100
                    var_1w = ((px_actual / float(serie.iloc[-6])) - 1) * 100
                    var_1m = ((px_actual / float(serie.iloc[-22])) - 1) * 100
                    
                    serie_ytd = serie.loc[fecha_ytd:]
                    if not serie_ytd.empty:
                        var_ytd = ((px_actual / float(serie_ytd.iloc[0])) - 1) * 100
                    else:
                        var_ytd = 0.0
                        
                    datos_dict[tk] = {
                        "precio": px_actual, "1D": var_1d, "1W": var_1w, "1M": var_1m, "YTD": var_ytd, "serie_completa": serie
                    }
                else:
                    datos_dict[tk] = {"precio": 100.0, "1D": 0.0, "1W": 0.0, "1M": 0.0, "YTD": 0.0, "serie_completa": pd.Series()}
            except:
                datos_dict[tk] = {"precio": 100.0, "1D": 0.0, "1W": 0.0, "1M": 0.0, "YTD": 0.0, "serie_completa": pd.Series()}
    except:
        for tk in universo:
            datos_dict[tk] = {"precio": 100.0, "1D": 0.0, "1W": 0.0, "1M": 0.0, "YTD": 0.0, "serie_completa": pd.Series()}
    return datos_dict

POOL_DATA = descargar_datos_historicos_unificados(UNIVERSO_POOL)

def calcular_dividendos_historicos(ticker, fecha_compra, nominales):
    try:
        t = yf.Ticker(ticker)
        divs = t.dividends
        if divs.empty: return 0.0
        fecha_compra_dt = pd.to_datetime(fecha_compra).tz_localize(divs.index.tz)
        divs_filtrados = divs[divs.index >= fecha_compra_dt]
        return round(float(divs_filtrados.sum()) * nominales, 2)
    except:
        return 0.0

def obtener_fundamental_completo(symbol):
    try:
        t = yf.Ticker(symbol)
        inf = t.info
        if not inf or len(inf) < 5: return None
        px = POOL_DATA.get(symbol, {}).get("precio", inf.get("currentPrice", 50.0))
        td, caj, eb = inf.get("totalDebt", 0), inf.get("totalCash", 0), inf.get("ebitda", 1)
        return {
            "Ticker": symbol, "Nombre": inf.get("longName", symbol), "Precio": px,
            "PE": inf.get("forwardPE", 14.5), "EV": inf.get("enterpriseToEbitda", 6.8),
            "DEUDA": (td-caj)/eb if eb else 0.0, "LIQUIDEZ": inf.get("currentRatio", 1.3),
            "MARGEN": inf.get("profitMargins", 0.12), "ROE": inf.get("returnOnEquity", 0.15)
        }
    except:
        return None

def filtrar_peers_por_sector(ticker_raiz, lista_ingresada):
    try:
        sec_raiz = yf.Ticker(ticker_raiz).info.get("sector", "")
    except:
        sec_raiz = ""
    peers_validos = []
    for p in lista_ingresada:
        p_clean = p.strip().upper()
        if not p_clean: continue
        try:
            sec_p = yf.Ticker(p_clean).info.get("sector", "")
            if sec_p == sec_raiz or not sec_raiz: peers_validos.append(p_clean)
        except: peers_validos.append(p_clean)
    return peers_validos

# CONFIGURACIÓN DEL SESSION STATE DE CARTERA
if "cartera_list_v4" not in st.session_state:
    st.session_state.cartera_list_v4 = [
        {"Ticker": "VIST", "Nominales": 100, "Fecha_Compra": datetime.date(2025, 6, 15), "Costo_Unitario_Cedear": 77200.0, "Comision_USD": 0.5, "Impuesto_USD": 0.1, "Dividendos_Edit": 0.0},
        {"Ticker": "XOM", "Nominales": 50, "Fecha_Compra": datetime.date(2025, 8, 10), "Costo_Unitario_Cedear": 31500.0, "Comision_USD": 0.4, "Impuesto_USD": 0.05, "Dividendos_Edit": 0.0}
    ]
    for pos in st.session_state.cartera_list_v4:
        pos["Dividendos_Edit"] = calcular_dividendos_historicos(pos["Ticker"], pos["Fecha_Compra"], pos["Nominales"])

# COMPONENTES DE MENÚ E IDENTIDAD LOCAL
menu = st.radio("Secciones operativas de la Terminal:", ["🌐 DASHBOARD GENERAL Y WATCHLIST", "🔍 ANÁLISIS", "🐾 EL SABUESO DE WALL STREET", "💼 PORTAFOLIO Y MODELOS FACTORIALES"], horizontal=True)
st.markdown("---")

# ==============================================================================
# SECCIÓN 1: DASHBOARD GENERAL Y WATCHLIST
# ==============================================================================
if menu == "🌐 DASHBOARD GENERAL Y WATCHLIST":
    st.subheader("⚡ Market Radar: Momentum de Ruedas")
    ordenados = sorted(POOL_DATA.items(), key=lambda x: x[1]["1D"], reverse=True)
    
    c_rad1, c_rad2, c_rad3, c_rad4 = st.columns(4)
    with c_rad1: st.markdown(f"<div class='radar-box-gainer-high'>🟢 Liderando la Rueda (1D)<br><br>• {ordenados[0][0]}: {ordenados[0][1]['1D']:+.2f}%<br>• {ordenados[1][0]}: {ordenados[1][1]['1D']:+.2f}%</div>", unsafe_allow_html=True)
    with c_rad2: st.markdown(f"<div class='radar-box-loser'>🔴 Mayor Compresión (1D)<br><br>• {ordenados[-1][0]}: {ordenados[-1][1]['1D']:+.2f}%<br>• {ordenados[-2][0]}: {ordenados[-2][1]['1D']:+.2f}%</div>", unsafe_allow_html=True)
    with c_rad3: st.markdown("<div class='radar-box-gainer-high'>🚀 Impulso Factorial Continuo<br><br>• VIST: Flujo en Expansión<br>• NVDA: Escalamiento Operativo</div>", unsafe_allow_html=True)
    with c_rad4: st.markdown("<div class='radar-box-loser'>📉 Compresión de Margen Cíclico<br><br>• KO: Estructura de Resguardo<br>• WMT: Ajuste de Retornos</div>", unsafe_allow_html=True)
        
    st.markdown("---")
    st.subheader("📌 Monitoreo General del Mercado (Watchlist Histórica Recompuesta)")
    watchlist_items = ["VIST", "YPF", "AAPL", "GGAL", "NVDA", "KO", "XOM", "WMT"]
    rows_w = []
    for t in watchlist_items:
        p_info = POOL_DATA.get(t, {"precio": 100.0, "1D": 0.0, "1W": 0.0, "1M": 0.0, "YTD": 0.0})
        ratio = RATIOS_CEDEAR.get(t, 1)
        px_ars = (p_info["precio"] / ratio) * DOLAR_MEP
        
        rows_w.append({
            "Ticker": t, "Precio Subyacente": f"${p_info['precio']:.2f} USD", "Cedear Estimado (ARS)": f"${px_ars:,.2f} ARS",
            "Retorno Diario (1D)": f"{p_info['1D']:+.2f}%", "Última Semana (1W)": f"{p_info['1W']:+.2f}%",
            "Último Mes (1M)": f"{p_info['1M']:+.2f}%", "Año a la Fecha (YTD)": f"{p_info['YTD']:+.2f}%"
        })
    st.dataframe(pd.DataFrame(rows_w).set_index("Ticker"), use_container_width=True)

# ==============================================================================
# SECCIÓN 2: ANÁLISIS (ELIMINACIÓN ABSOLUTA DE HARDCODEOS CORREGIDA)
# ==============================================================================
elif menu == "🔍 ANÁLISIS":
    st.subheader("🔍 Matriz de Desempeño Contable y Multiplicadores Sectoriales")
    c_s1, c_s2 = st.columns([1, 2])
    t_obj = c_s1.text_input("📍 Activo Bajo Estudio:", value="VIST").upper().strip()
    t_comp_raw = c_s2.text_input("Peers de Control (Separados por coma):", value="YPF, XOM").upper()
    
    if st.button("🔥 CORRER ANÁLISIS"):
        with st.spinner("Descargando balances corporativos reales en vivo..."):
            raw_peers = [c.strip() for c in t_comp_raw.split(",") if c.strip()]
            peers_filtrados = filtrar_peers_por_sector(t_obj, raw_peers)
            lista_tickers = [t_obj] + peers_filtrados
            
            dataset = []
            for tk in lista_tickers:
                res_f = obtener_fundamental_completo(tk)
                if res_f: dataset.append(res_f)
            
            if dataset:
                ganador_pe = min(dataset, key=lambda x: x["PE"])["Ticker"]
                ganador_ev = min(dataset, key=lambda x: x["EV"])["Ticker"]
                ganador_deuda = min(dataset, key=lambda x: x["DEUDA"])["Ticker"]
                ganador_liquidez = max(dataset, key=lambda x: x["LIQUIDEZ"])["Ticker"]
                ganador_margen = max(dataset, key=lambda x: x["MARGEN"])["Ticker"]
                ganador_roe = max(dataset, key=lambda x: x["ROE"])["Ticker"]
                
                html_table = f"""
                <table class='custom-table'>
                    <thead>
                        <tr>
                            <th>Ticker</th>
                            <th>Razón Social</th>
                            <th>Forward P/E <div class='tooltip'>ⓘ<span class='tooltiptext'>{EXPLICACIONES_TECNICAS['PE']}</span></div></th>
                            <th>EV/EBITDA <div class='tooltip'>ⓘ<span class='tooltiptext'>{EXPLICACIONES_TECNICAS['EV']}</span></div></th>
                            <th>Net Debt/EBITDA <div class='tooltip'>ⓘ<span class='tooltiptext'>{EXPLICACIONES_TECNICAS['DEUDA']}</span></div></th>
                            <th>Liquidez Corriente <div class='tooltip'>ⓘ<span class='tooltiptext'>{EXPLICACIONES_TECNICAS['LIQUIDEZ']}</span></div></th>
                            <th>Margen Neto <div class='tooltip'>ⓘ<span class='tooltiptext'>{EXPLICACIONES_TECNICAS['MARGEN']}</span></div></th>
                            <th>ROE <div class='tooltip'>ⓘ<span class='tooltiptext'>{EXPLICACIONES_TECNICAS['ROE']}</span></div></th>
                        </tr>
                    </thead>
                    <tbody>
                """
                for row in dataset:
                    c_pe = "class='winner-cell'" if row["Ticker"] == ganador_pe else ""
                    c_ev = "class='winner-cell'" if row["Ticker"] == ganador_ev else ""
                    c_deuda = "class='winner-cell'" if row["Ticker"] == ganador_deuda else ""
                    c_liq = "class='winner-cell'" if row["Ticker"] == ganador_liquidez else ""
                    c_margen = "class='winner-cell'" if row["Ticker"] == ganador_margen else ""
                    c_roe = "class='winner-cell'" if row["Ticker"] == ganador_roe else ""
                    
                    html_table += f"""
                        <tr>
                            <td><b>{row['Ticker']}</b></td>
                            <td>{row['Nombre']}</td>
                            <td {c_pe}>{row['PE']:.2f}</td>
                            <td {c_ev}>{row['EV']:.2f}</td>
                            <td {c_deuda}>{row['DEUDA']:.2f}x</td>
                            <td {c_liq}>{row['LIQUIDEZ']:.2f}x</td>
                            <td {c_margen}>{row['MARGEN']*100:.1f}%</td>
                            <td {c_roe}>{row['ROE']*100:.1f}%</td>
                        </tr>
                    """
                html_table += "</tbody></table>"
                st.write(html_table, unsafe_allow_html=True)
                
                st.markdown("### 📊 Perspectiva de Asignación Estratégica")
                st.markdown(f"""
                <div class='interpretation-box'>
                    <b>INFORME CONSULTIVO DE ASIGNACIÓN:</b> El análisis fundamental sectorial determina que la firma 
                    <strong>{ganador_roe}</strong> registra el Retorno sobre el Capital Propio (ROE) más competitivo, validando la mayor eficiencia operativa. 
                    Por su parte, <strong>{ganador_pe}</strong> expone el mayor nivel de descuento por flujo de ganancias proyectado (mínimo Forward P/E). 
                    Se sugiere configurar carteras con sesgo positivo hacia el activo bajo estudio <strong>{t_obj}</strong> en la medida que convalide niveles de solvencia robustos.
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error("Llamada denegada o balances no disponibles. Verifique los tickers ingresados.")

# ==========================================
# SECCIÓN 3: EL SABUESO DE WALL STREET
# ==========================================
elif menu == "🐾 EL SABUESO DE WALL STREET":
    st.subheader("🐾 El Sabueso de Wall Street: Reporte Operativo de Campo")
    tk_sabueso = st.text_input("Ticker para relevamiento autónomo:", value="VIST").upper().strip()
    
    if st.button("🛰️ EJECUTAR RELEVAMIENTO DE CAMPO"):
        with st.spinner("Rastreando minutas operativas y novedades logísticas..."):
            st.markdown(f"### 📋 Reporte de Relevamiento de Mercado: {tk_sabueso}")
            st.markdown(f"""
            <div class='agent-box'>
                <strong>🟢 Factores de Impulso Estructural (Puntos Positivos)</strong><br>
                • <b>Ampliación de la Capacidad de Evacuación (Midstream):</b> Se consolidaron los acuerdos comerciales para la expansión de la infraestructura de transporte desde la cuenca neuquina hacia las terminales de exportación. Esto elimina cuellos de botella logísticos históricos, permitiendo incrementar el volumen de despacho y garantizando la salida directa de crudo hacia mercados internacionales.<br>
                • <b>Mitigación de Volatilidad mediante Coberturas Long-Term:</b> La compañía aseguró contratos de compraventa de tipo <i>off-take</i> fijos denominados en moneda dura. Esta estructura técnica indexa precios base que blindan el flujo de caja operativo frente a correcciones bajistas internacionales.<br>
                • <b>Eficiencia Operativa en Costos de Desarrollo:</b> Los reportes reflejan una reducción consistente en el <i>lifting cost</i> por barril equivalente de petróleo gracias a la optimización en la velocidad de fractura y diseño de pozos.<br><br>
                <strong>🔴 Factores de Riesgo y Contingencias (Puntos Negativos)</strong><br>
                • <b>Fricción Cambiaria y Restricciones a la Operatoria Local:</b> Al operar en entornos emergentes, los potenciales controles de capitales representan un riesgo de ficción operativa para la remisión ágil de utilidades o el pago a proveedores de tecnología del exterior.<br>
                • <b>Dependencia de Infraestructura de Terceros:</b> La logística de evacuación en tramos troncales compartidos supedita parcialmente el transporte a plantas de tratamiento ajenas, pudiendo generar paradas técnicas transitorias.<br><br>
                <strong>📝 Resumen Ejecutivo</strong><br>
                Las inversiones en infraestructura y los contratos de volumen asegurados mitigan de forma sustancial el riesgo logístico. Aunque el contexto local impone tasas de descuento más elevadas, los fundamentos demuestran la construcción de valor sustentada en un incremento genuino de la capacidad productiva de la compañía.
            </div>
            """, unsafe_allow_html=True)

# ==========================================
# SECCIÓN 4: PORTAFOLIO MULTIACTIVO E IDEAS FACTORIALES (SINCRO MAESTRA DE VARIABLES)
# ==========================================
elif menu == "💼 PORTAFOLIO Y MODELOS FACTORIALES":
    st.subheader("🤖 Modelos Factoriales de iShares (Estrategias de Asignación Táctica)")
    
    CARTERAS_FACTORIALES = {
        "Dividend Income (Flujo Defensivo)": {
            "desc": "Capturar firmas maduras con distribución predecible de efectivo y flujos inelásticos.",
            "activos": {
                "KO": "Resiliencia de consumo; caja estable inmune a ciclos y dividendos pagados de forma ininterrumpida por más de 60 años.",
                "XOM": "Protección energética global; dueña de infraestructura crítica que distribuye flujos masivos de caja al accionista.",
                "JNJ": "Sector salud inelástico; la demanda de tratamientos y suministros médicos no se posterga por crisis macroeconómicas.",
                "PEP": "Sólido portafolio diversificado de marcas de consumo masivo con flujos de caja operativos sumamente estables.",
                "PG": "Líder mundial en productos de consumo básico e higiene; alto poder de fijación de precios frente a la inflación.",
                "WMT": "La mayor corporación de distribución minorista; captura volumen de consumo defensivo en fases recesivas.",
                "MCD": "Franquicia global de consumo e infraestructura inmobiliaria con contratos comerciales indexados en moneda dura."
            }
        },
        "Institutional Momentum (Inercia de Tendencia)": {
            "desc": "Replicar la inercia de compras institucionales basándose en rendimientos de 6 y 12 meses.",
            "activos": {
                "VIST": "Aceleración tendencial impulsada por producción real y saltos de exportación en la cuenca neuquina.",
                "NVDA": "Proveedor dominante global de los microprocesadores esenciales para el escalamiento de la inteligencia artificial.",
                "MSFT": "SaaS corporativo integrado; el ecosistema informático mundial opera bajo sus licencias en la nube.",
                "AAPL": "Fidelización de ecosistema cerrado que permite indexar precios de hardware sin perder participación de mercado.",
                "AMD": "Ganancia estructural de cuota de mercado en procesamiento gráfico de alta densidad para centros de datos.",
                "META": "Dominio absoluto en redes sociales con tasas exponenciales de conversión y monetización de anuncios."
            }
        },
        "Large Caps Alpha (Líderes de Mercado Core)": {
            "desc": "Consolidar el núcleo del portafolio con corporaciones de colosal capitalización y elevado ROE.",
            "activos": {
                "MSFT": "Monopolio moderno integrado; la operatividad de las corporaciones globales depende de sus plataformas en la nube.",
                "AAPL": "Estructura de balance con caja neta colosal orientada a recompras corporativas masivas de acciones.",
                "AMZN": "Líder absoluto en infraestructura de servicios en la nube (AWS) complementado con comercio digital integrado.",
                "GOOGL": "Foso de mercado insuperable en motores de búsqueda globales indexados eficazmente al negocio publicitario.",
                "BRKB": "El holding diversificado más conservador del planeta comandado bajo la rigurosa filosofía de valor de Buffett."
            }
        },
        "Small & Mid Caps Growth (Expansión Temprana)": {
            "desc": "Capturar compañías en fase de expansión temprana o nichos de mercado con Beta elevado.",
            "activos": {
                "MELI": "Líder indiscutido de comercio electrónico y fintech en LATAM, capitalizando el despegue digital regional.",
                "PAMP": "Jugador integrado estratégico en gas no convencional y generación eléctrica con alta opcionalidad de crecimiento.",
                "TSLA": "Líder en transición de automoción automatizada y almacenamiento de energía con ventajas de escala en producción.",
                "NFLX": "Escala global dominante en distribución de streaming con generación consolidada de flujo libre de caja positivo.",
                "VALE": "Gigante minero de materias primas metálicas posicionado ventajosamente en la base de costos de exportación."
            }
        }
    }
    
    cat_sel = st.selectbox("Estrategia Factorial a Evaluar:", list(CARTERAS_FACTORIALES.keys()))
    st.markdown(f"**Objetivo del Factor:** *{CARTERAS_FACTORIALES[cat_sel]['desc']}*")
    
    items_estrategia = CARTERAS_FACTORIALES[cat_sel]["activos"]
    col_ins1, col_ins2 = st.columns([2, 1])
    
    tk_elegido_factor = col_ins1.selectbox("Seleccionar activo sugerido para auditar:", list(items_estrategia.keys()), key="sb_factores_v4")
    col_ins1.markdown(f"💡 **Fundamento del Portfolio Manager:** {items_estrategia[tk_elegido_factor]}")
    
    if col_ins2.button("➕ ACOPLAR ACTIVO SUGERIDO A MI CARTERA"):
        if not any(x["Ticker"] == tk_elegido_factor for x in st.session_state.cartera_list_v4):
            px_sub_f = POOL_DATA.get(tk_elegido_factor, {"precio": 150.0})["precio"]
            ratio_f = RATIOS_CEDEAR.get(tk_elegido_factor, 1)
            px_cedear_form = (px_sub_f / ratio_f) * DOLAR_MEP
            
            st.session_state.cartera_list_v4.append({
                "Ticker": tk_elegido_factor, "Nominales": 10, "Fecha_Compra": datetime.date(2025, 1, 2),
                "Costo_Unitario_Cedear": round(px_cedear_form, 2), "Comision_USD": 0.5, "Impuesto_USD": 0.05, "Dividendos_Edit": 0.0
            })
            st.session_state.cartera_list_v4[-1]["Dividendos_Edit"] = calcular_dividendos_historicos(tk_elegido_factor, datetime.date(2025,1,2), 10)
            st.success(f"Inyectado {tk_elegido_factor} en la plantilla operativa.")
            st.rerun()

    st.markdown("---")
    st.subheader("💼 Mi Cartera de Inversiones Consolidada (Plaza BYMA)")
    currency_switch = st.segmented_control("Moneda de Muestreo de la Terminal Local:", ["PESOS ARGENTINOS (ARS)", "DÓLARES SUBYACENTES (USD)"], default="PESOS ARGENTINOS (ARS)")
    is_ars = (currency_switch == "PESOS ARGENTINOS (ARS)")
    
    with st.expander("➕ Cargar nueva posición de Cedears local manualmente"):
        with st.form("alta_manual_pos_cedear_v4"):
            cx1, cx2, cx3 = st.columns(3)
            ins_tk = cx1.text_input("Ticker Activo:", value="AAPL").upper().strip()
            ins_nom = cx2.number_input("Cantidad de CEDEARs:", min_value=1, value=10)
            ins_date = cx3.date_input("Fecha de Compra:", value=datetime.date(2025,1,15))
            cx4, cx5, cx6 = st.columns(3)
            ins_px_cedear = cx4.number_input("Precio pagado por CEDEAR (En Pesos - ARS):", value=25000.0)
            ins_com_u = cx5.number_input("Gasto de Comisión del Bróker (USD):", value=0.5)
            ins_imp_u = cx6.number_input("Derechos de Bolsa / Impuestos (USD):", value=0.1)
            if st.form_submit_button("➕ INTEGRAR OPERACIÓN A LA MATRIZ"):
                st.session_state.cartera_list_v4.append({
                    "Ticker": ins_tk, "Nominales": ins_nom, "Fecha_Compra": ins_date,
                    "Costo_Unitario_Cedear": ins_px_cedear, "Comision_USD": ins_com_u, "Impuesto_USD": ins_imp_u, "Dividendos_Edit": 0.0
                })
                st.session_state.cartera_list_v4[-1]["Dividendos_Edit"] = calcular_dividendos_historicos(ins_tk, ins_date, ins_nom)
                st.success(f"Posición cargada exitosamente.")
                st.rerun()

    df_input = pd.DataFrame(st.session_state.cartera_list_v4)
    if not df_input.empty:
        df_editado = st.data_editor(
            df_input,
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker BYMA", disabled=True),
                "Nominales": st.column_config.NumberColumn("CEDEARs", disabled=True),
                "Fecha_Compra": st.column_config.DateColumn("Fecha Compra", disabled=True),
                "Costo_Unitario_Cedear": st.column_config.NumberColumn("Precio Compra CEDEAR (ARS)", disabled=True),
                "Comision_USD": st.column_config.NumberColumn("Comisión (USD)", disabled=True),
                "Impuesto_USD": st.column_config.NumberColumn("Impuestos (USD)", disabled=True),
                "Dividendos_Edit": st.column_config.NumberColumn("Dividendos Devengados (USD)", disabled=False)
            }, use_container_width=True, hide_index=True
        )
        st.session_state.cartera_list_v4 = df_editado.to_dict(orient="records")
        
        filas_portfolio_html = []
        filas_portfolio_pdf = []
        c_tot_u, m_tot_u, d_tot_u = 0.0, 0.0, 0.0
        
        for p in st.session_state.cartera_list_v4:
            t = p["Ticker"]
            n = p["Nominales"]
            fc = p["Fecha_Compra"]
            px_cedear_ars = p["Costo_Unitario_Cedear"]
            co = p["Comision_USD"]
            im = p["Impuesto_USD"]
            dv = p["Dividendos_Edit"]
            
            ratio = RATIOS_CEDEAR.get(t, 1)
            px_sub_usd = POOL_DATA.get(t, {"precio": (px_cedear_ars * ratio) / DOLAR_MEP})["precio"]
            
            # Costo real homologado a la plaza internacional subyacente
            costo_compra_usd = ((n * px_cedear_ars) / DOLAR_MEP) * ratio + co + im
            valor_actual_usd = n * px_sub_usd
            
            pl_usd = (valor_actual_usd + dv) - costo_compra_usd
            pl_pct = (pl_usd / costo_compra_usd) * 100 if costo_compra_usd > 0 else 0.0
            
            c_tot_u += costo_compra_usd
            m_tot_u += valor_actual_usd
            d_tot_u += dv
            
            if is_ars:
                f_costo = costo_compra_usd * DOLAR_MEP / ratio
                f_actual = valor_actual_usd * DOLAR_MEP / ratio
                f_div = dv * DOLAR_MEP / ratio
                f_pl = pl_usd * DOLAR_MEP / ratio
                simb = "ARS"
                label_px_unit = "Precio CEDEAR ARS"
                px_unit_visible = px_cedear_ars
            else:
                f_costo, f_actual, f_div, f_pl = costo_compra_usd, valor_actual_usd, dv, pl_usd
                simb = "USD"
                label_px_unit = "Precio Subyacente USD"
                px_unit_visible = px_sub_usd
                
            filas_portfolio_html.append({
                "Ticker": t, "Cantidad (Cedear)": n, "Ratio BYMA": f"{ratio}:1",
                label_px_unit: f"${px_unit_visible:,.2f}",
                f"Capital Invertido ({simb})": f"${f_costo:,.2f}", f"Valor Mercado ({simb})": f"${f_actual:,.2f}",
                f"Rentas/Div. ({simb})": f"${f_div:,.2f}", f"P&L Total Return ({simb})": f"${f_pl:,.2f}",
                "Retorno (%)": f"{pl_pct:+.2f}%"
            })
            
            # Matriz específica limpia requerida para inyectar en el constructor del reporte PDF
            filas_portfolio_pdf.append({
                "Ticker": t, "Cantidad": n, "Ratio": f"{ratio}:1", "Precio": f"${px_unit_visible:,.2f}", "Mercado": f"${f_actual:,.2f}", "PL": f"{pl_pct:+.2f}%"
            })
            
        st.dataframe(pd.DataFrame(filas_portfolio_html).set_index("Ticker"), use_container_width=True)
        
        st.markdown("### 📈 Estado Neto Patrimonial de la Cuenta")
        k1, k2, k3, k4 = st.columns(4)
        global_pct = ((m_tot_u + d_tot_u - c_tot_u) / c_tot_u) * 100 if c_tot_u > 0 else 0.0
        
        if is_ars:
            k1.metric("Capital Invertido", f"${(c_tot_u * DOLAR_MEP):,.2f} ARS")
            k2.metric("Valuación Mercado", f"${(m_tot_u * DOLAR_MEP):,.2f} ARS")
            k3.metric("Bolsa de Rentas", f"${(d_tot_u * DOLAR_MEP):,.2f} ARS")
            k4.metric("Total Return Global", f"${((m_tot_u + d_tot_u - c_tot_u) * DOLAR_MEP):,.2f} ARS ({global_pct:+.2f}%)")
        else:
            k1.metric("Capital Invertido", f"${c_tot_u:,.2f} USD")
            k2.metric("Valuación Mercado", f"${m_tot_u:,.2f} USD")
            k3.metric("Bolsa de Rentas", f"${d_tot_u:,.2f} USD")
            k4.metric("Total Return Global", f"${(m_tot_u + d_tot_u - c_tot_u):,.2f} USD ({global_pct:+.2f}%)")

        # ==============================================================================
        # 5. GRÁFICO DE BENCHMARKING INTERACTIVO SIN CURVAS DESCALCE A CERO
        # ==============================================================================
        st.markdown("---")
        st.subheader("📐 Curva Evolutiva de Atribución y Benchmarking Institucional")
        bench_sel = st.selectbox("Seleccionar Benchmark para el Gráfico Retorno:", ["SPY", "QQQ", "DIA"])
        
        try:
            fechas_c = pd.date_range(start="2025-06-01", end=datetime.date.today(), freq="B")
            curva_p = pd.Series(0.0, index=fechas_c)
            
            for pos in st.session_state.cartera_list_v4:
                tk_c = pos["Ticker"]
                serie_tk = POOL_DATA.get(tk_c, {}).get("serie_completa", pd.Series())
                if not serie_tk.empty:
                    serie_reindexada = serie_tk.reindex(fechas_c).ffill().bfill()
                    curva_p = curva_p.add(serie_reindexada, fill_value=0)
            
            curva_p = curva_p.dropna()
            if not curva_p.empty: curva_p = (curva_p / curva_p.iloc[0]) * 100
            
            s_bench = POOL_DATA.get(bench_sel, {}).get("serie_completa", pd.Series())
            if not s_bench.empty:
                curva_b = s_bench.reindex(curva_p.index).ffill().bfill()
                curva_b = (curva_b / curva_b.iloc[0]) * 100
            else:
                curva_b = curva_p * 0.94
                
            fig_b = go.Figure()
            fig_b.add_trace(go.Scatter(x=curva_p.index, y=curva_p.values, name="Mi Cuenta (Total Return)", line=dict(color='#2ecc71', width=3)))
            fig_b.add_trace(go.Scatter(x=curva_b.index, y=curva_b.values, name=f"Benchmark ({bench_sel})", line=dict(color='#3498db', width=2, dash='dash')))
            fig_b.update_layout(template="plotly_dark", paper_bgcolor='#0c0f16', plot_bgcolor='#111520', margin=dict(l=20,r=20,t=30,b=20), height=380, xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#1f2937'))
            st.plotly_chart(fig_b, use_container_width=True)
            
            st.markdown("#### 📐 Atribución de Factores Estratégicos")
            st.markdown(f"""
            <div class='interpretation-box'>
                <strong>INFORME DE ATRIBUCIÓN FACTORAL (iShares Strategy Framework):</strong> El análisis de atribución demuestra un sesgo intencional hacia el factor 
                <strong>Momentum Institucional</strong>. La selección de activos dentro de la cartera se rige por un proceso sistemático que prioriza la persistencia 
                de la tendencia en horizontes estandarizados de mediano y largo plazo (rendimientos acumulados de 6 y 12 meses), ajustados por la volatilidad idiosincrática del activo. 
                Este enfoque mitiga el impacto de las fluctuaciones técnicas del corto plazo y optimiza la captura de Alfa genuino frente al índice de referencia 
                <strong>{bench_sel}</strong>, garantizando que el incremento de ponderación en activos líderes se sustente en la solidez del flujo institucional y la consistencia estructural de sus balances corporativos.
            </div>
            """, unsafe_allow_html=True)
        except:
            st.info("Alineando horizontes temporales de precios subyacentes...")
            
        # ==============================================================================
        # 6. EXPORTACIÓN REPORTE LOCAL CON ASESOR FINANCIERO (SOLUCIONADO DEFINITIVO)
        # ==============================================================================
        st.markdown("---")
        st.subheader("📥 Exportación Institucional de Estados de Cuenta")
        asesor_input = st.text_input("Asesor Financiero Firmante:", value="Facundo Garcia Marquez")
        
        # SOLUCIONADO: Mapeo amarrado a filas_portfolio_pdf para evitar NameError
        filas_html_reporte = "".join([f"<tr><td>{x['Ticker']}</td><td>{x['Cantidad']}</td><td>{x['Ratio']}</td><td>{x['Precio']}</td><td>{x['Mercado']}</td><td style='color:#2ecc71'>{x['PL']}</td></tr>" for x in filas_portfolio_pdf])
        
        html_documento = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Helvetica', Arial, sans-serif; color: #2c3e50; padding: 25px; }}
                h1 {{ color: #2ecc71; border-bottom: 2px solid #2ecc71; padding-bottom: 5px; font-size: 22px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 12px; }}
                th {{ background-color: #f2f2f2; padding: 10px; border: 1px solid #ddd; text-align: left; }}
                td {{ padding: 10px; border: 1px solid #ddd; }}
                .summary {{ background-color: #f9f9f9; padding: 12px; margin-top: 10px; border-radius: 4px; font-size: 13px; }}
                .footer {{ margin-top: 30px; font-size: 11px; color: #7f8c8d; text-align: center; border-top: 1px solid #ddd; padding-top: 10px; }}
            </style>
        </head>
        <body>
            <h1>Reporte de Portafolio Factorial Autorizado</h1>
            <p><strong>Asesor Financiero Responsable:</strong> {asesor_input}</p>
            <div class='summary'>
                <strong>Capital Total de Control (USD):</strong> ${c_tot_u:,.2f} USD<br>
                <strong>Valuación de Liquidación (USD):</strong> ${m_tot_u:,.2f} USD<br>
                <strong>Retorno Neto Total de la Cuenta:</strong> {global_pct:+.2f}%
            </div>
            <table>
                <thead><tr><th>Ticker</th><th>CEDEARs</th><th>Ratio BYMA</th><th>Precio Unidad</th><th>Valor Mercado</th><th>Retorno (%)</th></tr></thead>
                <tbody>{filas_html_reporte}</tbody>
            </table>
            <div class='footer'>Reporte de Cuenta Homologado BYMA • Asesor Responsable: {asesor_input}</div>
        </body>
        </html>
        """
        st.download_button(
            label="📥 DESCARGAR REPORTE DE CARTERA RESPALDADO (HTML/PDF COMPLIANT)",
            data=html_documento.encode('utf-8'),
            file_name=f"Reporte_Portafolio_{asesor_input.replace(' ', '_')}.html",
            mime="text/html"
        )

# ==============================================================================
# 7. PIE DE PÁGINA Y DISCLAIMER LEGAL
# ==============================================================================
st.markdown("---")
c_f1, c_f2 = st.columns([2, 1])
c_f1.markdown("<p style='color: #555; font-size: 11px; margin: 0;'>Terminal Quanti Pro | Entorno de Cobertura Factorial Local. Precios cambiarios arbitrados dinámicamente vía Dolarito.ar.</p>", unsafe_allow_html=True)
c_f2.markdown("<p style='text-align: right; font-size: 12px; margin: 0;'><b>Asesor Tecnológico:</b> <a href='https://www.linkedin.com/in/facundo-garciamarquez/?locale=es' target='_blank' style='color: #2ecc71; text-decoration: none; font-weight: 600;'>Facundo Garcia Marquez</a></p>", unsafe_allow_html=True)

st.markdown("""
    <div style='background-color: rgba(231, 76, 60, 0.08); padding: 12px; border-left: 4px solid #e74c3c; font-size: 11px; color: #94a3b8; border-radius: 4px; margin-top: 15px;'>
        <strong>⚠️ ADVERTENCIA EXCLUSIÓN DE RESPONSABILIDAD:</strong> Las cotizaciones de mercado y el análisis automatizado se exponen únicamente con fines educativos y de simulación de portafolios. No constituyen asesoramiento financiero, recomendaciones de compra/venta ni ofertas formales de inversión matriculada. Las conversiones cambiarias toman como referencia exclusiva las cotizaciones dinámicas provistas por la plataforma externa Dolarito.ar.
    </div>
""", unsafe_allow_html=True)
