import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import urllib.parse
import requests

# Configuración premium de la página
st.set_page_config(page_title="Valuador Financiero Pro", layout="wide", initial_sidebar_state="collapsed")

# Estilos CSS inyectados para forzar legibilidad y estética SaaS Dark
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
            nd_eb = (td - caj) / eb if eb else None
            common.update({"Tipo": "ACCION", "Forward P/E": inf.get("forwardPE"), "EV/EBITDA": inf.get("enterpriseToEbitda"), "P/B Ratio": inf.get("priceToBook"), "Deuda Neta/EBITDA": nd_eb, "Liquidez Corriente": inf.get("currentRatio"), "Beta": inf.get("beta"), "Margen Neto": inf.get("profitMargins"), "ROE": inf.get("returnOnEquity"), "FCF_Total": inf.get("freeCashflow"), "Acciones": inf.get("sharesOutstanding"), "Div_Rate": inf.get("dividendRate", 0), "Div_Yield": inf.get("dividendYield", 0)})
        return common
    except: return None

# Inicialización segura de Persistencia de Datos (Session State)
if "analisis_ejecutado" not in st.session_state:
    st.session_state.analisis_ejecutado = False
    st.session_state.df_datos = None
    st.session_state.obj_data = None

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

# --- DESPLIEGUE INTEGRADO MEDIANTE SOLAPAS ---
if st.session_state.analisis_ejecutado:
    df = st.session_state.df_datos
    obj = st.session_state.obj_data
    es_etf_target = obj["Tipo"] == "ETF"
    
    st.markdown("---")
    c_head1, c_head2 = st.columns([1, 15])
    with c_head1: st.image(obj["Logo"], width=50)
    with c_head2: st.header(f"{obj['Nombre']} ({obj['Ticker']})")

    # Arquitectura Integrada de Solapas nativas de Streamlit
    tab1, tab2, tab3, tab4 = st.tabs(["📋 MÓDULO FUNDAMENTAL", "💼 CARTERA SIMULADA INDEPENDIENTE", "🧮 VALOR INTRÍNSECO (DCF)", "📐 ESTRATEGIA TÉCNICA (DMI)"])

    # --- PESTAÑA 1: ANALISIS FUNDAMENTAL ---
    with tab1:
        st.subheader("ℹ️ Perfil de la Compañía y Descripción del Negocio")
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
                st.markdown("** Fortalezas Operativas:**")
                st.write(f"• Margen Neto sólido en {obj.get('Margen Neto', 0)*100:.1f}%.\n• Captura óptima de contratos comerciales sectoriales.\n• Liquidez corriente en {obj.get('Liquidez Corriente', 0):.2f}x.")
            with cc:
                st.markdown("** Riesgos y Coyuntura:**")
                st.write(f"• Apalancamiento en ratio de {obj.get('Deuda Neta/EBITDA', 0):.2f}x.\n• Elevados planes de Capex que pueden estresar transitoriamente el flujo de caja libre antes de consolidar facturación.")
        else:
            st.subheader("📋 Matriz Estructural de Fondos (ETFs)")
            df_etf = df[df['Tipo'] == "ETF"].copy()
            columnas_etf = [c for c in ["Ticker", "Nombre", "Precio Actual", "P/E Canasta", "Expense Ratio", "Dividend Yield", "Beta"] if c in df_etf.columns]
            st.dataframe(df_etf[columnas_etf].set_index('Ticker').style.format({"Precio Actual": "{:.2f} USD", "P/E Canasta": "{:.2f}", "Expense Ratio": lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A", "Dividend Yield": lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A", "Beta": "{:.2f}"}, na_rep="N/A"), width="stretch")

    # --- PESTAÑA 2: CARTERA SIMULADA INDEPENDIENTE ---
    with tab2:
        st.subheader("💼 Simulador Libre de Portafolio Estratégico")
        st.markdown("Armá la composición de tu cartera de forma independiente ingresando cualquier ticker.")
        
        c_p1, c_p2, c_p3 = st.columns(3)
        with c_p1: cart_ticker = st.text_input("Ingresá el Ticker para la Cartera:", value=obj["Ticker"]).upper()
        with c_p2: cart_cant = st.number_input("Cantidad de Acciones Poseídas:", min_value=1, value=100)
        with c_p3: cart_px = st.number_input("Precio de Compra Promedio (USD):", min_value=0.01, value=float(obj["Precio Actual"] * 0.9))
        
        try:
            t_cart = yf.Ticker(cart_ticker)
            inf_c = t_cart.info
            px_mercado = inf_c.get("currentPrice", inf_c.get("previousClose", 0))
            div_rate_c = inf_c.get("dividendRate", 0)
            div_yield_c = inf_c.get("dividendYield", 0)
            
            c_tot = cart_cant * cart_px
            v_act = cart_cant * px_mercado
            pnl_u = v_act - c_tot
            pnl_p = (pnl_u / c_tot) * 100 if c_tot > 0 else 0
            
            st.markdown(f"#### 📈 Rendimiento Actualizado de la Posición en {cart_ticker}")
            mc1, mc2, mc3 = st.columns(3)
            with mc1: st.metric("Capital Invertido", f"{c_tot:.2f} USD")
            with mc2: st.metric("Valor de Mercado", f"{v_act:.2f} USD")
            with mc3: st.metric("Ganancia / Pérdida (P&L)", f"{pnl_u:.2f} USD", f"{pnl_p:.2f}%")
            
            st.markdown("---")
            st.markdown("#### 📅 Cronograma Proyectado de Flujo por Dividendos")
            if pd.notna(div_rate_c) and div_rate_c > 0:
                c_anual = cart_cant * div_rate_c
                st.success(f"🎉 **Renta Estimada:** Percibirás un estimado de **{c_anual:.2f} USD anuales** en base al historial de pagos.")
                df_c = pd.DataFrame({"Trimestre": ["Próximo Q1", "Siguiente Q2", "Siguiente Q3", "Siguiente Q4", "TOTAL ACUMULADO"], "Monto Estimado": [c_anual/4, c_anual/4, c_anual/4, c_anual/4, c_anual]}).set_index("Trimestre")
                st.table(df_c.style.format("{:.2f} USD"))
            else:
                st.info(f"ℹ️ El activo {cart_ticker} no registra pagos de dividendos activos en Yahoo Finance.")
        except:
            st.error("No se pudieron recopilar datos para el activo de la cartera simulada.")

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

    # --- PESTAÑA 4: ESTRATEGIA TECNICA DEFINITIVA (RESTAURADA AL 100%) ---
    with tab4:
        st.subheader(f"📐 Terminal Técnica de Osciladores y Timing - {ticker_objetivo}")
        try:
            h_tecn = yf.Ticker(ticker_objetivo).history(period="1y")
            if len(h_tecn) > 40:
                cierre = h_tecn['Close']
                high = h_tecn['High']
                low = h_tecn['Low']
                precio_hoy = cierre.iloc[-1]
                
                # Cómputo matemático real de la EMA 30
                calc_ema_30 = cierre.ewm(span=30, adjust=False).mean()
                ema_30_hoy = calc_ema_30.iloc[-1]
                
                # Cómputo histórico completo de las curvas DMI y ADX 14
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
                
                # Métricas Técnicas destacadas
                m1, m2, m3 = st.columns(3)
                with m1: st.metric(label="Precio vs. EMA 30", value=f"{precio_hoy:.2f} USD", delta=f"{precio_hoy - ema_30_hoy:.2f} USD vs EMA 30")
                with m2: st.metric(label="Flujo Direccional (DMI)", value=f"+DI {p_di_hoy:.1f} | -DI {m_di_hoy:.1f}", delta=f"{p_di_hoy - m_di_hoy:.1f} Pts")
                with m3: st.metric(label="Fuerza de Tendencia (ADX)", value=f"{adx_hoy:.1f} Puntos", delta="Tendencia Activa" if adx_hoy > 20 else "Mercado Lateral", delta_color="normal" if adx_hoy > 20 else "off")
                
                # Panel A
                st.markdown("### 📈 Panel A: Tendencia de Mediano Plazo (Precio vs. EMA 30)")
                with st.expander("🔍 Ayuda Panel A:"):
                    st.write("Muestra el precio real cruzado con la Media Móvil Exponencial de 30 días. Precio por encima valida inercia alcista; por debajo, presión vendedora.")
                df_p = pd.DataFrame({"Precio Cierre (USD)": cierre, "EMA 30 Ruedas": calc_ema_30}, index=h_tecn.index)
                st.line_chart(df_p, height=300, use_container_width=True)
                
                # Panel B RESTAURADO
                st.markdown("### 📊 Panel B: Oscilador Direccional Completo (DMI 14 / ADX 14)")
                with st.expander("🔍 Ayuda Panel B:"):
                    st.write("• +DI (Azul): Fuerza Compradora. \n• -DI (Roja): Fuerza Vendedora. \n• ADX (Verde): Intensidad de la tendencia (>20/25 es fuerte).")
                df_d = pd.DataFrame({"+DI (Compradores)": series_plus_di, "-DI (Vendedores)": series_minus_di, "ADX (Fuerza General)": series_adx}, index=h_tecn.index)
                st.line_chart(df_d, height=220, use_container_width=True)
                
                # INTERPRETACIÓN AUTOMATIZADA RESTAURADA
                st.markdown("---")
                st.subheader("🎯 Diagnóstico Técnico y Recomendación Operativa")
                rec_col1, rec_col2 = st.columns(2)
                with rec_col1:
                    st.markdown("**🔍 Resumen del Algoritmo:**")
                    if precio_hoy > ema_30_hoy: st.write("• **Estructura:** Ciclo alcista activo operando por encima de la EMA 30.")
                    else: st.write("• **Estructura:** Ciclo correctivo operando por debajo de la EMA 30.")
                    if p_di_hoy > m_di_hoy: st.write("• **Flujo:** Control absoluto de los compradores (`+DI` > `-DI`). Presión de demanda.")
                    else: st.write("• **Flujo:** Control absoluto de los vendedores (`-DI` > `+DI`). Presión de oferta.")
                    if adx_hoy > 25: st.write(f"• **Fuerza:** El ADX en `{adx_hoy:.1f} pts` valida un movimiento institucional maduro y firme.")
                    else: st.write(f"• **Fuerza:** El ADX en `{adx_hoy:.1f} pts` delata compresión, fatiga o distribución lateral.")
                with rec_col2:
                    st.markdown("**🚀 Sugerencia y Timing:**")
                    if precio_hoy > ema_30_hoy and p_di_hoy > m_di_hoy and adx_hoy > 20: st.success("🟩 **ACCIONAR: LONG / COMPRA CONFIRMADA**\n\nTodos los indicadores están alineados a favor del movimiento. Estructura, flujo y fuerza respaldan la tendencia.")
                    elif precio_hoy < ema_30_hoy and m_di_hoy > p_di_hoy and adx_hoy > 20: st.error("🚨 **ACCIONAR: REDUCIR EXPOSICIÓN / EVITAR**\n\nTendencia bajista consolidada con fuerza institucional. Evitar compras hasta recuperar la media.")
                    elif adx_hoy < 20: st.warning("🟨 **ACCIONAR: PACIENCIA / MERCADO LATERAL**\n\nTendencia ausente. El precio oscilará de forma errática en rangos. Esperar quiebre limpio con volumen.")
                    else: st.info("🟦 **ACCIONAR: MONITOREO / TRANSICIÓN**\n\nLecturas mixtas en osciladores. Zona de rango o balanceo de carteras antes de definir dirección.")
            else: st.info("Historial insuficiente.")
        except: st.info("Módulo técnico consolidándose.")

# --- FOOTER ---
st.markdown("---")
st.markdown("<p style='text-align: center; color: #888888; font-size: 11px;'><strong>AVISO LEGAL:</strong> El contenido de esta plataforma es educativo y no constituye asesoramiento financiero.</p>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #aaaaaa; font-size: 14px;'>Desarrollado por <strong>Facundo Garcia Marquez</strong> | <a href='https://www.linkedin.com/in/facundo-garciamarquez/?locale=es' target='_blank' style='color: #0077B5; text-decoration: none;'>🔗 Conectemos en LinkedIn</a></p>", unsafe_allow_html=True)