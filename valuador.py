import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import urllib.parse
import requests

# 1. CONFIGURACIÓN DE PÁGINA Y SUPER-INYECCIÓN CSS PARA STICKY TABS
st.set_page_config(page_title="Valuador Financiero Pro", layout="wide", initial_sidebar_state="collapsed")

# Forzamos por CSS que el contenedor de pestañas se clave arriba al hacer scroll
st.markdown("""
    <style>
    /* Estilo general del contenedor principal */
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    
    /* CRUCIAL: Forzar barra de navegación fija (Sticky Tabs) */
    [data-testid="stTabs"] > div:first-child {
        position: -webkit-sticky !important;
        position: sticky !important;
        top: 0px !important;
        background-color: #0e1117 !important; /* Mismo color del fondo oscuro de Streamlit */
        z-index: 999999 !important;
        padding-top: 15px !important;
        padding-bottom: 10px !important;
        border-bottom: 2px solid #31333f !important;
    }
    
    /* Ajuste para que el texto de las pestañas resalte más en celulares */
    button[data-testid="stMarkdownContainer"] p {
        font-size: 15px !important;
        font-weight: 700 !important;
    }

    /* Estilo del Botón de Ejecución */
    .stButton>button {
        width: 100%;
        background-color: #2ecc71;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        padding: 0.7rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #27ae60;
        transform: translateY(-1px);
    }
    
    /* Contenedor del Título y Logo alineados */
    .header-inline {
        display: flex;
        align-items: center;
        margin-top: 15px;
        margin-bottom: 15px;
        gap: 15px;
    }
    .brand-logo {
        background-color: #ffffff;
        padding: 6px;
        border-radius: 10px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
        display: inline-block;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Terminal de Valuación de Activos")
st.markdown("Plataforma profesional de analítica fundamental corporativa y timing de mercado.")

# 2. ENTRADAS DE USUARIO
with st.container():
    col_in1, col_in2 = st.columns([1, 2])
    with col_in1:
        ticker_objetivo = st.text_input("📍 ACTIVO OBJETIVO:", value="VIST").upper()
    with col_in2:
        comp_in = st.text_input("🔍 COMPETIDORES DEL SECTOR (separados por coma):", value="YPF, XOM, PAM")
        competidores = [c.strip().upper() for c in comp_in.split(",") if c.strip()]

todos_tickers = [ticker_objetivo] + competidores

# 3. TRADUCTOR INTEGRADO
def traducir_espanol(texto):
    if not texto or texto == "Sin descripción disponible.": return texto
    try:
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=es&dt=t&q=" + urllib.parse.quote(texto)
        r = requests.get(url, timeout=5).json()
        return "".join([frase[0] for frase in r[0] if frase[0]])
    except: return texto

# 4. CAPTURA DE DATOS E INTELIGENCIA DE LOGOS
def obtener_datos(symbol):
    try:
        t = yf.Ticker(symbol)
        inf = t.info
        if not inf: return None
        
        # Estrategia de Logo Robusta usando DuckDuckGo Icons como alternativa directa
        nombre_limpio = inf.get("longName", symbol).split(" ")[0].split(",")[0]
        logo_url = f"https://icons.duckduckgo.com/ip3/{symbol.lower()}.com.ico"
        if "website" in inf and inf["website"]:
            dom = inf["website"].replace("https://","").replace("http://","").split("/")[0]
            logo_url = f"https://icons.duckduckgo.com/ip3/{dom}.ico"
            
        tiene_ebitda = "ebitda" in inf or "enterpriseToEbitda" in inf or "forwardPE" in inf
        raw_desc = inf.get("longBusinessSummary", "Sin descripción disponible.")
        desc_es = traducir_espanol(raw_desc) if symbol == ticker_objetivo else ""
        
        common = {
            "Ticker": symbol, "Nombre": inf.get("longName", "N/A"),
            "Precio Actual": inf.get('currentPrice', inf.get('previousClose', 0)),
            "Logo": logo_url, "Descripcion": desc_es
        }
        
        if not tiene_ebitda:
            common.update({
                "Tipo": "ETF", "P/E Canasta": inf.get("trailingPE"), 
                "Expense Ratio": inf.get("feesExpensesInvestmentPercentage"),
                "Dividend Yield": inf.get("dividendYield"), "Beta": inf.get("beta")
            })
        else:
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

# 5. RENDERIZADO Y PROCESAMIENTO
if st.button("🔥 EJECUTAR DIAGNÓSTICO INTEGRAL"):
    with st.spinner("Conectando con el libro de órdenes corporativo..."):
        datos = [obtener_datos(t) for t in todos_tickers if obtener_datos(t)]
        df_verif = pd.DataFrame(datos) if datos else pd.DataFrame()
        
        if df_verif.empty or ticker_objetivo not in df_verif['Ticker'].values:
            st.error(f"🚨 **ERROR:** Datos no encontrados para '{ticker_objetivo}'.")
        else:
            df = pd.DataFrame(datos)
            obj = df[df['Ticker'] == ticker_objetivo].iloc[0]
            
            # BLOQUE DE CABECERA CON LOGO MEJORADO
            st.markdown(f"""
                <div class="header-inline">
                    <div class="brand-logo">
                        <img src="{obj['Logo']}" width="40" height="40" style="vertical-align:middle;" onerror="this.src='https://cdn-icons-png.flaticon.com/512/2967/2967304.png'">
                    </div>
                    <h1 style="margin:0; display:inline-block; vertical-align:middle;">{obj['Nombre']} ({obj['Ticker']})</h1>
                </div>
            """, unsafe_allow_html=True)

            # RENDERIZADO DE LAS PESTAÑAS (TABS STICKY ACTIVAS)
            tab1, tab2, tab3 = st.tabs(["📋 MÓDULO FUNDAMENTAL", "🧮 VALOR INTRÍNSECO (DCF)", "📐 ESTRATEGIA TÉCNICA (DMI)"])
            
            with tab1:
                st.subheader("ℹ️ Perfil de la Compañía y Descripción del Negocio")
                st.write(obj["Descripcion"])
                
                if obj["Tipo"] == "ACCION":
                    st.markdown("---")
                    st.subheader("🏆 Liderazgo Financiero en el Sector")
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
                    st.subheader("📋 Matriz de Múltiplos Comparativos")
                    v_min = ["Forward P/E", "EV/EBITDA", "P/B Ratio", "Deuda Neta/EBITDA"]
                    v_max = ["Liquidez Corriente", "Margen Neto", "ROE"]
                    st.dataframe(df_acc.set_index('Ticker')[v_min + v_max].format("{:.2f}"), width="stretch")
                else:
                    st.info("Activo estructurado como ETF de canasta.")

            with tab2:
                if obj["Tipo"] == "ACCION":
                    st.subheader(f"🧮 Modelo de Flujos Descontados (DCF) - {obj['Ticker']}")
                    fcf, sh, pr = obj["FCF_Total"], obj["Acciones"], obj["Precio Actual"]
                    if pd.notna(fcf) and fcf > 0:
                        fcf_a = fcf / sh
                        c1, c2, c3 = st.columns(3)
                        with c1: cw = st.slider("Crecimiento Esperado (Años 1-5):", 0, 40, 12, 1, "%d%%") / 100
                        with c2: td = st.slider("WACC (Tasa Descuento Exigida):", 5, 25, 10, 1, "%d%%") / 100
                        with c3: mt = st.slider("Múltiplo Terminal EV/EBITDA:", 3, 20, 6, 1, "%dx")
                        v_i = sum([fcf_a * ((1+cw)**i) / ((1+td)**i) for i in range(1, 6)]) + (fcf_a * ((1+cw)**5) * mt) / ((1+td)**5)
                        st.metric("Valor Intrínseco Teórico (Fair Value)", f"{v_i:.2f} USD", f"{((v_i-pr)/v_i)*100:.1f}% Margen de Seguridad")
                    else: st.warning("El modelo requiere flujos operativos libres (FCF) positivos para proyectar.")

            with tab3:
                st.subheader(f"📐 Suite de Indicadores Técnicos - {obj['Ticker']}")
                try:
                    h = yf.Ticker(obj["Ticker"]).history(period="1y")
                    if len(h) > 40:
                        c = h['Close']
                        ema = c.ewm(span=30, adjust=False).mean()
                        st.markdown("### 📈 Panel A: Ciclo de Tendencia (Precio vs. EMA 30)")
                        with st.expander("🔍 ¿Cómo leer este gráfico?"):
                            st.write("Si el precio diario (azul) quiebra y cotiza por sobre la EMA 30 (roja), el algoritmo valida una fase de acumulación alcista.")
                        st.line_chart(pd.DataFrame({"Precio Cierre": c, "EMA 30": ema}), height=300)
                        
                        if c.iloc[-1] > ema.iloc[-1]: st.success("🟩 ALGORITMO: ESTRATEGIA ALCISTA ACTIVA (LONG)")
                        else: st.error("🚨 ALGORITMO: ALERTA DE COMPRESIÓN BAJISTA (REDUCIR)")
                except: st.info("Historial técnico consolidándose.")

# 6. FOOTER PROFESIONAL
st.markdown("---")
st.markdown("<p style='text-align: center; color: #888; font-size: 11px;'>AVISO LEGAL: El contenido es educativo y no constituye recomendación implícita de compra o venta.</p>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #aaa; text-align: center;'>Desarrollado por <strong>Facundo Garcia Marquez</strong> | <a href='https://www.linkedin.com/in/facundo-garciamarquez/?locale=es' target='_blank' style='color:#0077B5; text-decoration:none;'>🔗 Conectemos en LinkedIn</a></p>", unsafe_allow_html=True)