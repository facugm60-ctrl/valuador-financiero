import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import urllib.parse
import requests

# 1. CONFIGURACIÓN DEL ENTORNO
st.set_page_config(page_title="Valuador Financiero Pro", layout="wide", initial_sidebar_state="expanded")

# Inyección de CSS para forzar textos más grandes y legibles en toda la terminal
st.markdown("""
    <style>
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    h1 {font-weight: 800; color: #FFFFFF; font-size: 28px !important;}
    h2 {font-weight: 700; color: #F0F2F6; font-size: 22px !important;}
    h3 {font-weight: 700; color: #F0F2F6; font-size: 18px !important;}
    p, li, span, label {font-size: 15px !important;}
    .stMetric label {font-size: 14px !important; font-weight: 600;}
    .stMetric div {font-size: 24px !important; font-weight: 700;}
    /* Botón Ejecutar estilizado */
    .stButton>button {
        width: 100%;
        background-color: #2ecc71;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        padding: 0.6rem;
        font-size: 16px !important;
        margin-top: 10px;
    }
    .stButton>button:hover {
        background-color: #27ae60;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Terminal de Valuación de Activos")
st.markdown("Plataforma profesional de analítica fundamental corporativa y timing de mercado.")

# 2. ENTRADAS DE CONTROL SUPERIOR
with st.container():
    col_in1, col_in2 = st.columns([1, 2])
    with col_in1:
        ticker_objetivo = st.text_input("📍 ACTIVO OBJETIVO (ej. VIST, SPY, TXAR.BA):", value="VIST").upper()
    with col_in2:
        comp_in = st.text_input("🔍 COMPETIDORES DEL SECTOR (separados por coma):", value="YPF, XOM, PAM")
        competidores = [c.strip().upper() for c in comp_in.split(",") if c.strip()]

todos_tickers = [ticker_objetivo] + competidores

# 3. FUNCIONES DE TRADUCCIÓN Y BACKEND
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
        
        logo_url = f"https://icons.duckduckgo.com/ip3/{symbol.lower()}.com.ico"
        if "website" in inf and inf["website"]:
            dom = inf["website"].replace("https://","").replace("http://","").split("/")[0]
            logo_url = f"https://icons.duckduckgo.com/ip3/{dom}.ico"
            
        tiene_ebitda = "ebitda" in inf or "enterpriseToEbitda" in inf or "forwardPE" in inf
        raw_desc = inf.get("longBusinessSummary", "Sin descripción disponible.")
        desc_es = traducir_espanol(raw_desc) if symbol == ticker_objetivo else ""
        
        common = {"Ticker": symbol, "Nombre": inf.get("longName", "N/A"), "Precio Actual": inf.get('currentPrice', inf.get('previousClose', 0)), "Logo": logo_url, "Descripcion": desc_es}
        
        if not tiene_ebitda:
            common.update({"Tipo": "ETF", "P/E Canasta": inf.get("trailingPE"), "Expense Ratio": inf.get("feesExpensesInvestmentPercentage"), "Dividend Yield": inf.get("dividendYield"), "Beta": inf.get("beta")})
        else:
            td, caj, eb = inf.get("totalDebt", 0), inf.get("totalCash", 0), inf.get("ebitda", 1)
            nd_eb = (td - caj) / eb if eb else None
            common.update({"Tipo": "ACCION", "Forward P/E": inf.get("forwardPE"), "EV/EBITDA": inf.get("enterpriseToEbitda"), "P/B Ratio": inf.get("priceToBook"), "Deuda Neta/EBITDA": nd_eb, "Liquidez Corriente": inf.get("currentRatio"), "Beta": inf.get("beta"), "Margen Neto": inf.get("profitMargins"), "ROE": inf.get("returnOnEquity"), "FCF_Total": inf.get("freeCashflow"), "Acciones": inf.get("sharesOutstanding"), "Div_Rate": inf.get("dividendRate", 0), "Div_Yield": inf.get("dividendYield", 0)})
        return common
    except: return None

# Inicializamos la memoria de sesión si no existe
if "analisis_listo" not in st.session_state:
    st.session_state.analisis_listo = False
    st.session_state.df_datos = None
    st.session_state.obj_data = None

if st.button("🔥 EJECUTAR DIAGNÓSTICO INTEGRAL"):
    with st.spinner("Sincronizando registros operativas y balances..."):
        datos = [obtener_datos(t) for t in todos_tickers if obtener_datos(t)]
        df_verif = pd.DataFrame(datos) if datos else pd.DataFrame()
        
        if df_verif.empty or ticker_objetivo not in df_verif['Ticker'].values:
            st.error(f"🚨 **ERROR:** No se pudieron recuperar registros estables para '{ticker_objetivo}'.")
            st.session_state.analisis_listo = False
        else:
            st.session_state.df_datos = pd.DataFrame(datos)
            st.session_state.obj_data = st.session_state.df_datos[st.session_state.df_datos['Ticker'] == ticker_objetivo].iloc[0]
            st.session_state.analisis_listo = True

# --- RENDERIZADO CONTROLADO POR ESTADO DE SESIÓN ---
if st.session_state.analisis_listo:
    df = st.session_state.df_datos
    obj = st.session_state.obj_data
    es_etf_target = obj["Tipo"] == "ETF"
    
    # Cabecera Visual con Logo
    st.markdown("---")
    c_head1, c_head2 = st.columns([1, 15])
    with c_head1: st.image(obj["Logo"], width=50)
    with c_head2: st.header(f"{obj['Nombre']} ({obj['Ticker']})")

    # UX PREMIUM: MENU CLAVADO EN LA SIDEBAR (NUNCA DESAPARECE NI RESETEA LA APP)
    with st.sidebar:
        st.markdown("## 🎛️ Centro de Navegación")
        seccion_activa = st.radio(
            "Seleccioná el módulo analítico:",
            ["📋 Módulo Fundamental", "💼 Cartera Simulada", "🧮 Calculadora DCF", "📐 Estrategia Técnica"]
        )

    # --- SECCIÓN 1: MODULO FUNDAMENTAL ---
    if seccion_activa == "📋 Módulo Fundamental":
        st.subheader("ℹ️ Perfil de la Compañía")
        st.write(obj["Descripcion"])
        
        if not es_etf_target:
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
            columnas_validas = [c for c in ["Ticker", "Nombre", "Precio Actual", "Forward P/E", "EV/EBITDA", "P/B Ratio", "Deuda Neta/EBITDA", "Liquidez Corriente", "Beta", "Margen Neto", "ROE"] if c in df_acc.columns]
            df_m = df_acc[columnas_validas].set_index('Ticker')
            st.dataframe(df_m.style.format({
                "Precio Actual": "{:.2f} USD", "Forward P/E": "{:.2f}", "P/B Ratio": "{:.2f}", 
                "EV/EBITDA": "{:.2f}", "Deuda Neta/EBITDA": "{:.2f}x", "Liquidez Corriente": "{:.2f}x", "Beta": "{:.2f}",
                "Margen Neto": lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A", "ROE": lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A"
            }, na_rep="N/A"), width="stretch")
            
            st.markdown("---")
            st.subheader("🤖 Informe del Asesor (Pros & Contras)")
            cp, cc = st.columns(2)
            with cp:
                st.markdown("**🟢 Fortalezas Operativas:**")
                st.write(f"• Margen Neto sólido en {obj.get('Margen Neto', 0)*100:.1f}%.\n• Captura óptima de contratos comerciales.\n• Liquidez corriente en {obj.get('Liquidez Corriente', 0):.2f}x.")
            with cc:
                st.markdown("**🔴 Riesgos y Coyuntura:**")
                st.write(f"• Apalancamiento en ratio de {obj.get('Deuda Neta/EBITDA', 0):.2f}x.\n• Presión por elevados planes de Capex que pueden estresar transitoriamente el flujo de caja libre antes de consolidar facturación.")
        else:
            st.subheader("📋 Matriz Estructural de Fondos (ETFs)")
            df_etf = df[df['Tipo'] == "ETF"].copy()
            columnas_etf = [c for c in ["Ticker", "Nombre", "Precio Actual", "P/E Canasta", "Expense Ratio", "Dividend Yield", "Beta"] if c in df_etf.columns]
            st.dataframe(df_etf[columnas_etf].set_index('Ticker').style.format({
                "Precio Actual": "{:.2f} USD", "P/E Canasta": "{:.2f}",
                "Expense Ratio": lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A",
                "Dividend Yield": lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A", "Beta": "{:.2f}"
            }, na_rep="N/A"), width="stretch")

    # --- SECCIÓN 2: CARTERA SIMULADA ---
    elif seccion_activa == "💼 Cartera Simulada":
        st.subheader(f"💼 Simulador de Portafolio - {ticker_objetivo}")
        c_port1, c_port2 = st.columns(2)
        with c_port1: cant_acciones = st.number_input("Cantidad de Acciones:", min_value=1, value=100)
        with c_port2: precio_compra = st.number_input("Precio de Compra Promedio (USD):", min_value=0.01, value=float(obj["Precio Actual"] * 0.9))
        
        costo_total = cant_acciones * precio_compra
        valor_actual = cant_acciones * obj["Precio Actual"]
        pnl_usd = valor_actual - costo_total
        pnl_pct = (pnl_usd / costo_total) * 100 if costo_total > 0 else 0
        
        m_c1, m_c2, m_c3 = st.columns(3)
        with m_c1: st.metric("Capital Invertido", f"{costo_total:.2f} USD")
        with m_c2: st.metric("Valor de Mercado", f"{valor_actual:.2f} USD")
        with m_c3: st.metric("P&L de la Posición", f"{pnl_usd:.2f} USD", f"{pnl_pct:.2f}%")
        
        st.markdown("---")
        st.markdown("#### 📅 Cronograma Proyectado de Renta Pasiva")
        d_rate = obj.get("Div_Rate", 0) if obj["Tipo"] == "ACCION" else obj.get("Dividend Yield", 0) * obj["Precio Actual"]
        if pd.notna(d_rate) and d_rate > 0:
            cobro_anual = cant_acciones * d_rate
            st.success(f"🎉 **Renta Estimada:** Percibirás un estimado de **{cobro_anual:.2f} USD anuales**.")
            df_cron = pd.DataFrame({"Período Estimado": ["Próximo Q1", "Siguiente Q2", "Siguiente Q3", "Siguiente Q4", "TOTAL ANUAL"], "Flujo Estimado": [cobro_anual/4, cobro_anual/4, cobro_anual/4, cobro_anual/4, cobro_anual]}).set_index("Período Estimado")
            st.table(df_cron.style.format("{:.2f} USD"))
        else: st.info(f"ℹ️ {ticker_objetivo} no registra pagos de dividendos activos.")

    # --- SECCIÓN 3: CALCULADORA DCF ---
    elif seccion_activa == "🧮 Calculadora DCF":
        if not es_etf_target:
            st.subheader(f"🧮 Proyección de Flujos Descontados (DCF) - {ticker_objetivo}")
            fcf, sh, pr = obj["FCF_Total"], obj["Acciones"], obj["Precio Actual"]
            if pd.notna(fcf) and fcf > 0 and sh > 0:
                fcf_a = fcf / sh
                cd1, cd2, cd3 = st.columns(3)
                with cd1: cw = st.slider("Crecimiento Anual (1-5):", 0, 40, 12, 1, "%d%%") / 100
                with cd2: td = st.slider("Tasa WACC:", 5, 25, 10, 1, "%d%%") / 100
                with cd3: mt = st.slider("Múltiplo Terminal:", 3, 20, 6, 1, "%dx")
                v_i = sum([fcf_a * ((1+cw)**i) / ((1+td)**i) for i in range(1, 6)]) + (fcf_a * ((1+cw)**5) * mt) / ((1+td)**5)
                
                cr1, cr2 = st.columns(2)
                with cr1: st.metric("VALOR INTRÍNSECO TEÓRICO", f"{v_i:.2f} USD")
                with cr2: st.metric("Precio de Mercado", f"{pr:.2f} USD", f"{((v_i-pr)/v_i)*100:.1f}% Margen")
            else: st.info("ℹ️ El modelo requiere flujos corporativos positivos (FCF) estables.")
        else: st.info("ℹ️ Los modelos DCF no aplican a ETFs.")

    # --- SECCIÓN 4: ESTRATEGIA TÉCNICA ---
    elif seccion_activa == "📐 Estrategia Técnica":
        st.subheader(f"📐 Análisis de Indicadores Técnicos - {ticker_objetivo}")
        try:
            h = yf.Ticker(ticker_objetivo).history(period="1y")
            if len(h) > 40:
                cierre = h['Close']
                calc_ema = cierre.ewm(span=30, adjust=False).mean()
                st.markdown("### 📈 Panel A: Ciclo de Tendencia (Precio vs. EMA 30)")
                with st.expander("🔍 ¿Cómo leer este gráfico?"):
                    st.write("Si el precio de cierre (azul) opera por encima de la EMA 30 (roja), la inercia es alcista.")
                st.line_chart(pd.DataFrame({"Precio Cierre": cierre, "EMA 30": calc_ema}), height=300)
                if cierre.iloc[-1] > calc_ema.iloc[-1]: st.success("🟩 **ALGORITMO: STRATEGY LONG ACTIVADA (ALCISTA)**")
                else: st.error("🚨 **ALGORITMO: REDUCIR EXPOSICIÓN (REDUCE/SHORT)**")
        except: st.info("Historial técnico consolidándose.")

# --- FOOTER ---
st.markdown("---")
st.markdown("<p style='text-align: center; color: #888888; font-size: 11px;'><strong>AVISO LEGAL:</strong> El contenido de esta plataforma es educativo y no constituye asesoramiento financiero.</p>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #aaaaaa; font-size: 14px;'>Desarrollado por <strong>Facundo Garcia Marquez</strong> | <a href='https://www.linkedin.com/in/facundo-garciamarquez/?locale=es' target='_blank' style='color: #0077B5; text-decoration: none;'>🔗 Conectemos en LinkedIn</a></p>", unsafe_allow_html=True)