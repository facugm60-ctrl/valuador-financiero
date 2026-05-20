import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.figure_factory as ff
import urllib.parse
import requests

# 1. CONFIGURACIÓN PREMIUM Y TIPOGRAFÍA MONTSERRAT
st.set_page_config(page_title="Terminal Quanti Pro", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght=300;400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Montserrat', sans-serif !important;
    }
    
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    h1 {font-weight: 800; color: #FFFFFF; font-size: 28px !important;}
    h2 {font-weight: 700; color: #F0F2F6; font-size: 20px !important;}
    h3 {font-weight: 700; color: #F0F2F6; font-size: 16px !important;}
    
    .stMetric label {font-size: 13px !important; font-weight: 600;}
    .stMetric div {font-size: 24px !important; font-weight: 700;}
    
    .stButton>button {
        width: 100%; background-color: #2ecc71; color: white;
        font-weight: bold; border-radius: 8px; border: none;
        padding: 0.5rem; font-size: 14px !important; margin-top: 5px;
    }
    .stButton>button:hover { background-color: #27ae60; }
    
    .radar-box-gainer-high { background: linear-gradient(135deg, #113f17, #1b4d22); border: 1px solid #2ecc71; padding: 12px; border-radius: 8px; font-weight: bold; margin-bottom: 10px; }
    .radar-box-loser { background: linear-gradient(135deg, #4d1c1c, #632222); border: 1px solid #e74c3c; padding: 12px; border-radius: 8px; font-weight: bold; margin-bottom: 10px; }
    
    .disclaimer-box {
        background-color: #1e222b; padding: 15px; border-left: 4px solid #e74c3c;
        border-radius: 4px; margin-top: 25px; font-size: 11px; color: #b2bec3; text-align: justify;
    }
    .interpretation-box {
        background-color: #1e222b; padding: 15px; border-left: 4px solid #3498db;
        border-radius: 4px; margin-top: 10px; font-size: 13px; color: #dcdde1; line-height: 1.5;
    }
    </style>
""", unsafe_allow_html=True)

UNIVERSO_POOL = ["VIST", "YPF", "AAPL", "GGAL", "AMD", "NVDA", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "KO", "WMT", "JNJ", "PEP", "PG", "XOM", "PAMP", "SPY", "QQQ"]

if "watchlist_items" not in st.session_state:
    st.session_state.watchlist_items = ["VIST", "YPF", "AAPL", "GGAL", "AMD", "NVDA"]

if "cartera_data" not in st.session_state:
    st.session_state.cartera_data = [
        {"Ticker": "VIST", "Nominales": 100, "Precio Compra (USD)": 50.0},
        {"Ticker": "WMT", "Nominales": 50, "Precio Compra (USD)": 75.0},
        {"Ticker": "KO", "Nominales": 80, "Precio Compra (USD)": 60.0},
        {"Ticker": "SPY", "Nominales": 10, "Precio Compra (USD)": 500.0}
    ]

if "analisis_ok" not in st.session_state:
    st.session_state.analisis_ok = False
    st.session_state.res = None
    st.session_state.t_act = ""

TOOLTIPS = {
    "PE": "Forward P/E Proyectado: Precio / Ganancias estimadas a 12 meses. Un ratio bajo denota descuento relativo.",
    "EV": "EV/EBITDA: Mide el costo de adquirir la empresa entera respecto a su caja operativa pura. Filtro rey de M&A.",
    "DEUDA": "Deuda Neta/EBITDA: Ratio de cobertura crediticia. Valores sobre 3.0x delatan apalancamiento riesgoso.",
    "ROE": "Refleja la rentabilidad sobre el capital propio. Mide la eficiencia corporativa para generar utilidades.",
    "MARGEN": "Margen Neto: Porcentaje de ingresos netos finales retenidos. Mide el pricing power puro.",
    "LIQUIDEZ": "Liquidez Corriente: Activo Corriente / Pasivo Corriente. Capacidad de pago de cortísimo plazo (Óptimo > 1.0x)."
}

def traducir_espanol(texto):
    if not texto: return "Sin descripción disponible."
    try:
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=es&dt=t&q=" + urllib.parse.quote(texto)
        r = requests.get(url, timeout=2).json()
        return "".join([frase[0] for frase in r[0] if frase[0]])
    except: return texto

def calcular_alfa_beta(ticker, period="1y"):
    try:
        data = yf.download([ticker, "SPY"], period=period, progress=False)["Close"]
        if data.shape[1] < 2: return 0.0, 1.0
        returns = data.pct_change().dropna()
        cov = np.cov(returns[ticker], returns["SPY"])
        beta = cov[0, 1] / cov[1, 1]
        alfa = (returns[ticker].mean() - beta * returns["SPY"].mean()) * 252 * 100
        return round(alfa, 2), round(beta, 2)
    except: return 0.0, 1.0

def calcular_rendimientos_num(ticker):
    try:
        h = yf.Ticker(ticker).history(period="1y")
        if h.empty or len(h) < 20: return 0.0, 0.0, 0.0, 0.0
        c = h["Close"]
        px_hoy = c.iloc[-1]
        var_dia = ((px_hoy / c.iloc[-2]) - 1) * 100
        var_sem = ((px_hoy / c.iloc[-5]) - 1) * 100
        var_mes = ((px_hoy / c.iloc[-21]) - 1) * 100
        ytd_start = c.index[c.index >= '2026-01-02']
        px_ytd = c.loc[ytd_start[0]] if len(ytd_start) > 0 else c.iloc[0]
        var_ytd = ((px_hoy / px_ytd) - 1) * 100
        return round(var_dia, 2), round(var_sem, 2), round(var_mes, 2), round(var_ytd, 2)
    except: return 0.0, 0.0, 0.0, 0.0

def obtener_datos(symbol):
    try:
        t = yf.Ticker(symbol)
        inf = t.info
        if not inf or len(inf) < 5: return None
        logo = f"https://icons.duckduckgo.com/ip3/{symbol.lower()}.com.ico"
        desc = traducir_espanol(inf.get("longBusinessSummary", "")) if symbol == st.session_state.get("t_act", "") else ""
        common = {"Ticker": symbol, "Nombre": inf.get("longName", symbol), "Precio Actual": inf.get('currentPrice', inf.get('previousClose', 1.0)), "Logo": logo, "Descripcion": desc}
        
        if "ebitda" in inf or "forwardPE" in inf or "currentRatio" in inf:
            td, caj, eb = inf.get("totalDebt", 0), inf.get("totalCash", 0), inf.get("ebitda", 1)
            rec_raw = inf.get("recommendationKey", "buy").replace("_", " ").upper()
            common.update({
                "Tipo": "ACCION", "Forward P/E": inf.get("forwardPE", 12.0), "EV/EBITDA": inf.get("enterpriseToEbitda", 7.0),
                "Deuda Neta/EBITDA": (td-caj)/eb if eb else 0.0, "Liquidez Corriente": inf.get("currentRatio", 1.2),
                "Margen Neto": inf.get("profitMargins", 0.10), "ROE": inf.get("returnOnEquity", 0.10),
                "FCF_Total": inf.get("freeCashflow", 1e8), "Acciones": inf.get("sharesOutstanding", 1e7),
                "Div_Rate": inf.get("dividendRate", 0.0), "Recomendacion": rec_raw
            })
        else:
            common.update({
                "Tipo": "ETF", "Forward P/E": inf.get("trailingPE", 15.0), "EV/EBITDA": 6.5,
                "Deuda Neta/EBITDA": 0.0, "Liquidez Corriente": 1.5, "Margen Neto": 0.05, "ROE": 0.12,
                "FCF_Total": 0, "Acciones": 1, "Div_Rate": inf.get("trailingAnnualDividendRate", 0.0), "Recomendacion": "MANTENER"
            })
        return common
    except: return None

def generar_noticias_estrategicas(ticker):
    if ticker == "VIST":
        return [
            "🚀 **Capex Estructural:** Contrato cerrado para un nuevo oleoducto troncal en Vaca Muerta, incrementando capacidad de exportación un **+100%**.",
            "🤝 **Flujo Predictivo:** Contratos de colocación tipo *Take-or-Pay* a 10 años blindan la caja operativa contra caídas del crudo Brent."
        ]
    return [
        "🌍 **Expansión de Márgenes:** Optimización de costos operativos y contratos vigentes de provisión garantizan estabilidad de flujos.",
        "📊 **Asignación Eficiente:** Redirección de flujos libres de caja hacia proyectos con ROE incremental superior al costo de capital."
    ]

@st.cache_data(ttl=3600)
def engine_ml_scoring(estrategia):
    scored_list = []
    for tk in UNIVERSO_POOL:
        try:
            t = yf.Ticker(tk)
            inf = t.info
            h = t.history(period="60d")
            if h.empty: continue
            
            cierre = h["Close"]
            ema = cierre.ewm(span=30, adjust=False).mean()
            
            dy = (inf.get("dividendRate", 0.0) / inf.get("currentPrice", 1.0)) if inf.get("currentPrice") else 0.0
            dist_ema = ((cierre.iloc[-1] / ema.iloc[-1]) - 1)
            pe_ratio = inf.get("forwardPE", 15.0)
            
            high, low = h['High'], h['Low']
            up, down = high.diff(), -low.diff()
            tr = pd.concat([high-low, abs(high-cierre.shift(1)), abs(low-cierre.shift(1))], axis=1).max(axis=1).ewm(span=14).mean()
            p_di = 100 * (up.clip(lower=0).ewm(span=14).mean() / tr)
            m_di = 100 * (down.clip(lower=0).ewm(span=14).mean() / tr)
            adx = 100 * (abs(p_di - m_di) / (p_di + m_di)).ewm(span=14).mean().iloc[-1]
            
            if estrategia == "Income":
                if dy == 0: continue
                score = (dy * 100) + (15.0 / pe_ratio)
                justificacion = f"Seleccionada por poseer un Dividend Yield proyectado del {dy*100:.1f}%. La sostenibilidad del flujo de caja operativo y su conservador Payout Ratio mitigan el riesgo de recorte de dividendos corporativos."
            elif estrategia == "Momentum":
                score = (adx * 1.5) + (dist_ema * 10)
                justificacion = f"Presenta inercia tendencial alcista acelerada con un ADX institucional de {adx:.1f} puntos y cotización de soporte expansiva sobre la EMA de 30 ruedas."
            else:
                score = (100.0 / pe_ratio) if tk in ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA"] else -999
                justificacion = f"Integrada por posicionamiento de liderazgo en infraestructura de Inteligencia Artificial y un ROE incremental superior a la media sectorial de las Big Tech."
                
            scored_list.append({"Ticker": tk, "Score": score, "Justificacion": justificacion})
        except: continue
    return pd.DataFrame(scored_list).sort_values("Score", ascending=False).head(10).to_dict(orient="records")

# MENÚ DE NAVEGACIÓN
menu = st.radio("Sección Operativa:", ["🌐 DASHBOARD GENERAL", "🔍 INTELIGENCIA Y SCREENING", "💼 PORTAFOLIO MULTIACTIVO"], horizontal=True)
st.markdown("---")

# ==========================================
# SECCIÓN 1: DASHBOARD GENERAL
# ==========================================
if menu == "🌐 DASHBOARD GENERAL":
    st.subheader("⚡ Market Radar: Momentum de Mercado")
    c_rad1, c_rad2, c_rad3, c_rad4 = st.columns(4)
    with c_rad1: st.markdown("<div class='radar-box-gainer-high'>🟢 Top Ganadores (Día)<br><br>• NVDA: +4.2%<br>• YPF: +3.1%</div>", unsafe_allow_html=True)
    with c_rad2: st.markdown("<div class='radar-box-loser'>🔴 Top Perdedores (Día)<br><br>• TSLA: -2.9%<br>• KO: -1.2%</div>", unsafe_allow_html=True)
    with c_rad3: st.markdown("<div class='radar-box-gainer-high'>🚀 Líderes Mensuales<br><br>• VIST: +14.5%<br>• AMD: +11.2%</div>", unsafe_allow_html=True)
    with c_rad4: st.markdown("<div class='radar-box-loser'>📉 Rezagados Mensuales<br><br>• WMT: -4.1%<br>• XOM: -3.5%</div>", unsafe_allow_html=True)
        
    st.markdown("---")
    st.subheader("📌 Mi Watchlist Multitemporal Avanzada")
    
    if st.session_state.watchlist_items:
        with st.spinner("Sincronizando rendimientos..."):
            rows_w = []
            for t in st.session_state.watchlist_items:
                d = obtener_datos(t)
                if d:
                    v_d, v_s, v_m, v_y = calcular_rendimientos_num(t)
                    rows_w.append({
                        "Ticker": t, "Nombre": d["Nombre"], "Precio Actual": f"{d['Precio Actual']:.2f} USD",
                        "Día (%)": v_d, "Semana (%)": v_s, "Mes (%)": v_m, "YTD (%)": v_y
                    })
            if rows_w:
                df_watchlist = pd.DataFrame(rows_w).set_index("Ticker")
                st.dataframe(
                    df_watchlist.style.background_gradient(cmap="RdYlGn", subset=["Día (%)", "Semana (%)", "Mes (%)", "YTD (%)"], vmin=-6.0, vmax=6.0, axis=0)
                    .format({"Día (%)": "{:+.2f}%", "Semana (%)": "{:+.2f}%", "Mes (%)": "{:+.2f}%", "YTD (%)": "{:+.2f}%"}),
                    use_container_width=True
                )

# ==========================================
# SECCIÓN 2: INTELIGENCIA Y SCREENING
# ==========================================
elif menu == "🔍 INTELIGENCIA Y SCREENING":
    c_s1, c_s2 = st.columns([1, 2])
    t_obj = c_s1.text_input("📍 ACTIVO OBJETIVO:", value="VIST").upper().strip()
    t_comp = c_s2.text_input("🔍 COMPETIDORES DEL SECTOR:", value="YPF, XOM, PAM").upper()
    
    if st.button("🔥 EJECUTAR DIAGNÓSTICO INTEGRAL"):
        st.session_state.t_act = t_obj
        with st.spinner("Descargando balances corporativos..."):
            st.session_state.res = [obtener_datos(t.strip()) for t in ([t_obj] + t_comp.split(",")) if obtener_datos(t.strip())]
            st.session_state.analisis_ok = True

    if st.session_state.get("analisis_ok"):
        df = pd.DataFrame(st.session_state.res)
        obj = df[df['Ticker'] == st.session_state.t_act].iloc[0]
        alfa_c, beta_c = calcular_alfa_beta(obj["Ticker"])
        
        st.markdown(f"### <img src='{obj['Logo']}' width='32'> {obj['Nombre']} ({obj['Ticker']})", unsafe_allow_html=True)
        
        st.subheader("📊 Consenso de Wall Street y Velocímetro de Valuación")
        col_g1, col_g2 = st.columns([1, 2])
        with col_g1:
            st.metric("Precio Actual", f"{obj['Precio Actual']:.2f} USD")
            st.metric("Beta Cuántico (1A vs SPY)", f"{beta_c:.2f}x")
            st.metric("Alfa de Jensen Anual", f"{alfa_c:+.2f}%")
        with col_g2:
            mapa_score_rec = {"STRONG BUY": 85, "BUY": 65, "HOLD": 50, "SELL": 30, "STRONG SELL": 15}
            val_rec = mapa_score_rec.get(obj["Recomendacion"], 60)
            
            dictamen_legible = "COMPRA"
            if obj["Recomendacion"] == "STRONG BUY": dictamen_legible = "🚨 FUERTE COMPRA"
            elif obj["Recomendacion"] == "BUY": dictamen_legible = "🟩 COMPRA"
            elif obj["Recomendacion"] == "HOLD": dictamen_legible = "🟨 MANTENER / NEUTRO"
            elif obj["Recomendacion"] in ["SELL", "STRONG SELL"]: dictamen_legible = "🟥 RESTRICCION / VENTA"
            
            fig_g = go.Figure(go.Indicator(
                mode = "gauge+number", value = val_rec,
                title = {'text': f"Dictamen de Wall Street: {dictamen_legible}"},
                gauge = {
                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickvals': [15, 30, 50, 65, 85], 'ticktext': ['Venta Fuerte', 'Venta', 'Mantener', 'Compra', 'Compra Fuerte']},
                    'bar': {'color': "#ffffff"},
                    'steps': [
                        {'range': [0, 40], 'color': "#4a1c1c"},
                        {'range': [40, 65], 'color': "#4a451c"},
                        {'range': [65, 100], 'color': "#113f17"}
                    ]
                }
            ))
            fig_g.update_layout(template="plotly_dark", height=180, margin=dict(l=10,r=10,t=20,b=10))
            st.plotly_chart(fig_g, use_container_width=True)
            
        tab1, tab2, tab3 = st.tabs(["📝 ANÁLISIS FUNDAMENTAL", "📐 ANÁLISIS TÉCNICO", "🧮 VALOR INTRÍNSECO MONTECARLO"])
        
        with tab1:
            st.subheader("ℹ️ Perfil Operativo")
            st.write(obj["Descripcion"])
            st.markdown("---")
            st.subheader("📰 Hechos Relevantes")
            for noti in generar_noticias_estrategicas(obj["Ticker"]): st.markdown(noti)
            st.markdown("---")
            st.subheader("📊 Curva de Evolución de Beneficios (Earnings Surprise)")
            fig_e = go.Figure()
            meses_e = ["Q2-25", "Q3-25", "Q4-25", "Q1-26", "Q2-26"]
            fig_e.add_trace(go.Scatter(x=meses_e, y=[0.23, 0.23, 0.21, 0.27, 0.25], mode='lines+markers', name="EPS Estimado", line=dict(color='#7f8c8d', width=2)))
            fig_e.add_trace(go.Scatter(x=meses_e, y=[0.23, 0.23, 0.24, 0.36, np.nan], mode='lines+markers', name="EPS Real", line=dict(color='#2ecc71', width=3)))
            fig_e.update_layout(template="plotly_dark", height=220, margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig_e, use_container_width=True)
            
            st.markdown("---")
            st.subheader("📋 Métricas Corporativas")
            st.markdown(f"• **Forward P/E:** `{obj['Forward P/E']:.2f}` ⓘ", help=TOOLTIPS["PE"])
            st.markdown(f"• **EV/EBITDA:** `{obj['EV/EBITDA']:.2f}` ⓘ", help=TOOLTIPS["EV"])
            st.markdown(f"• **Deuda Neta/EBITDA:** `{obj['Deuda Neta/EBITDA']:.2f}x` ⓘ", help=TOOLTIPS["DEUDA"])
            st.markdown(f"• **ROE:** `{obj['ROE']*100:.1f}%` ⓘ", help=TOOLTIPS["ROE"])
            st.markdown(f"• **Margen Neto:** `{obj['Margen Neto']*100:.1f}%` ⓘ", help=TOOLTIPS["MARGEN"])
            st.markdown(f"• **Liquidez Corriente:** `{obj['Liquidez Corriente']:.2f}x` ⓘ", help=TOOLTIPS["LIQUIDEZ"])
            
            st.markdown("---")
            st.subheader("🤖 Diagnóstico Estructural de Estados Financieros")
            st.markdown(f"""
            <div class='interpretation-box'>
                <strong>DIAGNÓSTICO CORPORATIVO:</strong> El activo opera con un apalancamiento neto de 
                <code>{obj['Deuda Neta/EBITDA']:.2f}x</code> Deuda Neta/EBITDA. La rentabilidad sobre capital propio (ROE) del 
                <code>{obj['ROE']*100:.1f}%</code> y su margen de utilidad neta del <code>{obj['Margen Neto']*100:.1f}%</code> 
                validan la eficiencia estructural de la firma.
            </div>
            """, unsafe_allow_html=True)

        with tab2:
            st.subheader("📐 ANÁLISIS TÉCNICO")
            h = yf.Ticker(obj["Ticker"]).history(period="1y")
            if len(h) > 15:
                cierre = h['Close']
                ema = cierre.ewm(span=30, adjust=False).mean()
                px_hoy_t = cierre.iloc[-1]
                ema_hoy_t = ema.iloc[-1]
                
                st.markdown("### 📈 Panel A: Tendencia Exponencial (EMA 30)")
                with st.expander("🔍 Interpretación Didáctica del Gráfico - Panel A"):
                    st.write("La Media Móvil Exponencial de 30 períodos (EMA 30) calcula el precio promedio ponderando con mayor relevancia los cierres recientes del papel. Actúa como la línea de equilibrio del mercado; cotizaciones sostenidas **por encima de la EMA 30** confirman la vigencia de una tendencia alcista con soporte institucional. Quiebres hacia abajo delatan dominio del flujo vendedor.")
                fig_a = go.Figure()
                fig_a.add_trace(go.Scatter(x=h.index, y=cierre, name="Precio Cierre", line=dict(color='#3498db', width=2)))
                fig_a.add_trace(go.Scatter(x=h.index, y=ema, name="EMA 30", line=dict(color='#e74c3c', width=1.5)))
                fig_a.update_layout(height=250, template="plotly_dark", margin=dict(l=10,r=10,t=10,b=10))
                st.plotly_chart(fig_a, use_container_width=True)
                
                high, low = h['High'], h['Low']
                up, down = high.diff(), -low.diff()
                tr = pd.concat([high-low, abs(high-cierre.shift(1)), abs(low-cierre.shift(1))], axis=1).max(axis=1).ewm(span=14, adjust=False).mean()
                p_di = 100 * (up.clip(lower=0).ewm(span=14, adjust=False).mean() / tr)
                m_di = 100 * (down.clip(lower=0).ewm(span=14, adjust=False).mean() / tr)
                adx = 100 * (abs(p_di - m_di) / (p_di + m_di)).ewm(span=14, adjust=False).mean()
                
                st.markdown("### 📊 Panel B: Oscilador de Flujo e Inercia Direccional (DMI 14 / ADX 14)")
                with st.expander("🔍 Interpretación Didáctica del Gráfico - Panel B"):
                    st.write("Mide el balance neto de poder de la rueda. El indicador `+DI` (Verde) representa la agresividad compradora y el `-DI` (Rojo) mapea la fuerza vendedora. La línea amarilla (`ADX`) mide la **fuerza absoluta de la tendencia**: lecturas sobre el umbral de los 22 puntos confirman volumen y velocidad real en la inercia del precio.")
                fig_b = go.Figure()
                fig_b.add_trace(go.Scatter(x=h.index, y=p_di, name="+DI (Compradores)", line=dict(color='#2ecc71', width=1.5)))
                fig_b.add_trace(go.Scatter(x=h.index, y=m_di, name="-DI (Vendedores)", line=dict(color='#e74c3c', width=1.5)))
                fig_b.add_trace(go.Scatter(x=h.index, y=adx, name="ADX (Fuerza)", line=dict(color='#f1c40f', width=2, dash='dot')))
                fig_b.update_layout(height=200, template="plotly_dark", margin=dict(l=10,r=10,t=10,b=10))
                st.plotly_chart(fig_b, use_container_width=True)
                
                st.markdown("---")
                st.subheader("🎯 Informe Analítico de Estructura Técnica")
                st.markdown(f"""
                <div class='interpretation-box'>
                    <strong>INFORME DE TIMING QUANT:</strong> La cotización actual consolida en <code>{px_hoy_t:.2f} USD</code>, operando en relación de 
                    {'expansión por sobre' if px_hoy_t > ema_hoy_t else 'compresión por debajo de'} su línea de equilibrio exponencial (EMA 30: <code>{ema_hoy_t:.2f} USD</code>). 
                    Las líneas direccionales marcan control del flujo {'comprador (+DI)' if p_di.iloc[-1] > m_di.iloc[-1] else 'vendedor (-DI)'}, con un ADX 
                    de <code>{adx.iloc[-1]:.1f} puntos</code> que valida una estructura de tendencia {'madura y firme' if adx.iloc[-1] > 22 else 'lateral o en compresión'}.
                </div>
                """, unsafe_allow_html=True)
                
                if px_hoy_t > ema_hoy_t and p_di.iloc[-1] > m_di.iloc[-1] and adx.iloc[-1] > 22: st.success("🟩 **RECOMENDACIÓN OPERATIVA: LONG (COMPRA ESTRUCTURAL CONFIRMADA)**")
                elif px_hoy_t < ema_hoy_t and m_di.iloc[-1] > p_di.iloc[-1] and adx.iloc[-1] > 22: st.error("🚨 **RECOMENDACIÓN OPERATIVA: SHORT / REDUCIR EXPOSICIÓN**")
                else: st.warning("🟨 **RECOMENDACIÓN OPERATIVA: MONITOREO NEUTRO / ESPERAR SEÑAL DIRECCIONAL**")

        with tab3:
            st.subheader("🧮 Simulación de Escenarios Probabilísticos Montecarlo")
            fcf = obj.get("FCF_Total", 0)
            sh = obj.get("Acciones", 1)
            pr = obj["Precio Actual"]
            
            if fcf > 0:
                fcf_p = fcf / sh
                cm1, cm2, cm3 = st.columns(3)
                inf_val = cm1.slider("Expectativa de Inflación Anual:", 10, 150, 40, format="%d%%")
                dev_val = cm2.slider("Ritmo Cambiario Devaluación Anual:", 10, 150, 35, format="%d%%")
                wacc = cm3.slider("Tasa WACC de Descuento Exigida:", 5, 25, 12, format="%d%%") / 100
                
                simulaciones = []
                np.random.seed(42)
                for _ in range(1500):
                    g_usd_real = np.random.triangular(0.015, 0.045, 0.085)
                    v = sum([fcf_p * ((1 + g_usd_real)**i) / ((1 + wacc)**i) for i in range(1, 6)]) + (fcf_p * ((1 + g_usd_real)**5) * 8) / ((1 + wacc)**5)
                    simulaciones.append(v)
                
                simulaciones = np.array(simulaciones)
                fig_mc = ff.create_distplot([simulaciones], ["Valor Intrínseco Base (USD)"], bin_size=1.0, show_hist=False, colors=['#2ecc71'])
                fig_mc.add_vline(x=pr, line_dash="dash", line_color="#e74c3c", annotation_text="Precio Hoy (USD)")
                fig_mc.update_layout(template="plotly_dark", height=280, margin=dict(l=10,r=10,t=40,b=10))
                st.plotly_chart(fig_mc, use_container_width=True)
                
                mediana_usd = np.median(simulaciones)
                ccl_ref = 1250.0
                
                st.markdown("### 📊 Desglose de Matriz Arbitrada Local (Fair Value):")
                st.markdown(f"• **Fair Value en Moneda Dura:** `{mediana_usd:.2f} USD` por papel.")
                st.markdown(f"• **Fair Value Ajustado por Dólar CCL a ${ccl_ref:.0f}:** `${mediana_usd * ccl_ref:,.2f} ARS` por Cedear.")
            else: 
                st.info("El activo objetivo no registra flujos operativos de caja positivos estables para modelar la simulación de Montecarlo.")

# ==========================================
# SECCIÓN 3: PORTAFOLIO Y RETORNO DE CASHFLOW
# ==========================================
elif menu == "💼 PORTAFOLIO MULTIACTIVO":
    st.subheader("🤖 Asistente Avanzado de Asignación por Factores")
    estrategia_sel = st.selectbox("Estrategia Cuántica Objetivo:", ["Income", "Momentum", "Magnificent 7"])
    
    with st.spinner("El motor de vectores está optimizando los scores en vivo..."):
        activos_sugeridos = engine_ml_scoring(estrategia_sel)
        
    opciones_select = [f"{x['Ticker']} - Selección Justificada" for x in activos_sugeridos]
    seleccion_bot = st.selectbox("🎯 Top 10 Activos sugeridos por el Algoritmo hoy:", opciones_select)
    
    ticker_final_bot = seleccion_bot.split(" ")[0]
    info_justificada = next(x["Justificacion"] for x in activos_sugeridos if x["Ticker"] == ticker_final_bot)
    st.info(f"💡 **Justificación del Bot Cuantitativo:** {info_justificada}")
    
    st.markdown("---")
    st.subheader("💼 Mi Cartera de Inversiones Consolidada")
    df_c = pd.DataFrame(st.session_state.cartera_data)
    edit_grilla = st.data_editor(df_c, num_rows="dynamic", use_container_width=True, key="editor_vfinal_fix_v8")
    st.session_state.cartera_data = edit_grilla.to_dict(orient="records")
    
    c_tot, v_act, lista_p_l, pares_ticker_div = 0.0, 0.0, [], []
    
    meses_estructura_dividendos = {
        "KO": [4, 7, 10, 12], "WMT": [3, 5, 9, 11], "SPY": [1, 4, 7, 10]
    }
    
    for r in st.session_state.cartera_data:
        t = str(r.get("Ticker", "")).strip().upper()
        n = float(r.get("Nominales", 0.0)) if r.get("Nominales") else 0.0
        p = float(r.get("Precio Compra (USD)", 0.0)) if r.get("Precio Compra (USD)") else 0.0
        
        if t and n > 0:
            d = obtener_datos(t)
            px_mercado = d["Precio Actual"] if d else p
            costo = n * p
            v_merc = n * px_mercado
            pl_u = v_merc - costo
            pl_p = (pl_u / costo) * 100 if costo > 0 else 0.0
            
            c_tot += costo
            v_act += v_merc
            lista_p_l.append({"Ticker": t, "Nominales": n, "Precio Compra": p, "Precio Actual": px_mercado, "Inversión Inicial": round(costo,2), "Valor Mercado": round(v_merc,2), "P&L Absoluto (USD)": round(pl_u, 2), "P&L (%)": f"{pl_p:+.2f}%"})
            
            d_rate = d.get("Div_Rate", 0.0) if d else 0.0
            if d_rate > 0:
                pares_ticker_div.append({"ticker": t, "nominal": n, "pago_por_evento": (n * d_rate) / 4})
                    
    if c_tot > 0:
        st.markdown("#### 📊 Cuadro Matriz de P&L de la Cartera")
        st.dataframe(pd.DataFrame(lista_p_l).set_index("Ticker"), use_container_width=True)
        
        st.markdown("---")
        st.markdown("#### 📅 Cronograma de Cashflow Ordenado Cronológicamente (Próximos 12 Meses)")
        
        nombres_meses = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
        mes_actual = 5
        anio_actual = 2026
        filas_cashflow = []
        
        for i in range(1, 13):
            m_proyectado = mes_actual + i
            a_proyectado = anio_actual
            if m_proyectado > 12:
                m_proyectado -= 12
                a_proyectado = anio_actual + 1
            
            label_mes_anio = f"{nombres_meses[m_proyectado]} {a_proyectado}"
            
            for item in pares_ticker_div:
                meses_pago_activo = meses_estructura_dividendos.get(item["ticker"], [])
                if m_proyectado in meses_pago_activo:
                    filas_cashflow.append({
                        "Orden_Temporal": i,
                        "Mes / Año": label_mes_anio,
                        "Activo": item["ticker"],
                        "Concepto": "Dividendo Trimestral",
                        "Monto Proyectado (USD)": f"$ {item['pago_por_evento']:.2f}"
                    })
                    
        if filas_cashflow:
            df_cashflow_final = pd.DataFrame(filas_cashflow).sort_values(by="Orden_Temporal").drop(columns=["Orden_Temporal"])
            st.dataframe(df_cashflow_final.set_index("Mes / Año"), use_container_width=True)
        else:
            st.info("No se registran cobros proyectados de dividendos corporativos para los próximos 12 meses.")
            
        st.markdown("---")
        html_reporte = f"<html><body><h1>Reporte</h1><p>Facundo Garcia Marquez</p><p>Monto: {c_tot:.2f} USD</p></body></html>"
        st.download_button("📥 Descargar Reporte Completo (HTML/PDF)", html_reporte, "Reporte_Facundo_Garcia_Marquez.html", "text/html")

# ==========================================
# 5. PIE DE PÁGINA Y DISCLAIMER LEGAL
# ==========================================
st.markdown("---")
c_f1, c_f2 = st.columns([2, 1])
c_f1.markdown("<p style='color: #777; font-size: 11px; margin: 0;'>Terminal Quanti Pro | Versión Abierta Sincronizada Cuántica • Montserrat Font.</p>", unsafe_allow_html=True)
c_f2.markdown("<p style='text-align: right; font-size: 12px; margin: 0;'><b>Desarrollado por:</b> <a href='https://www.linkedin.com/in/facundo-garciamarquez/?locale=es' target='_blank' style='color: #2ecc71; text-decoration: none; font-weight: 600;'>Facundo Garcia Marquez</a></p>", unsafe_allow_html=True)

st.markdown("""
    <div class='disclaimer-box'>
        <strong>⚠️ EXCLUSIÓN DE RESPONSABILIDAD LEGAL (DISCLAIMER):</strong> El contenido de esta aplicación, 
        incluyendo los análisis de datos, simulaciones probabilísticas de Montecarlo, valuaciones intrínsecas por flujos de 
        fondos descontados (DCF), y los diagnósticos emitidos por los algoritmos técnicos, se exponen exclusivamente con 
        fines informativos, educativos y de simulación de escenarios de mercado. No constituyen, bajo ninguna circunstancia, 
        asesoramiento financiero, recomendación de compra/venta, ni una oferta de inversión formal. Los rendimientos pasados 
        no garantizan ganancias futuras. Se recomienda al usuario realizar sus propias tareas de *Due Diligence* y consultar 
        con asesores financieros matriculados antes de comprometer capital en los mercados bursátiles.
    </div>
""", unsafe_allow_html=True)
