import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

# Configuramos la página en modo ancho y un título pro
st.set_page_config(page_title="Valuador Financiero Pro", layout="wide", initial_sidebar_state="collapsed")

# Estilo CSS inyectado para mejorar fuentes, botones y look & feel general
st.markdown("""
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    h1 {font-weight: 800; color: #FFFFFF;}
    h3 {font-weight: 700; color: #F0F2F6; margin-top: 1rem;}
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
    </style>
""", unsafe_allow_html=True)

st.title("📊 Terminal de Valuación de Activos")
st.markdown("Plataforma profesional de analítica fundamental corporativa, screening de ETFs y timing de mercado.")

# Bloque de Entradas Lateral/Superior estilizado
with st.container():
    col1, col2 = st.columns([1, 2])
    with col1:
        ticker_objetivo = st.text_input("📍 ACTIVO OBJETIVO (ej. VIST, SPY, TXAR.BA):", value="VIST").upper()
    with col2:
        comp_in = st.text_input("🔍 COMPETIDORES DEL SECTOR (separados por coma):", value="YPF, XOM, PAM")
        competidores = [c.strip().upper() for c in comp_in.split(",") if c.strip()]

todos_tickers = [ticker_objetivo] + competidores

def obtener_datos(symbol):
    try:
        t = yf.Ticker(symbol)
        inf = t.info
        if not inf: return None
        tiene_ebitda = "ebitda" in inf or "enterpriseToEbitda" in inf or "forwardPE" in inf
        es_etf = not tiene_ebitda
        
        if es_etf:
            return {
                "Ticker": symbol, "Nombre": inf.get("longName", "N/A"),
                "Tipo": "ETF", "Precio Actual": inf.get('currentPrice', inf.get('previousClose', 0)),
                "P/E Canasta": inf.get("trailingPE"), "Expense Ratio": inf.get("feesExpensesInvestmentPercentage"),
                "Dividend Yield": inf.get("dividendYield"), "Beta": inf.get("beta")
            }
        else:
            td = inf.get("totalDebt", 0)
            caj = inf.get("totalCash", 0)
            eb = inf.get("ebitda", 1)
            nd_eb = (td - caj) / eb if eb else None
            return {
                "Ticker": symbol, "Nombre": inf.get("longName", "N/A"),
                "Tipo": "ACCION", "Precio Actual": inf.get('currentPrice', inf.get('previousClose', 0)),
                "Forward P/E": inf.get("forwardPE"), "EV/EBITDA": inf.get("enterpriseToEbitda"),
                "P/B Ratio": inf.get("priceToBook"), "Deuda Neta/EBITDA": nd_eb,
                "Liquidez Corriente": inf.get("currentRatio"), "Beta": inf.get("beta"),
                "Margen Neto": inf.get("profitMargins"), "ROE": inf.get("returnOnEquity"),
                "FCF_Total": inf.get("freeCashflow"), "Acciones": inf.get("sharesOutstanding")
            }
    except: return None

