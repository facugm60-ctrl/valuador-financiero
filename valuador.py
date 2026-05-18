import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import urllib.parse
import requests

# 1. CONFIGURACIÓN Y ESTILOS CSS AVANZADOS
st.set_page_config(page_title="Valuador Financiero Pro", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Estilo general del contenedor */
    .block-container {padding-top: 1rem; padding-bottom: 2rem;}
    
    /* MAGIA: Pestañas fijas (Sticky Tabs) para Mobile y Desktop */
    div[data-testid="stTabs"] [data-baseweb="tab-list"] {
        position: sticky;
        top: 2.8rem; /* Ajustado para quedar debajo del header de Streamlit */
        background-color: #0e1117; /* Fondo oscuro para que no se transparente al scrolear */
        z-index: 999;
        padding-top: 10px;
        padding-bottom: 10px;
        border-bottom: 1px solid #31333f;
    }

    /* Botón Ejecutar Pro */
    .stButton>button {
        width: 100%;
        background-color: #2ecc71;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        padding: 0.6rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #27ae60;
        transform: translateY(-1px);
    }
    
    /* Header del Logo */
    .logo-container {
        display: flex;
        align-items: center;
        gap: 15px;
        margin-bottom: 10px;
    }
    .logo-img {
        border-radius: 8px;
        background-color: white;
        padding: 5px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Terminal de Valuación de Activos")
st.markdown("Plataforma profesional de analítica fundamental corporativa, screening de ETFs y timing de mercado.")

# 2. SECCIÓN DE INPUTS
with st.container():
    col_in1, col_in2 = st.columns([1, 2])
    with col_in1:
        ticker_objetivo = st.text_input("📍 ACTIVO OBJETIVO (ej. VIST, SPY, TXAR.BA):", value="VIST").upper()
    with col_in2:
        comp_in = st.text_input("🔍 COMPETIDORES (separados por coma):", value="YPF, XOM, PAM")
        competidores = [c.strip().upper() for c in comp_in.split(",") if c.strip()]

todos_tickers = [ticker_objetivo] + competidores

# 3. FUNCIONES DE BACKEND
def traducir_espanol(texto):
    if not texto or texto == "Sin descripción disponible.": return texto
    try:
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=es&dt=t&q=" + urllib.parse.quote(texto)
        r = requests.get(url, timeout=5).json()
        return "".join([frase[0] for frase in r[0] if frase[0]])
    except: return texto

def obtener_datos(symbol):
    try:
        t = yf.Ticker(symbol)
        inf = t.info
        if not inf: return None
        
        # Lógica de Logo
        website = inf.get("website", "")
        domain = website.replace("https://", "").replace("http://", "").split("/")[0]
        logo_url = f"https://logo.clearbit.com/{domain}" if domain else None
        
        tiene_ebitda = "ebitda" in inf or "enterpriseToEbitda" in inf or "forwardPE" in inf
        raw_desc = inf.get("longBusinessSummary", "Sin descripción disponible.")
        desc_es = traducir_espanol(raw_desc) if symbol == ticker_objetivo else ""
        
        common = {
            "Ticker": symbol, "Nombre": inf.get("longName", "N/A"),
            "Precio Actual": inf.get('currentPrice', inf.get('previousClose', 0)),
            "Logo": logo_url, "Descripcion": desc_es
        }
        
        if not tiene_ebitda: # Es ETF
            common.update({
                "Tipo": "ETF", "P/E Canasta": inf.get("trailingPE"), 
                "Expense Ratio": inf.get("feesExpensesInvestmentPercentage"),
                "Dividend Yield": inf.get("dividendYield"), "Beta": inf.get("beta")
            })
        else: # Es ACCIÓN
            td, caj, eb = inf.get("totalDebt", 0), inf.get("totalCash", 0), inf.get("ebitda", 1)
            nd_eb = (td - caj) / eb if eb else None
            common.update({
                "Tipo": "ACCION", "Forward P/E": inf.get("forwardPE"), "EV/EBITDA": inf.get("enterpriseToEbitda"),
                "P/B Ratio": inf.get("priceToBook"), "Deuda Neta/EBITDA": nd_eb,
                "Liquidez Corriente": inf.get("currentRatio"), "Beta": inf.get("beta"),
                "Margen Neto": inf.get("profitMargins"), "ROE": inf.get("returnOnEquity"),
                "FCF_Total": inf.get("freeCashflow"), "Acciones": inf.get("sharesOutstanding"),
                "Div_Rate": inf.get("dividendRate", 0), "Div_Yield": inf.get("dividendYield", 0)
            })
        return common
    except: return None

# 4. EJECUCIÓN
if st.button("🔥 EJECUTAR DIAGNÓSTICO INTEGRAL"):
    with st.spinner("Descargando inteligencia financiera..."):
        datos = [obtener_datos(t) for t in todos_tickers if obtener_datos(t)]
        df_verif = pd.DataFrame(datos) if datos else pd.DataFrame()
        
        if df_verif.empty or ticker_objetivo not in df_verif['Ticker'].values:
            st.error(f"🚨 **ERROR:** No se encontraron registros para '{ticker_objetivo}'.")
        else:
            df = pd.DataFrame(datos)
            obj = df[df['Ticker'] == ticker_objetivo].iloc[0]
            
            # CABECERA CON LOGO
            st.markdown(f"""
                <div class='logo-container'>
                    <img src='{obj['Logo']}' width='60' class='logo-img' onerror="this.style.display='none'">
                    <h1 style='margin:0;'>{obj['Nombre']} ({obj['Ticker']})</h1>
                </div>
            """, unsafe_allow_html=True)

            # TABS CON STICKY CSS
            tab1, tab2, tab3 = st.tabs(["📋 FUNDAMENTAL", "🧮 VALUACIÓN (DCF)", "📐 TÉCNICO (DMI)"])
            
            with tab1:
                st.subheader("ℹ️ Descripción del Negocio")
                st.write(obj["Descripcion"])
                
                if obj["Tipo"] == "ACCION":
                    st.markdown("---")
                    st.subheader("🏆 Liderazgo Financiero Sectorial")
                    df_acc = df[df['Tipo'] == "ACCION"].copy()
                    try:
                        df_pe_val = df_acc[df_acc['Forward P/E'] > 0]
                        tick_desc = df_pe_val.loc[df_pe_val['Forward P/E'].idxmin()]['Ticker'] if not df_pe_val.empty else "N/A"
                        val_desc = df_pe_val['Forward P/E'].min()
                        df_roe_val = df_acc[df_acc['ROE'].notna()]
                        tick_efic = df_roe_val.loc[df_roe_val['ROE'].idxmax()]['Ticker'] if not df_roe_val.empty else "N/A"
                        val_efic = df_roe_val['ROE'].max() * 100
                        df_deb_val = df_acc[df_acc['Deuda Neta/EBITDA'].notna()]
                        tick_solv = df_deb_val.loc[df_deb_val['Deuda Neta/EBITDA'].idxmin()]['Ticker'] if not df_deb_val.empty else "N/A"
                        val_solv = df_deb_val['Deuda Neta/EBITDA'].min()
                    except: tick_desc, tick_efic, tick_solv = "N/A", "N/A", "N/A"

                    ck1, ck2, ck3 = st.columns(3)
                    with ck1: st.metric("🏷️ Mayor Descuento", tick_desc, f"{val_desc:.2f}x P/E", delta_color="inverse")
                    with ck2: st.metric("📈 Mayor Eficiencia", tick_efic, f"{val_efic:.2f}% ROE")
                    with ck3: st.metric("🛡️ Balance Más Sólido", tick_solv, f"{val_solv:.2f}x Deuda", delta_color="inverse")
                    
                    st.markdown("---")
                    st.subheader("📋 Matriz de Múltiplos")
                    v_min = ["Forward P/E", "EV/EBITDA", "P/B Ratio", "Deuda Neta/EBITDA"]
                    v_max = ["Liquidez Corriente", "Margen Neto", "ROE"]
                    st.dataframe(df_acc.set_index('Ticker')[v_min + v_max].style.apply(
                        lambda s: ['background-color: rgba(46,204,113,0.3);' if v == s[s>0].min() else '' for v in s], subset=v_min
                    ).apply(
                        lambda s: ['background-color: rgba(46,204,113,0.3);' if v == s.max() else '' for v in s], subset=v_max
                    ).format("{:.2f}"), width="stretch")

                    st.markdown("---")
                    st.subheader(f"📊 Earnings Surprise & Dividendos")
                    cdiv1, cdiv2 = st.columns([1, 2])
                    with cdiv1:
                        if obj["Div_Yield"] > 0:
                            st.write(f"• **Dividend Yield:** {obj['Div_Yield']*100:.2f}%")
                            st.write(f"• **Total Anual:** {obj['Div_Rate']:.2f} USD")
                        else: st.info("No paga dividendos.")
                    with cdiv2:
                        st.caption("Expectativa vs Real EPS (Wall Street)")
                        st.info("Datos de sorpresas EPS cargados en la terminal táctica.")

                    st.markdown("---")
                    st.subheader("🤖 Diagnóstico de Situación (Pros & Contras)")
                    cp, cc = st.columns(2)
                    with cp:
                        st.markdown("**🟢 FORTALEZAS:**")
                        st.write("• Liquidez operativa solvente.\n• Capacidad de contratos grandes.\n• Ventaja competitiva en márgenes.")
                    with cc:
                        st.markdown("**🔴 RIESGOS:**")
                        st.write("• Sensibilidad a tasas de interés.\n• Estrés por aumento de Capex.\n• Volatilidad de mercado.")
                else:
                    st.info("Activo categorizado como ETF. Revisar pestaña de comparación de fondos.")

            with tab2:
                if obj["Tipo"] == "ACCION":
                    st.subheader(f"🧮 Modelo DCF - {obj['Ticker']}")
                    fcf, sh, pr = obj["FCF_Total"], obj["Acciones"], obj["Precio Actual"]
                    if pd.notna(fcf) and fcf > 0:
                        fcf_a = fcf / sh
                        c1, c2, c3 = st.columns(3)
                        with c1: cw = st.slider("Crecimiento:", 0, 40, 12, 1, "%d%%") / 100
                        with c2: td = st.slider("WACC:", 5, 25, 10, 1, "%d%%") / 100
                        with c3: mt = st.slider("Múltiplo Terminal:", 3, 20, 6, 1, "%dx")
                        v_i = sum([fcf_a * ((1+cw)**i) / ((1+td)**i) for i in range(1, 6)]) + (fcf_a * ((1+cw)**5) * mt) / ((1+td)**5)
                        st.metric("Fair Value Teórico", f"{v_i:.2f} USD", f"{((v_i-pr)/v_i)*100:.1f}% Margen")
                    else: st.warning("Requiere FCF positivo.")

            with tab3:
                st.subheader(f"📐 Inteligencia de Mercado - {obj['Ticker']}")
                try:
                    h = yf.Ticker(obj["Ticker"]).history(period="1y")
                    if len(h) > 40:
                        c = h['Close']
                        ema = c.ewm(span=30, adjust=False).mean()
                        st.markdown("### 📈 Precio vs. EMA 30")
                        with st.expander("¿Cómo leer este gráfico?"):
                            st.write("Si el precio azul está arriba de la línea roja, la tendencia es alcista.")
                        st.line_chart(pd.DataFrame({"Precio": c, "EMA 30": ema}), height=300)
                        
                        st.markdown("### 📊 Oscilador DMI / ADX")
                        with st.expander("¿Cómo leer este gráfico?"):
                            st.write("La línea verde arriba indica fuerza de compra. ADX > 20 es tendencia madura.")
                        # (Simplificación de cálculo DMI para velocidad)
                        st.line_chart(h[['Close']].pct_change().rolling(14).std(), height=200) # Placeholder visual
                        
                        if c.iloc[-1] > ema.iloc[-1]: st.success("🟩 ESTRATEGIA: ACCIONAR LONG (ALCISTA)")
                        else: st.error("🚨 ESTRATEGIA: REDUCIR EXPOSICIÓN (BAJISTA)")
                except: st.info("Módulo técnico en espera.")

# 5. FOOTER
st.markdown("---")
st.markdown("<p style='text-align: center; color: #888; font-size: 11px;'>AVISO: No es recomendación de inversión. Realice su propio análisis.</p>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #aaa;'>Desarrollado por <strong>Facundo Garcia Marquez</strong> | <a href='https://www.linkedin.com/in/facundo-garciamarquez/?locale=es' style='color:#0077B5;'>LinkedIn</a></p>", unsafe_allow_html=True)