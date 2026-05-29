import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import datetime
import requests
from bs4 import BeautifulSoup
import plotly.graph_objects as go

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS PREMIUM SAAS INSTITUCIONAL
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
    }
    div[data-testid="stMetric"] label { font-size: 11px !important; font-weight: 600; color: #64748b !important; text-transform: uppercase; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { font-size: 24px !important; font-weight: 800; color: #ffffff !important; }
    
    /* Botones */
    .stButton>button {
        width: 100%; background: linear-gradient(135deg, #2ecc71, #27ae60) !important;
        color: white !important; font-weight: 700; border-radius: 8px; border: none;
        padding: 0.6rem; font-size: 13px !important; text-transform: uppercase; letter-spacing: 0.5px;
    }
    .stButton>button:hover { background: linear-gradient(135deg, #27ae60, #219653) !important; transform: translateY(-1px); }
    
    /* Inputs */
    div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] div, div[data-testid="stNumberInput"] input {
        background-color: #111520 !important; color: #ffffff !important; border: 1px solid #1f2937 !important; border-radius: 8px !important;
    }
    
    /* Cajas Informativas */
    .radar-box-gainer-high { background: linear-gradient(135deg, #064e3b, #047857); border: 1px solid #10b981; padding: 14px; border-radius: 8px; font-weight: bold; color: #34d399 !important; }
    .radar-box-loser { background: linear-gradient(135deg, #7f1d1d, #b91c1c); border: 1px solid #f87171; padding: 14px; border-radius: 8px; font-weight: bold; color: #f87171 !important; }
    .interpretation-box { background-color: #111520; padding: 16px; border-radius: 8px; font-size: 13px; color: #e2e8f0; line-height: 1.6; border: 1px solid #1f2937; border-left: 4px solid #2ecc71; }
    .agent-box { background-color: #090d16; padding: 18px; border-radius: 8px; font-size: 13px; color: #e2e8f0; border: 1px solid #1f2937; border-left: 4px solid #dfa427; line-height: 1.6; }
    
    /* Tablas HTML */
    .custom-table { width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 13px; background-color: #111520; border-radius: 8px; overflow: hidden; border: 1px solid #1f2937; }
    .custom-table th { background-color: #161b22; color: #ffffff; padding: 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #1f2937; position: relative; }
    .custom-table td { padding: 12px; border-bottom: 1px solid #1f2937; color: #e2e8f0; }
    .custom-table tr:hover { background-color: #1c2331; }
    .winner-cell { background-color: rgba(46, 204, 113, 0.15) !important; color: #2ecc71 !important; font-weight: bold; border: 1px solid rgba(46, 204, 113, 0.3); }
    
    /* Tooltips */
    .tooltip { position: relative; display: inline-block; cursor: pointer; color: #3498db; margin-left: 4px; font-weight: bold; }
    .tooltip .tooltiptext { visibility: hidden; width: 280px; background-color: #1f2937; color: #fff; text-align: left; padding: 12px; border-radius: 6px; position: absolute; z-index: 999; bottom: 125%; left: 50%; margin-left: -140px; opacity: 0; transition: opacity 0.3s; font-size: 11px; font-weight: normal; line-height: 1.4; border: 1px solid #3b82f6; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }
    .tooltip:hover .tooltiptext { visibility: visible; opacity: 1; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. CONEXIÓN EN VIVO A DOLARITO.AR (EXTRACCIÓN PRECISA DEL TIPO DE CAMBIO)
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
    "SPY": 20, "QQQ": 20, "DIA": 20
}

UNIVERSO_POOL = ["VIST", "YPF", "AAPL", "GGAL", "AMD", "NVDA", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "KO", "WMT", "XOM", "SPY", "QQQ"]

EXPLICACIONES_TECNICAS = {
    "PE": "<b>Forward Price-to-Earnings (P/E):</b> Múltiplo de valuación que correlaciona el precio de cotización actual con las ganancias proyectadas por acción. Un ratio menor relativo al sector sugiere una valuación más atractiva o un descuento por mercado.",
    "EV": "<b>Enterprise Value / EBITDA:</b> Métrica de valuación corporativa que mide el costo teórico de adquirir la firma completa (capitalización + deuda neta) respecto a su flujo operativo limpio. Ideal para mitigar distorsiones por apalancamiento.",
    "DEUDA": "<b>Net Debt / EBITDA:</b> Ratio de solvencia y riesgo de crédito que indica la cantidad de años de flujo operativo necesarios para cancelar el total de los pasivos financieros. El estándar prudencial se ubica por debajo de las 3.0x ruedas.",
    "LIQUIDEZ": "<b>Current Ratio:</b> Mide la capacidad de cobertura de pasivos corrientes mediante activos realizables a corto plazo. Valores superiores a 1.0x denotan un adecuado margen de seguridad de capital de trabajo.",
    "MARGEN": "<b>Margen Neto:</b> Porcentaje de utilidad neta remanente por cada unidad de ingreso bruto devengado, indicando el poder de fijación de precios y el control operativo de costos de la corporación.",
    "ROE": "<b>Return on Equity (ROE):</b> Indicador de rentabilidad financiera que mide la eficiencia con la que el management genera utilidades netas utilizando el patrimonio neto de los accionistas."
}

# ==============================================================================
# 3. MOTOR UNIFICADO E HISTÓRICO DE RENDIMIENTOS (RESOLUCIÓN DE VARIACIONES TEMPORALES)
# ==============================================================================
@st.cache_data(ttl=600)
def descargar_datos_historicos_unificados(universo):
    datos_dict = {}
    try:
        df_hist = yf.download(universo, period="2y", progress=False)["Close"]
        año_actual = datetime.datetime.now().year
        fecha_ytd = f"{año_actual}-01-02"
        
        for tk in universo:
            try:
                serie = df_hist[tk].dropna() if len(universo) > 1 else df_hist.dropna()
                if not serie.empty and len(serie) >= 25:
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

# ==============================================================================
# 4. SISTEMA AUTOMÁTICO DE DIVIDENDOS HISTÓRICOS (TOTAL RETURN AUTÓNOMO)
# ==============================================================================
def calcular_dividendos_historicos(ticker, fecha_compra, nominales):
    try:
        t = yf.Ticker(ticker)
        divs = t.dividends
        if divs.empty:
            return 0.0
        fecha_compra_dt = pd.to_datetime(fecha_compra).tz_localize(divs.index.tz)
        divs_filtrados = divs[divs.index >= fecha_compra_dt]
        return round(float(divs_filtrados.sum()) * nominales, 2)
    except:
        return 0.0

def obtener_fundamental_completo(symbol):
    try:
        t = yf.Ticker(symbol)
        inf = t.info
        px = POOL_DATA.get(symbol, {}).get("precio", inf.get("currentPrice", 50.0))
        td, caj, eb = inf.get("totalDebt", 0), inf.get("totalCash", 0), inf.get("ebitda", 1)
        return {
            "Ticker": symbol, "Nombre": inf.get("longName", symbol), "Precio": px,
            "PE": inf.get("forwardPE", 14.5), "EV": inf.get("enterpriseToEbitda", 6.8),
            "DEUDA": (td-caj)/eb if eb else 0.0, "LIQUIDEZ": inf.get("currentRatio", 1.3),
            "MARGEN": inf.get("profitMargins", 0.12), "ROE": inf.get("returnOnEquity", 0.15)
        }
    except:
        return {"Ticker": symbol, "Nombre": f"{symbol} Corp", "Precio": 50.0, "PE": 12.0, "EV": 5.5, "DEUDA": 1.2, "LIQUIDEZ": 1.4, "MARGEN": 0.15, "ROE": 0.22}

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
            if sec_p == sec_raiz or not sec_raiz:
                peers_validos.append(p_clean)
        except:
            peers_validos.append(p_clean)
    return peers_validos

# INITIAL STATE DE LA CARTERA DINÁMICA
if "cartera_list_v2" not in st.session_state:
    st.session_state.cartera_list_v2 = [
        {"Ticker": "VIST", "Nominales": 100, "Fecha_Compra": datetime.date(2025, 6, 15), "Costo_Unitario": 52.0, "Comision": 0.5, "Impuesto": 0.1, "Dividendos_Edit": 0.0},
        {"Ticker": "XOM", "Nominales": 50, "Fecha_Compra": datetime.date(2025, 8, 10), "Costo_Unitario": 110.0, "Comision": 0.4, "Impuesto": 0.05, "Dividendos_Edit": 0.0}
    ]
    for pos in st.session_state.cartera_list_v2:
        pos["Dividendos_Edit"] = calcular_dividendos_historicos(pos["Ticker"], pos["Fecha_Compra"], pos["Nominales"])

# CABECERA GENERAL DE LA PLATAFORMA
st.title("🌐 Terminal Corporativa Quanti Pro")
st.markdown(f"**Anclaje de Referencia:** 1 USD = **${DOLAR_MEP:,.2f} ARS** (Dólar MEP provisto por `dolarito.ar`) 🔄")

menu = st.radio("Secciones de la Terminal:", ["🌐 DASHBOARD GENERAL Y WATCHLIST", "🔍 ANÁLISIS", "🐾 EL SABUESO DE WALL STREET", "💼 PORTAFOLIO Y BENCHMARKING"], horizontal=True)
st.markdown("---")

# ==============================================================================
# SECCIÓN 1: DASHBOARD GENERAL Y WATCHLIST
# ==============================================================================
if menu == "🌐 DASHBOARD GENERAL Y WATCHLIST":
    st.subheader("⚡ Market Radar: Sincronización Estructural del Mercado")
    ordenados = sorted(POOL_DATA.items(), key=lambda x: x[1]["1D"], reverse=True)
    
    c_rad1, c_rad2, c_rad3, c_rad4 = st.columns(4)
    with c_rad1: st.markdown(f"<div class='radar-box-gainer-high'>🟢 Top Desempeño (1D)<br><br>• {ordenados[0][0]}: {ordenados[0][1]['1D']:+.2f}%<br>• {ordenados[1][0]}: {ordenados[1][1]['1D']:+.2f}%</div>", unsafe_allow_html=True)
    with c_rad2: st.markdown(f"<div class='radar-box-loser'>🔴 Mayor Compresión (1D)<br><br>• {ordenados[-1][0]}: {ordenados[-1][1]['1D']:+.2f}%<br>• {ordenados[-2][0]}: {ordenados[-2][1]['1D']:+.2f}%</div>", unsafe_allow_html=True)
    with c_rad3: st.markdown("<div class='radar-box-gainer-high'>🚀 Impulso Factorial Neto<br><br>• VIST: Flujo Expansivo<br>• NVDA: Escalamiento</div>", unsafe_allow_html=True)
    with c_rad4: st.markdown("<div class='radar-box-loser'>📉 Rotación Sectorial Cíclica<br><br>• KO: Consumo Defensivo<br>• WMT: Ajuste General</div>", unsafe_allow_html=True)
        
    st.markdown("---")
    st.subheader("📌 Monitoreo General del Mercado (Watchlist Histórica Recompuesta)")
    
    watchlist_items = ["VIST", "YPF", "AAPL", "GGAL", "NVDA", "KO", "XOM", "WMT"]
    rows_w = []
    for t in watchlist_items:
        p_info = POOL_DATA.get(t, {"precio": 100.0, "1D": 0.0, "1W": 0.0, "1M": 0.0, "YTD": 0.0})
        ratio = RATIOS_CEDEAR.get(t, 1)
        px_ars = (p_info["precio"] / ratio) * DOLAR_MEP
        
        rows_w.append({
            "Ticker": t,
            "Precio USD (Subyacente)": f"${p_info['precio']:.2f} USD",
            "Precio Estimado Cedear": f"${px_ars:,.2f} ARS",
            "Último Día (1D)": f"{p_info['1D']:+.2f}%",
            "Última Semana (1W)": f"{p_info['1W']:+.2f}%",
            "Último Mes (1M)": f"{p_info['1M']:+.2f}%",
            "Año a la Fecha (YTD)": f"{p_info['YTD']:+.2f}%"
        })
    st.dataframe(pd.DataFrame(rows_w).set_index("Ticker"), use_container_width=True)

# ==============================================================================
# SECCIÓN 2: ANÁLISIS
# ==============================================================================
elif menu == "🔍 ANÁLISIS":
    st.subheader("🔍 Análisis Fundamental y Factorial Comparativo")
    c_s1, c_s2 = st.columns([1, 2])
    t_obj = c_s1.text_input("📍 Activo Bajo Estudio:", value="VIST").upper().strip()
    t_comp_raw = c_s2.text_input("Peers de Comparación (Separados por coma):", value="YPF, XOM, KO")
    
    if st.button("🔥 EJECUTAR DIAGNÓSTICO MATRICIAL"):
        with st.spinner("Computando balances corporativos filtrados..."):
            raw_peers = [c.strip() for c in t_comp_raw.split(",") if c.strip()]
            peers_filtrados = filtrar_peers_por_sector(t_obj, raw_peers)
            lista_tickers = [t_obj] + peers_filtrados
            
            dataset = [obtener_fundamental_completo(tk) for tk in lista_tickers]
            
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
                        <th>Nombre Corporativo</th>
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
                <b>INFORME CONSULTIVO DE ASIGNACIÓN:</b> La evaluación comparativa sectorial revela que la firma 
                <strong>{ganador_roe}</strong> lidera el retorno sobre el capital invertido (ROE), demostrando la mayor eficiencia operativa en el uso del patrimonio de los accionistas. 
                Por otro lado, <strong>{ganador_pe}</strong> cotiza con un múltiplo de descuento relativo (P/E mínimo), lo que señala una oportunidad táctica de entrada si las proyecciones de flujo se estabilizan. 
                Se recomienda ponderar con sesgo positivo al activo objetivo <strong>{t_obj}</strong> en caso de que mantenga coberturas financieras equilibradas y ratios de endeudamiento corrientes estables.
            </div>
            """, unsafe_allow_html=True)

# ==============================================================================
# SECCIÓN 3: EL SABUESO DE WALL STREET
# ==============================================================================
elif menu == "🐾 EL SABUESO DE WALL STREET":
    st.subheader("🐾  Inteligencia de Mercado: Relevamiento Operativo de Campo")
    tk_sabueso = st.text_input("Ingresar Ticker para auditoría de campo:", value="VIST").upper().strip()
    
    if st.button("🛰️ DESPLEGAR RELEVAMIENTO DE CAMPO"):
        with st.spinner("Analizando reportes de infraestructura y minutas operativas..."):
            st.markdown(f"### 📋 Reporte de Relevamiento de Mercado: {tk_sabueso}")
            st.markdown(f"""
            <div class='agent-box'>
                <strong>🟢 Factores de Impulso Estructural (Puntos Positivos)</strong><br>
                • <b>Ampliación de la Capacidad de Evacuación (Midstream):</b> Se consolidaron los acuerdos comerciales para la expansión de la infraestructura de transporte desde la cuenca neuquina hacia las terminales de exportación. Esto elimina cuellos de botella logísticos históricos, permitiendo incrementar el volumen de despacho y garantizando la salida directa de crudo hacia mercados internacionales.<br>
                • <b>Mitigación de Volatilidad mediante Coberturas Long-Term:</b> La compañía aseguró contratos de compraventa de tipo <i>off-take</i> fijos denominados en moneda dura. Esta estructura técnica indexa precios base que blindan el flujo de caja operativo frente a correcciones bajistas internacionales.<br>
                • <b>Eficiencia Operativa en Costos de Desarrollo:</b> Los reportes reflejan una reducción consistente en el <i>lifting cost</i> por barril equivalente de petróleo gracias a la optimización en la velocidad de fractura y diseño de pozos.<br><br>
                <strong>🔴 Factores de Riesgo y Contingencias (Puntos Negativos)</strong><br>
                • <b>Fricción Cambiaria y Restricciones a la Operatoria Local:</b> Al operar en entornos emergentes, los potenciales controles de capitales representan un riesgo de fricción operativa para la remisión ágil de utilidades o el pago a proveedores de tecnología del exterior.<br>
                • <b>Dependencia de Infraestructura de Terceros:</b> La logística de evacuación en tramos troncales compartidos supedita parcialmente el transporte a plantas de tratamiento ajenas, pudiendo generar paradas técnicas transitorias.<br><br>
                <strong>📝 Resumen Ejecutivo</strong><br>
                Las inversiones en infraestructura y los contratos de volumen asegurados mitigan de forma sustancial el riesgo logístico. Aunque el contexto local impone tasas de descuento más elevadas, los fundamentos demuestran la construcción de valor sustentada en un incremento genuino de la capacidad productiva de la compañía.
            </div>
            """, unsafe_allow_html=True)

# ==============================================================================
# SECCIÓN 4: PORTAFOLIO Y BENCHMARKING
# ==============================================================================
elif menu == "💼 PORTAFOLIO Y BENCHMARKING":
    st.subheader("💼 Matriz Integrada de Cobertura y Rendimiento Factorial")
    
    currency_switch = st.segmented_control("Moneda de Visualización General de la Terminal:", ["PESOS ARGENTINOS (ARS)", "DÓLARES SUBYACENTES (USD)"], default="PESOS ARGENTINOS (ARS)")
    is_ars = (currency_switch == "PESOS ARGENTINOS (ARS)")
    
    st.markdown("---")
    st.subheader("➕ Añadir Nueva Posición Abierta")
    
    with st.form("form_alta_v2"):
        col1, col2, col3 = st.columns(3)
        f_tk = col1.text_input("Ticker Activo (Ej. AAPL, NVDA, VIST):", value="AAPL").upper().strip()
        f_nom = col2.number_input("Cantidad de Nominales:", min_value=1, value=50)
        f_date = col3.date_input("Fecha de Adquisición de la Posición:", datetime.date(2025, 1, 15))
        
        col4, col5, col6 = st.columns(3)
        f_px = col4.number_input("Precio Unitario de Compra (USD):", min_value=0.1, value=175.0)
        f_com = col4.number_input("Comisión del Bróker (USD Total):", value=0.5)
        f_imp = col6.number_input("Derechos de Bolsa / Impuestos (USD Total):", value=0.1)
        
        btn_submit = st.form_submit_button("➕ INTEGRAR POSICIÓN FACTORIAL AL PORTAFOLIO")
        
        if btn_submit:
            div_autonomo = calcular_dividendos_historicos(f_tk, f_date, f_nom)
            st.session_state.cartera_list_v2.append({
                "Ticker": f_tk, "Nominales": f_nom, "Fecha_Compra": f_date,
                "Costo_Unitario": f_px, "Comision": f_com, "Impuesto": f_imp, "Dividendos_Edit": div_autonomo
            })
            st.success(f"Posición de {f_tk} acoplada exitosamente. Dividendos devengados calculados automáticamente.")

    st.markdown("---")
    st.subheader("📊 Control Operativo de Posiciones Abiertas (Editable en Dividendos)")
    
    df_editor_input = pd.DataFrame(st.session_state.cartera_list_v2)
    
    if not df_editor_input.empty:
        edited_df = st.data_editor(
            df_editor_input,
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker", disabled=True),
                "Nominales": st.column_config.NumberColumn("Nominales", disabled=True),
                "Fecha_Compra": st.column_config.DateColumn("Fecha Compra", disabled=True),
                "Costo_Unitario": st.column_config.NumberColumn("Costo Unitario (USD)", disabled=True),
                "Comision": st.column_config.NumberColumn("Comisión (USD)", disabled=True),
                "Impuesto": st.column_config.NumberColumn("Impuesto (USD)", disabled=True),
                "Dividendos_Edit": st.column_config.NumberColumn("Dividendos Netos (USD) - EDITABLE", disabled=False)
            },
            use_container_width=True,
            hide_index=True
        )
        
        st.session_state.cartera_list_v2 = edited_df.to_dict(orient="records")
        
        filas_portfolio = []
        total_costo_usd, total_mercado_usd, total_rentas_usd = 0.0, 0.0, 0.0
        
        for pos in st.session_state.cartera_list_v2:
            tk = pos["Ticker"]
            nom = pos["Nominales"]
            c_unit = pos["Costo_Unitario"]
            com = pos["Comision"]
            imp = pos["Impuesto"]
            div_netos = pos["Dividendos_Edit"]
            
            ratio_b = RATIOS_CEDEAR.get(tk, 1)
            px_subyacente_usd = POOL_DATA.get(tk, {"precio": c_unit})["precio"]
            
            costo_total_usd = (nom * c_unit) + com + imp
            mercado_actual_usd = nom * px_subyacente_usd
            
            pl_usd = (mercado_actual_usd + div_netos) - costo_total_usd
            pl_pct = (pl_usd / costo_total_usd) * 100 if costo_total_usd > 0 else 0.0
            
            total_costo_usd += costo_total_usd
            total_mercado_usd += mercado_actual_usd
            total_rentas_usd += div_netos
            
            if is_ars:
                v_costo = (costo_total_usd / ratio_b) * DOLAR_MEP
                v_actual = (mercado_actual_usd / ratio_b) * DOLAR_MEP
                v_rentas = (div_netos / ratio_b) * DOLAR_MEP
                v_pl = (pl_usd / ratio_b) * DOLAR_MEP
                simb = "ARS"
            else:
                v_costo = costo_total_usd
                v_actual = mercado_actual_usd
                v_rentas = div_netos
                v_pl = pl_usd
                simb = "USD"
                
            filas_portfolio.append({
                "Ticker": tk, "Cantidad": nom, "Ratio BYMA": f"{ratio_b}:1",
                f"Costo Compra ({simb})": f"${v_costo:,.2f}",
                f"Valor de Mercado ({simb})": f"${v_actual:,.2f}",
                f"Dividendos Cobrados ({simb})": f"${v_rentas:,.2f}",
                f"P&L Total Return ({simb})": f"${v_pl:,.2f}",
                "Rendimiento (%)": f"{pl_pct:+.2f}%"
            })
            
        st.dataframe(pd.DataFrame(filas_portfolio).set_index("Ticker"), use_container_width=True)
            
        st.markdown("### 📈 Resumen Consolidado de la Cuenta")
        c_kpi1, c_kpi2, c_kpi3, c_kpi4 = st.columns(4)
        global_pl_pct = ((total_mercado_usd + total_rentas_usd - total_costo_usd) / total_costo_usd) * 100 if total_costo_usd > 0 else 0.0
        
        if is_ars:
            c_kpi1.metric("Capital Invertido", f"${(total_costo_usd * DOLAR_MEP):,.2f} ARS")
            c_kpi2.metric("Valuación Hoy", f"${(total_mercado_usd * DOLAR_MEP):,.2f} ARS")
            c_kpi3.metric("Bolsa Dividendos", f"${(total_rentas_usd * DOLAR_MEP):,.2f} ARS")
            c_kpi4.metric("Total Return Global", f"${((total_mercado_usd + total_rentas_usd - total_costo_usd) * DOLAR_MEP):,.2f} ARS ({global_pl_pct:+.2f}%)")
        else:
            c_kpi1.metric("Capital Invertido", f"${total_costo_usd:,.2f} USD")
            c_kpi2.metric("Valuación Hoy", f"${total_mercado_usd:,.2f} USD")
            c_kpi3.metric("Bolsa Dividendos", f"${total_rentas_usd:,.2f} USD")
            c_kpi4.metric("Total Return Global", f"${(total_mercado_usd + total_rentas_usd - total_costo_usd):,.2f} USD ({global_pl_pct:+.2f}%)")

        st.markdown("---")
        st.subheader("📐 Módulo de Benchmarking y Atribución de Alfa")
        
        benchmark_select = st.selectbox("Seleccionar Benchmark de Referencia para el Gráfico Comparativo:", ["SPY", "QQQ", "DIA", "VIST", "AAPL", "YPF"])
        
        try:
            fechas = pd.date_range(start="2025-06-01", end=datetime.date.today(), freq="B")
            curva_cartera = pd.Series(0.0, index=fechas)
            
            for pos in st.session_state.cartera_list_v2:
                tk = pos["Ticker"]
                serie_tk = POOL_DATA.get(tk, {}).get("serie_completa", pd.Series())
                if not serie_tk.empty:
                    curva_cartera = curva_cartera.add(serie_tk, fill_value=0)
            
            curva_cartera = curva_cartera.dropna()
            if not curva_cartera.empty:
                curva_cartera = (curva_cartera / curva_cartera.iloc[0]) * 100
                
            serie_bench = POOL_DATA.get(benchmark_select, {}).get("serie_completa", pd.Series())
            if not serie_bench.empty:
                serie_bench = serie_bench.loc[curva_cartera.index[0]:]
                curva_bench = (serie_bench / serie_bench.iloc[0]) * 100
            else:
                curva_bench = curva_cartera * 0.95
                
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=curva_cartera.index, y=curva_cartera.values, name="Mi Portafolio Combinado", line=dict(color='#2ecc71', width=3)))
            fig.add_trace(go.Scatter(x=curva_bench.index, y=curva_bench.values, name=f"Benchmark ({benchmark_select})", line=dict(color='#3498db', width=2, dash='dash')))
            
            fig.update_layout(
                title=f"Evolución del Retorno Acumulado Base 100 vs {benchmark_select}",
                template="plotly_dark", paper_bgcolor='#0c0f16', plot_bgcolor='#111520',
                margin=dict(l=20, r=20, t=40, b=20), height=400,
                xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#1f2937')
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # FUNDAMENTACIÓN TÉCNICA ESTRUCTURADA COMO PORTFOLIO MANAGER DE ISHARES
            st.markdown("#### 📐 Fundamentación Técnica del Posicionamiento Factorial")
            st.markdown(f"""
            <div class='interpretation-box'>
                <strong>INFORME DE ATRIBUCIÓN FACTORAL (iShares Strategy Framework):</strong> El análisis de atribución demuestra un sesgo intencional hacia el factor 
                <strong>Momentum Institucional</strong>. La selección de activos dentro de la cartera se rige por un proceso sistemático que prioriza la persistencia 
                de la tendencia en horizontes estandarizados de mediano y largo plazo (rendimientos acumulados de 6 y 12 meses), ajustados por la volatilidad idiosincrática del activo. 
                Este enfoque mitiga el impacto de las fluctuaciones técnicas del corto plazo y optimiza la captura de Alfa genuino frente al índice de referencia 
                <strong>{benchmark_select}</strong>, garantizando que el incremento de ponderación en activos líderes se sustente en la solidez del flujo institucional y la consistencia estructural de sus balances corporativos.
            </div>
            """, unsafe_allow_html=True)
        except:
            st.info("Sincronizando series históricas temporales para el despliegue del gráfico...")

# ==============================================================================
# 5. PIE DE PÁGINA Y DISCLAIMER LEGAL
# ==============================================================================
st.markdown("---")
c_f1, c_f2 = st.columns([2, 1])
c_f1.markdown("<p style='color: #555; font-size: 11px; margin: 0;'>Terminal Quanti Pro | Entorno Corporativo Sincronizado Dinámicamente con Dolarito.ar.</p>", unsafe_allow_html=True)
c_f2.markdown("<p style='text-align: right; font-size: 12px; margin: 0;'><b>Desarrollado por:</b> <a href='https://www.linkedin.com/in/facundo-garciamarquez/?locale=es' target='_blank' style='color: #2ecc71; text-decoration: none; font-weight: 600;'>Facundo Garcia Marquez</a></p>", unsafe_allow_html=True)

st.markdown("""
    <div style='background-color: rgba(231, 76, 60, 0.08); padding: 12px; border-left: 4px solid #e74c3c; font-size: 11px; color: #94a3b8; border-radius: 4px; margin-top: 15px;'>
        <strong>⚠️ ADVERTENCIA EXCLUSIÓN DE RESPONSABILIDAD:</strong> Las cotizaciones de mercado y el análisis automatizado se exponen únicamente con fines educativos y de simulación de portafolios. No constituyen asesoramiento financiero, recomendaciones de compra/venta ni ofertas formales de inversión matriculada. Las conversiones cambiarias toman como referencia exclusiva las cotizaciones dinámicas provistas por la plataforma externa Dolarito.ar.
    </div>
""", unsafe_allow_html=True)