if st.button("🔥 EJECUTAR DIAGNÓSTICO INTEGRAL"):
    with st.spinner("Procesando algoritmos y descargando datos de Wall Street..."):
        datos = [obtener_datos(t) for t in todos_tickers if obtener_datos(t)]
        
        df_verif = pd.DataFrame(datos) if datos else pd.DataFrame()
        if df_verif.empty or ticker_objetivo not in df_verif['Ticker'].values:
            st.error(f"🚨 **ERROR:** No se encontraron registros para '{ticker_objetivo}'. Intentá agregando el sufijo correspondiente (ej. '.BA' para activos locales).")
        else:
            df = pd.DataFrame(datos)
            obj = df[df['Ticker'] == ticker_objetivo].iloc[0]
            es_etf_target = obj["Tipo"] == "ETF"
            
            # --- ARQUITECTURA POR PESTAÑAS (TABS) ---
            tab1, tab2, tab3 = st.tabs(["📋 MÓDULO FUNDAMENTAL", "🧮 VALOR INTRÍNSECO (DCF)", "📐 ESTRATEGIA TÉCNICA (DMI)"])
            
            # --- PESTAÑA 1: ANÁLISIS FUNDAMENTAL ---
            with tab1:
                if not es_etf_target:
                    st.subheader("🏆 Liderazgo Financiero en el Sector")
                    df_acc = df[df['Tipo'] == "ACCION"].copy()
                    
                    # Computamos los ganadores del sector
                    try:
                        df_pe_val = df_acc[df_acc['Forward P/E'] > 0]
                        ticker_descuento = df_pe_val.loc[df_pe_val['Forward P/E'].idxmin()]['Ticker'] if not df_pe_val.empty else "N/A"
                        val_descuento = df_pe_val['Forward P/E'].min() if not df_pe_val.empty else 0
                        
                        df_roe_val = df_acc[df_acc['ROE'].notna()]
                        ticker_eficiencia = df_roe_val.loc[df_roe_val['ROE'].idxmax()]['Ticker'] if not df_roe_val.empty else "N/A"
                        val_eficiencia = df_roe_val['ROE'].max() * 100 if not df_roe_val.empty else 0
                        
                        df_deb_val = df_acc[df_acc['Deuda Neta/EBITDA'].notna()]
                        ticker_solvencia = df_deb_val.loc[df_deb_val['Deuda Neta/EBITDA'].idxmin()]['Ticker'] if not df_deb_val.empty else "N/A"
                        val_solvencia = df_deb_val['Deuda Neta/EBITDA'].min() if not df_deb_val.empty else 0
                    except:
                        ticker_descuento, val_descuento = "N/A", 0
                        ticker_eficiencia, val_eficiencia = "N/A", 0
                        ticker_solvencia, val_solvencia = "N/A", 0

                    c_kpi1, c_kpi2, c_kpi3 = st.columns(3)
                    with c_kpi1:
                        st.metric(label="🏷️ Mayor Descuento (Menor Forward P/E)", value=ticker_descuento, delta=f"{val_descuento:.2f}x P/E", delta_color="inverse")
                    with c_kpi2:
                        st.metric(label="📈 Mayor Eficiencia Operativa (ROE)", value=ticker_eficiencia, delta=f"{val_eficiencia:.2f}% ROE")
                    with c_kpi3:
                        st.metric(label="🛡️ Balance Más Sólido (Menor Deuda Neta/EBITDA)", value=ticker_solvencia, delta=f"{val_solvencia:.2f}x Ratio", delta_color="inverse")
                    
                    st.markdown("---")
                    
                    st.subheader("📋 Matriz de Múltiplos y Estructura de Capital")
                    columnas_validas = [c for c in ["Ticker", "Nombre", "Precio Actual", "Forward P/E", "EV/EBITDA", "P/B Ratio", "Deuda Neta/EBITDA", "Liquidez Corriente", "Beta", "Margen Neto", "ROE"] if c in df_acc.columns]
                    df_m = df_acc[columnas_validas]
                    
                    v_min = [c for c in ["Forward P/E", "EV/EBITDA", "P/B Ratio", "Deuda Neta/EBITDA"] if c in df_m.columns]
                    v_max = [c for c in ["Liquidez Corriente", "Margen Neto", "ROE"] if c in df_m.columns]
                    
                    st.dataframe(df_m.style.apply(
                        lambda s: ['background-color: rgba(46,204,113,0.3); font-weight:bold' if v == s[s>0].min() else '' for v in s], subset=v_min
                    ).apply(
                        lambda s: ['background-color: rgba(46,204,113,0.3); font-weight:bold' if v == s.max() else '' for v in s], subset=v_max
                    ).format({
                        "Precio Actual": "{:.2f} USD", "Forward P/E": "{:.2f}", "P/B Ratio": "{:.2f}", 
                        "EV/EBITDA": "{:.2f}", "Deuda Neta/EBITDA": "{:.2f}x", "Liquidez Corriente": "{:.2f}x", "Beta": "{:.2f}",
                        "Margen Neto": lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A", "ROE": lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A"
                    }, na_rep="N/A"), width="stretch")
                    
                    df_s = df[(df['Ticker'] != ticker_objetivo) & (df['Tipo'] == "ACCION")]
                    meds = df_s.median(numeric_only=True) if not df_s.empty else None
                    
                    st.markdown("---")
                    st.subheader("🎯 Mapa Matriz: Relación Valoración vs. Rentabilidad (Forward P/E vs. ROE)")
                    st.caption("💡 Tip del Analista: Las mejores oportunidades se ubican arriba a la izquierda (bajo múltiplo P/E y alto retorno sobre el capital ROE).")
                    
                    try:
                        df_scatter = df_acc[df_acc['Forward P/E'].notna() & df_acc['ROE'].notna()].copy()
                        if not df_scatter.empty:
                            df_scatter['ROE (%)'] = df_scatter['ROE'] * 100
                            df_scatter = df_scatter.set_index('Ticker')
                            st.scatter_chart(df_scatter, x='Forward P/E', y='ROE (%)', use_container_width=True)
                    except:
                        st.info("No hay suficientes datos cruzados para trazar el mapa de dispersión.")
                    
                    st.markdown("---")
                    st.markdown("### 🤖 Informe del Asesor Inteligente de Inversión")
                    c_inf1, c_inf2 = st.columns(2)
                    with c_inf1:
                        st.markdown("**🛡️ Auditoría de Riesgo de Balance:**")
                        txt = ""
                        db = obj["Deuda Neta/EBITDA"]
                        if pd.notna(db):
                            if db > 3: txt += f"• ⚠️ **Deuda Elevada:** Ratio en `{db:.2f}x`. Monitorear apalancamiento.\n"
                            elif db < 0: txt += f"• 🛡️ **Caja Neta Positiva:** Solvencia excelente (`{db:.2f}x`). Más efectivo que pasivos.\n"
                            else: txt += f"• 👍 **Deuda Controlada:** Parámetros saludables (`{db:.2f}x`).\n"
                        lq = obj["Liquidez Corriente"]
                        if pd.notna(lq):
                            if lq < 1: txt += f"• 🚨 **Estrés de Liquidez:** Corto plazo ajustado (`{lq:.2f}x`).\n"
                            else: txt += f"• 👍 **Liquidez Solvente:** Cubre deudas de corto plazo con `{lq:.2f}x`.\n"
                        st.write(txt)
                    with c_inf2:
                        st.markdown("**🎯 Dictamen de Valuación Relativa:**")
                        pe_o = obj["Forward P/E"]
                        pe_m = meds["Forward P/E"] if meds is not None else None
                        if pd.notna(db) and db > 3: st.error("🚨 **EVITAR:** Riesgo de balance crítico. Excluido por apalancamiento.")
                        elif pd.notna(pe_o) and pd.notna(pe_m) and pe_o < pe_m: st.success("🟩 **COMPRAR:** Múltiplos rezagados con descuento frente a la mediana.")
                        else: st.info("🟪 **MANTENER:** Cotización en rangos de equilibrio razonables.")
                else:
                    st.subheader("📋 Matriz de Eficiencia y Costos estructurales (ETFs)")
                    df_etf = df[df['Tipo'] == "ETF"].copy()
                    columnas_etf = [c for c in ["Ticker", "Nombre", "Precio Actual", "P/E Canasta", "Expense Ratio", "Dividend Yield", "Beta"] if c in df_etf.columns]
                    df_etf = df_etf[columnas_etf]
                    
                    st.dataframe(df_etf.style.apply(
                        lambda s: ['background-color: rgba(46,204,113,0.3); font-weight:bold' if v == s[s>0].min() else '' for v in s], subset=["Expense Ratio"] if "Expense Ratio" in df_etf.columns else []
                    ).apply(
                        lambda s: ['background-color: rgba(46,204,113,0.3); font-weight:bold' if v == s.max() else '' for v in s], subset=["Dividend Yield"] if "Dividend Yield" in df_etf.columns else []
                    ).format({
                        "Precio Actual": "{:.2f} USD", "P/E Canasta": "{:.2f}",
                        "Expense Ratio": lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A",
                        "Dividend Yield": lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A", "Beta": "{:.2f}"
                    }, na_rep="N/A"), width="stretch")
                    
                    st.markdown("### 🤖 Informe de Estructura del Portafolio (Asesor ETF)")
                    cetf1, cetf2 = st.columns(2)
                    with cetf1:
                        st.markdown("**💰 Costos de Arrastre:**")
                        er = obj["Expense Ratio"]
                        dy = obj["Dividend Yield"]
                        txt_etf = ""
                        if pd.notna(er):
                            if er > 0.005: txt_etf += f"• ⚠️ **Costo Alto:** Expense Ratio en `{er*100:.2f}%` anual.\n"
                            else: txt_etf += f"• 👍 **Ultra Eficiente:** Comisión baja (`{er*100:.2f}%` anual).\n"
                        if pd.notna(dy) and dy > 0: txt_etf += f"• 💵 **Renta Pasiva:** Dividend Yield del `{dy*100:.2f}%` anual.\n"
                        st.write(txt_etf)
                    with cetf2:
                        st.markdown("**⚡ Volatilidad Sistémica:**")
                        bt = obj["Beta"]
                        if pd.notna(bt):
                            if bt > 1.2: st.warning(f"⚡ **PERFIL AGRESIVO (Beta: {bt:.2f}):** Movimiento amplificado respecto al mercado.")
                            elif bt < 0.8: st.success(f"🛡️ **PERFIL DEFENSIVO (Beta: {bt:.2f}):** Amortiguado ideal para conservadores.")
                            else: st.info(f"⚖️ **PERFIL MODERADO (Beta: {bt:.2f}):** Se desplaza en sintonía con los índices.")

            # --- PESTAÑA 2: CALCULADORA DCF ---
            with tab2:
                if not es_etf_target:
                    st.subheader(f"🧮 Modelo de Flujos de Caja Descontados (DCF) - {ticker_objetivo}")
                    fcf, sh, pr = obj["FCF_Total"], obj["Acciones"], obj["Precio Actual"]
                    if pd.notna(fcf) and pd.notna(sh) and sh > 0 and fcf > 0:
                        fcf_a = fcf / sh
                        cd1, cd2, cd3 = st.columns(3)
                        with cd1: cw = st.slider("Crecimiento Estimado (Años 1-5):", 0, 40, 12, 1, "%d%%") / 100
                        with cd2: td = st.slider("Tasa de Descuento Exigida (WACC):", 5, 25, 10, 1, "%d%%") / 100
                        with cd3: mt = st.slider("Múltiplo Terminal Solicitado (EV/EBITDA):", 3, 20, 6, 1, "%dx")
                        
                        f_p = [fcf_a * ((1+cw)**i) / ((1+td)**i) for i in range(1, 6)]
                        v_t = (fcf_a * ((1+cw)**5) * mt) / ((1+td)**5)
                        v_i = sum(f_p) + v_t
                        
                        st.markdown("#### 🎯 Resultados del Escenario Proyectado")
                        cr1, cr2 = st.columns(2)
                        with cr1:
                            st.metric("FCF por Acción Inicial", f"{fcf_a:.2f} USD")
                            st.metric("VALOR INTRÍNSECO TEÓRICO (Fair Value)", f"{v_i:.2f} USD")
                        with cr2:
                            st.metric("Precio de Cierre en Mercado", f"{pr:.2f} USD")
                            if v_i > pr: st.success(f"📈 **MARGEN DE SEGURIDAD: {((v_i-pr)/v_i)*100:.1f}%**")
                            else: st.error(f"📉 **SOBREPRECIO ESTIMADO: {((pr-v_i)/v_i)*100:.1f}%**")
                    else:
                        st.info("ℹ️ El modelo DCF requiere flujos de caja libre corporativos positivos para proyectar.")
                else:
                    st.info("ℹ️ Los modelos de flujos descontados (DCF) no aplican a ETFs. Usar Tab 1.")

            # --- PESTAÑA 3: ESTRATEGIA TÉCNICA ---
            with tab3:
                st.subheader(f"📐 Suite de Indicadores Técnicos y Temporales - {ticker_objetivo}")
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
                        with m1: st.metric(label="Precio vs. EMA 30", value=f"{precio_hoy:.2f} USD", delta=f"{precio_hoy - ema_30_hoy:.2f} USD")
                        with m2: st.metric(label="Dirección de Flujo (+DI / -DI)", value=f"{p_di_hoy:.1f} vs {m_di_hoy:.1f}", delta=f"{p_di_hoy - m_di_hoy:.1f} Pts")
                        with m3: st.metric(label="Intensidad de Tendencia (ADX)", value=f"{adx_hoy:.1f} Pts", delta="Tendencia Activa" if adx_hoy > 20 else "Compresión", delta_color="normal" if adx_hoy > 20 else "off")
                        
                        st.markdown("### 📈 Tendencia de Mediano Plazo (Precio vs. EMA 30)", help="Línea azul: precio. Línea roja: EMA 30.")
                        df_p = pd.DataFrame({"Precio Cierre": cierre, "EMA 30": calc_ema_30}, index=h_tecn.index)
                        st.line_chart(df_p, height=300, use_container_width=True)
                        
                        st.markdown("### 📊 Oscilador Direccional Completo (DMI 14 / ADX 14)", help="+DI (Azul): Fuerza Compradora. -DI (Roja): Fuerza Vendedora. ADX (Verde): Intensidad.")
                        df_d = pd.DataFrame({"+DI": series_plus_di, "-DI": series_minus_di, "ADX": series_adx}, index=h_tecn.index)
                        st.line_chart(df_d, height=200, use_container_width=True)
                        
                        st.markdown("### 🎯 Conclusión Técnica Estructural")
                        rec_col1, rec_col2 = st.columns(2)
                        with rec_col1:
                            st.markdown("**🔍 Resumen del Algoritmo:**")
                            if precio_hoy > ema_30_hoy: st.write("• **Estructura:** Ciclo alcista activo operando arriba de la EMA 30.")
                            else: st.write("• **Estructura:** Ciclo correctivo activo operando abajo de la EMA 30.")
                            if p_di_hoy > m_di_hoy: st.write(f"• **Flujo:** Control comprador dominando la escena estructural.")
                            else: st.write(f"• **Flujo:** Presión vendedora ejerciendo el control del libro de órdenes.")
                            if adx_hoy > 25: st.write(f"• **Fuerza:** Tendencia completamente madura respaldada institucionalmente.")
                            else: st.write(f"• **Fuerza:** Fase de compresión o distribución errática sin dirección clara.")
                        with rec_col2:
                            st.markdown("**🚀 Sugerencia y Sincronización:**")
                            if precio_hoy > ema_30_hoy and p_di_hoy > m_di_hoy and adx_hoy > 20: st.success("🟩 **ACCIONAR: LONG**\n\nTodos los vectores técnicos alineados en suba. Zona ideal para sumarse al movimiento.")
                            elif precio_hoy < ema_30_hoy and m_di_hoy > p_di_hoy and adx_hoy > 20: st.error("🚨 **ACCIONAR: REDUCIR EXPOSICIÓN**\n\nTendencia bajista consolidada con fuerza institucional. Mantenerse al margen.")
                            elif adx_hoy < 20: st.warning("🟨 **ACCIONAR: PACIENCIA**\n\nTendencia ausente. El mercado va a picar de forma errática. Esperar rupturas.")
                            else: st.info("🟦 **ACCIONAR: MONITOREO**\n\nFuerzas mixtas en zona de transición o rango de acumulación.")
                    else:
                        st.info("Historial insuficiente para métricas de tiempo.")
                except:
                    st.info("Módulo analítico en espera.")

# --- FOOTER DE FIRMA Y DISCLAIMER LEGAL ---
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #888888; font-size: 11px; max-width: 900px; margin: 0 auto; line-height: 1.4;'>"
    "<strong>AVISO LEGAL / DISCLAIMER INFORMATIVO:</strong> El contenido, cálculos automáticos, métricas y sugerencias operativas emitidos por esta plataforma "
    "tienen un propósito estrictamente educativo y de simulación quantitative. No constituyen, bajo ningún concepto, asesoramiento financiero directo, "
    "recomendación implícita de compra/venta, ni una oferta pública de valores negociables. El desarrollador no se responsabiliza por pérdidas o decisiones operativas tomadas en base a estos datos."
    "</p>",
    unsafe_allow_html=True
)
st.markdown(
    "<p style='text-align: center; color: #aaaaaa; font-size: 14px; margin-top: 15px;'>"
    "Desarrollado por <strong>Facundo Garcia Marquez</strong> | "
    "<a href='https://www.linkedin.com/in/facundo-garciamarquez/?locale=es' target='_blank' style='color: #0077B5; text-decoration: none;'>🔗 Conectemos en LinkedIn</a>"
    "</p>",
    unsafe_allow_html=True
)