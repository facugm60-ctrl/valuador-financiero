import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import urllib.parse
import requests

# Configuración premium de la página
st.set_page_config(page_title="Valuador Financiero Pro", layout="wide", initial_sidebar_state="collapsed")

# Estilos CSS inyectados para maximizar la legibilidad SaaS Dark
st.markdown("""
    <style>
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    h1 {font-weight: 800; color: #FFFFFF; font-size: 28px !important;}
    h2 {font-weight: 700; color: #F0F2F6; font-size: 22px !important;}
    h3 {font-weight: 700; color: #F0F2F6; font-size: 18px !important;}
    p, li, span, label {font-size: 15px !important;}
    .stMetric label {font-size: 14px !important; font-weight: 600;}
    .stMetric div {font-size: 24px !important; font-weight: 700;}
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
    .stButton>button:hover { background-color: #27ae60; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Terminal de Valuación de Activos")
st.markdown("Plataforma profesional de analítica fundamental corporativa y timing de mercado.")

# INICIALIZACIÓN CRUCIAL AL PRINCIPIO: Evita el AttributeError en todas las solapas
if "cartera_df" not in st.session_state:
    st.session_state.cartera_df = pd.DataFrame([
        {"Ticker": "VIST", "Nominales": 100, "Precio Compra (USD)": 50.0},
        {"Ticker": "WMT", "Nominales": 50, "Precio Compra (USD)": 75.0},
        {"Ticker": "KO", "Nominales": 80, "Precio Compra (USD)": 60.0},
        {"Ticker": "SPY", "Nominales": 10, "Precio Compra (USD)": 500.0}
    ])

if "analisis_ejecutado" not in st.session_state:
    st.session_state.analisis_ejecutado = False
    st.session_state.df_datos = None
    st.session_state.obj_data = None

# Bloque de Entradas de Usuario
with st.container():
    col_in1, col_in2 = st.columns([1, 2])
    with col_in1:
        ticker_objetivo = st.text_input("📍 ACTIVO OBJETIVO (ej. VIST, SPY, TXAR.BA):", value="VIST").upper()
    with col_in2:
        comp_in = st.text_input("🔍 COMPETIDORES DEL SECTOR (separados por coma):", value="YPF, XOM, PAM")
        competidores = [c.strip().upper() for c in comp_in.split(",") if c.strip()]

todos_tickers = [ticker_objetivo] + competidores

# Funciones de Backend operativas
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
            nd_eb = (td - caj) / eb if eb else 0
            common.update({"Tipo": "ACCION", "Forward P/E": inf.get("forwardPE"), "EV/EBITDA": inf.get("enterpriseToEbitda"), "P/B Ratio": inf.get("priceToBook"), "Deuda Neta/EBITDA": nd_eb, "Liquidez Corriente": inf.get("currentRatio"), "Beta": inf.get("beta"), "Margen Neto": inf.get("profitMargins"), "ROE": inf.get("returnOnEquity"), "FCF_Total": inf.get("freeCashflow"), "Acciones": inf.get("sharesOutstanding"), "Div_Rate": inf.get("dividendRate", 0), "Div_Yield": inf.get("dividendYield", 0)})
        return common
    except: return None

if st.button("🔥 EJECUTAR DIAGNÓSTICO INTEGRAL"):
    with st.spinner("Descargando balances y cargando algoritmos técnicos..."):
        datos = [obtener_datos(t) for t in todos_tickers if obtener_datos(t)]
        df_verif = pd.DataFrame(datos) if datos else pd.DataFrame()
        if df_verif.empty or ticker_objetivo not in df_verif['Ticker'].values:
            st.error(f"🚨 **ERROR:** No se encontraron registros estables para '{ticker_objetivo}'.")
            st.session_state.analisis_ejecutado = False
        else:
            st.session_state.df_datos = pd.DataFrame(datos)
            st.session_state.obj_data = st.session_state.df_datos[st.session_state.df_datos['Ticker'] == ticker_objetivo].iloc[0]
            st.session_state.analisis_ejecutado = True

# --- DESPLIEGUE MEDIANTE SOLAPAS ---
if st.session_state.analisis_ejecutado:
    df = st.session_state.df_datos
    obj = st.session_state.obj_data
    es_etf_target = obj["Tipo"] == "ETF"
    
    st.markdown("---")
    c_head1, c_head2 = st.columns([1, 15])
    with c_head1: st.image(obj["Logo"], width=50)
    with c_head2: st.header(f"{obj['Nombre']} ({obj['Ticker']})")

    # SOLAPAS CON NOMBRE CORREGIDO
    tab1, tab2, tab3, tab4 = st.tabs(["📋 ANÁLISIS FUNDAMENTAL", "💼 CARTERA MULTIACTIVO", "🧮 VALOR INTRÍNSECO (DCF)", "📐 ANÁLISIS TÉCNICO"])

    # --- PESTAÑA 1: ANALISIS FUNDAMENTAL ---
    with tab1:
        st.subheader("ℹ️ Operaciones de la Empresa e Inversiones")
        st.write(obj["Descripcion"])
        
        if not es_etf_target:
            st.markdown("---")
            st.subheader("📋 Matriz de Múltiplos Comparativos (Ganadores Resaltados)")
            df_acc = df[df['Tipo'] == "ACCION"].copy()
            columnas_validas = [c for c in ["Ticker", "Forward P/E", "EV/EBITDA", "P/B Ratio", "Deuda Neta/EBITDA", "Liquidez Corriente", "Margen Neto", "ROE"] if c in df_acc.columns]
            df_m = df_acc[columnas_validas].set_index('Ticker')
            
            df_styled = df_m.style.format({
                "Forward P/E": "{:.2f}", "EV/EBITDA": "{:.2f}", "P/B Ratio": "{:.2f}",
                "Deuda Neta/EBITDA": "{:.2f}x", "Liquidez Corriente": "{:.2f}x",
                "Margen Neto": lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A", "ROE": lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A"
            }, na_rep="N/A")
            
            df_styled = df_styled.highlight_min(subset=["Forward P/E", "EV/EBITDA", "P/B Ratio", "Deuda Neta/EBITDA"], color="#1b4d22")
            df_styled = df_styled.highlight_max(subset=["Liquidez Corriente", "Margen Neto", "ROE"], color="#1b4d22")
            st.dataframe(df_styled, width="stretch")
            
            st.markdown("**🔍 Interpretación del Arbitraje de Múltiplos:**")
            try:
                p_min_tick = df_m["Forward P/E"].idxmin()
                roe_max_tick = df_m["ROE"].idxmax()
                st.write(f"• El mercado convalida el mayor descuento relativo en el ticker **{p_min_tick}**, registrando el menor ratio Precio/Ganancias del sector. Por otra parte, la mayor tracción operativa y retorno sobre el capital invertido está liderado por **{roe_max_tick}** con un ROE destacado.")
            except: st.write("• Datos sectoriales listos para análisis comparativo de valor.")

            st.markdown("---")
            st.subheader("🤖 Informe del Asesor Financiero (Análisis de Riesgo y Deuda)")
            cp, cc = st.columns(2)
            with cp:
                st.markdown("**🟢 Perfil de Inversión y Solvencia:**")
                st.write(f"• **Modelo de Negocio:** La compañía inyecta capital intensivo en infraestructura operativa estratégica para sostener contratos corporativos de largo plazo.")
                deuda_ratio = obj.get('Deuda Neta/EBITDA', 0)
                st.write(f"• **Estructura de Deuda:** El apalancamiento de `{deuda_ratio:.2f}x Deuda Neta/EBITDA` refleja el nivel de pasivos tomados frente a su generación operativa real.")
            with cc:
                st.markdown("**🔴 Diagnóstico de Estrés Financiero:**")
                liq_ratio = obj.get('Liquidez Corriente', 0)
                if liq_ratio < 1.0:
                    st.error(f"⚠️ **ALERTA DE ESTRÉS:** La empresa registra una liquidez corriente de `{liq_ratio:.2f}x` (menor a 1.0). Sus activos líquidos no cubren las obligaciones inmediatas.")
                else:
                    st.success(f"✅ **COBERTURA DE CAJA:** Ratio de liquidez corriente en `{liq_ratio:.2f}x`. Dispone de suficiente espalda líquida para cubrir sus pasivos de corto plazo sin ahogos.")
        else:
            st.subheader("📋 Matriz Estructural de Fondos (ETFs)")
            df_etf = df[df['Tipo'] == "ETF"].copy()
            columnas_etf = [c for c in ["Ticker", "Nombre", "Precio Actual", "P/E Canasta", "Expense Ratio", "Dividend Yield", "Beta"] if c in df_etf.columns]
            st.dataframe(df_etf[columnas_etf].set_index('Ticker').style.format({"Precio Actual": "{:.2f} USD", "P/E Canasta": "{:.2f}", "Expense Ratio": lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A", "Dividend Yield": lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A", "Beta": "{:.2f}"}, na_rep="N/A"), width="stretch")

    # --- PESTAÑA 2: CARTERA MULTIACTIVO TOTALMENTE INDEPENDIENTE (FIXED) ---
    with tab2:
        st.subheader("💼 Consolidación de Cartera Multiactivo Dinámica")
        st.markdown("Agregá, modificá o eliminá los activos de tu portafolio en la grilla interactiva. Hacé doble clic en las celdas para cambiar valores.")
        
        editar_cartera = st.data_editor(
            st.session_state.cartera_df, 
            num_rows="dynamic", 
            key="grilla_cartera_premium",
            use_container_width=True
        )
        st.session_state.cartera_df = editar_cartera

        costo_total_port = 0.0
        valor_actual_port = 0.0
        dividendos_anuales_totales = 0.0
        registros_procesados = []
        
        for index, row in editar_cartera.iterrows():
            tick = str(row["Ticker"]).strip().upper() if pd.notna(row["Ticker"]) else ""
            nominales = float(row["Nominales"]) if pd.notna(row["Nominales"]) else 0
            px_compra = float(row["Precio Compra (USD)"]) if pd.notna(row["Precio Compra (USD)"]) else 0
            
            if tick and nominales > 0:
                try:
                    t_yf = yf.Ticker(tick)
                    t_inf = t_yf.info
                    px_ahora = t_inf.get("currentPrice", t_inf.get("previousClose", px_compra))
                    div_rate = t_inf.get("dividendRate", 0) or (t_inf.get("dividendYield", 0) * px_ahora)
                    
                    c_total = nominales * px_compra
                    v_actual = nominales * px_ahora
                    pnl_u = v_actual - c_total
                    
                    costo_total_port += c_total
                    valor_actual_port += v_actual
                    if pd.notna(div_rate):
                        dividendos_anuales_totales += (nominales * div_rate)
                        
                    registros_procesados.append({
                        "Ticker": tick, "Nominales": nominales, "Precio Medio": px_compra,
                        "Precio Mercado": px_ahora, "Costo Total": c_total, "Valor Mercado": v_actual, "P&L USD": pnl_u
                    })
                except:
                    c_total = nominales * px_compra
                    registros_procesados.append({
                        "Ticker": tick, "Nominales": nominales, "Precio Medio": px_compra,
                        "Precio Mercado": 0.0, "Costo Total": c_total, "Valor Mercado": 0.0, "P&L USD": 0.0
                    })

        if registros_procesados:
            df_resumen_port = pd.DataFrame(registros_procesados).set_index("Ticker")
            st.markdown("#### 📈 Consolidado del Portafolio de Inversión")
            
            pnl_total_usd = valor_actual_port - costo_total_port
            pnl_total_pct = (pnl_total_usd / costo_total_port) * 100 if costo_total_port > 0 else 0
            
            mc1, mc2, mc3 = st.columns(3)
            with mc1: st.metric("Capital Total Invertido", f"{costo_total_port:.2f} USD")
            with mc2: st.metric("Valor de Mercado Actual", f"{valor_actual_port:.2f} USD")
            with mc3: st.metric("P&L Total de Cartera", f"{pnl_total_usd:.2f} USD", f"{pnl_total_pct:.2f}%")
            
            st.dataframe(df_resumen_port.style.format({
                "Precio Medio": "{:.2f} USD", "Precio Mercado": "{:.2f} USD",
                "Costo Total": "{:.2f} USD", "Valor Mercado": "{:.2f} USD", "P&L USD": "{:.2f} USD"
            }), width="stretch")
            
            st.markdown("---")
            st.markdown("#### 📅 Cronograma Unificado de Renta Pasiva (Flujo de Fondos)")
            if dividendos_anuales_totales > 0:
                st.success(f"🎉 **Caja de Cobros:** Tu cartera consolidada proyecta una renta pasiva de **{dividendos_anuales_totales:.2f} USD anuales**.")
                df_cron = pd.DataFrame({
                    "Período de Distribución": ["Flujo Estimado Q1", "Flujo Estimado Q2", "Flujo Estimado Q3", "Flujo Estimado Q4", "CAJA TOTAL ANUAL PROYECTADA"],
                    "Monto Flujo Cobro": [dividendos_anuales_totales/4, dividendos_anuales_totales/4, dividendos_anuales_totales/4, dividendos_anuales_totales/4, dividendos_anuales_totales]
                }).set_index("Período de Distribución")
                st.table(df_cron.style.format("{:.2f} USD"))
            else:
                st.info("ℹ️ Los activos cargados actualmente no registran dividendos en la base de datos.")

    # --- PESTAÑA 3: CALCULADORA DCF ---
    with tab3:
        if not es_etf_target:
            st.subheader(f"🧮 Modelo de Flujos de Caja Descontados (DCF) - {ticker_objetivo}")
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
            else: st.info("ℹ️ El modelo DCF requiere flujos corporativos positivos (FCF) estables para proyectar.")
        else: st.info("ℹ️ Los modelos DCF no aplican a ETFs.")

    # --- PESTAÑA 4: ANALISIS TECNICO DEFINITIVO (RESTAURADO COMPLETO CON PANELES A Y B) ---
    with tab4:
        st.subheader(f"📐 Terminal Técnica de Osciladores y Timing - {ticker_objetivo}")
        try:
            h_tecn = yf.Ticker(ticker_objetivo).history(period="1y")
            if len(h_tecn) > 40:
                cierre = h_tecn['Close']
                high = h_tecn['High']
                low = h_tecn['Low']
                precio_hoy = cierre.iloc[-1]
                calc_ema_30 = cierre.ewm(span=30, adjust=False).mean()
                ema_30_hoy = calc_ema_30.iloc[-1]
                
                up_move = high.diff()
                down_move = -low.diff()
                plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
                minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
                tr1 = high - low
                tr2 = np.abs(high - cierre.shift(1))
                tr3 = np.abs(low - cierre.shift(1))
                tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                tr_14 = tr.ewm(alpha=1/14, adjust=False).mean()
                plus_dm_14 = pd.Series(plus_dm, index=h_tecn.index).ewm(alpha=1/14, adjust=False).mean()
                minus_dm_14 = pd.Series(minus_dm, index=h_tecn.index).ewm(alpha=1/14, adjust=False).mean()
                
                series_plus_di = (plus_dm_14 / tr_14) * 100
                series_minus_di = (minus_dm_14 / tr_14) * 100
                dx = (np.abs(series_plus_di - series_minus_di) / (series_plus_di + series_minus_di)) * 100
                series_adx = dx.ewm(alpha=1/14, adjust=False).mean()
                
                p_di_hoy = series_plus_di.iloc[-1]
                m_di_hoy = series_minus_di.iloc[-1]
                adx_hoy = series_adx.iloc[-1]
                
                m1, m2, m3 = st.columns(3)
                with m1: st.metric(label="Precio vs. EMA 30", value=f"{precio_hoy:.2f} USD", delta=f"{precio_hoy - ema_30_hoy:.2f} USD vs EMA 30")
                with m2: st.metric(label="Flujo Direccional (DMI)", value=f"+DI {p_di_hoy:.1f} | -DI {m_di_hoy:.1f}", delta=f"{p_di_hoy - m_di_hoy:.1f} Pts")
                with m3: st.metric(label="Fuerza de Tendencia (ADX)", value=f"{adx_hoy:.1f} Puntos", delta="Tendencia Activa" if adx_hoy > 20 else "Mercado Lateral", delta_color="normal" if adx_hoy > 20 else "off")
                
                st.markdown("### 📈 Panel A: Tendencia de Mediano Plazo (Precio vs. EMA 30)")
                df_p = pd.DataFrame({"Precio Cierre (USD)": cierre, "EMA 30 Ruedas": calc_ema_30}, index=h_tecn.index)
                st.line_chart(df_p, height=300, use_container_width=True)
                
                st.markdown("### 📊 Panel B: Oscilador Direccional Completo (DMI 14 / ADX 14)")
                df_d = pd.DataFrame({"+DI (Compradores)": series_plus_di, "-DI (Vendedores)": series_minus_di, "ADX (Fuerza General)": series_adx}, index=h_tecn.index)
                st.line_chart(df_d, height=220, use_container_width=True)
                
                st.markdown("---")
                st.subheader("🎯 Diagnóstico Técnico y Recomendación Operativa")
                rec_col1, rec_col2 = st.columns(2)
                with rec_col1:
                    st.markdown("**🔍 Resumen del Algoritmo:**")
                    if precio_hoy > ema_30_hoy: st.write("• **Estructura:** Ciclo alcista activo operando por encima de la EMA 30.")
                    else: st.write("• **Estructura:** Ciclo correctivo operando por debajo de la EMA 30.")
                    if p_di_hoy > m_di_hoy: st.write("• **Flujo:** Control absoluto de los compradores (`+DI` > `-DI`). Presión de demanda.")
                    else: st.write("• **Flujo:** Control absoluto de los vendedores (`-DI` > `+DI`). Presión de oferta.")
                    if adx_hoy > 25: st.write(f"• **Fuerza:** El ADX en `{adx_hoy:.1f} pts` valida un movimiento institucional maduro.")
                    else: st.write(f"• **Fuerza:** El ADX en `{adx_hoy:.1f} pts` delata compresión o distribución lateral.")
                with rec_col2:
                    st.markdown("**🚀 Sugerencia y Timing:**")
                    if precio_hoy > ema_30_hoy and p_di_hoy > m_di_hoy and adx_hoy > 20: st.success("🟩 **ACCIONAR: LONG / COMPRA CONFIRMADA**\n\nTodos los indicadores están alineados a favor del movimiento.")
                    elif precio_hoy < ema_30_hoy and m_di_hoy > p_di_hoy and adx_hoy > 20: st.error("🚨 **ACCIONAR: REDUCIR EXPOSICIÓN / EVITAR**\n\nTendencia bajista de corto/mediano plazo.")
                    elif adx_hoy < 20: st.warning("🟨 **ACCIONAR: PACIENCIA / MERCADO LATERAL**\n\nTendencia ausente. El precio oscilará de forma errática en rangos.")
                    else: st.info("🟦 **ACCIONAR: MONITOREO / TRANSICIÓN**\n\nLecturas mixtas en osciladores. Zona de rango o balanceo de carteras.")
            else: st.info("Historial insuficiente.")
        except: st.info("Módulo técnico consolidándose.")

# --- FOOTER ---
st.markdown("---")
st.markdown("<p style='text-align: center; color: #888888; font-size: 11px;'><strong>AVISO LEGAL:</strong> El contenido de esta plataforma es educativo y no constituye asesoramiento financiero.</p>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #aaaaaa; font-size: 14px;'>Desarrollado por <strong>Facundo Garcia Marquez</strong> | <a href='https://www.linkedin.com/in/facundo-garciamarquez/?locale=es' target='_blank' style='color: #0077B5; text-decoration: none;'>🔗 Conectemos en LinkedIn</a></p>", unsafe_allow_html=True)