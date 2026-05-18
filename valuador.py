import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import urllib.parse
import requests

# Configuración limpia de la página
st.set_page_config(page_title="Valuador Financiero Pro", layout="wide", initial_sidebar_state="collapsed")

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

# Función auxiliar de traducción rápida
def traducir_espanol(texto):
    if not texto or texto == "Sin descripción disponible.": return texto
    try:
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=es&dt=t&q=" + urllib.parse.quote(texto)
        r = requests.get(url, timeout=5).json()
        return "".join([frase[0] for frase in r[0] if frase[0]])
    except: return texto

# Captura de datos financieros y logos
def obtener_datos(symbol):
    try:
        t = yf.Ticker(symbol)
        inf = t.info
        if not inf: return None
        
        # Generación de URL de Logo estable
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
        
        if not tiene_ebitda: # Es un ETF
            common.update({
                "Tipo": "ETF", "P/E Canasta": inf.get("trailingPE"), 
                "Expense Ratio": inf.get("feesExpensesInvestmentPercentage"),
                "Dividend Yield": inf.get("dividendYield"), "Beta": inf.get("beta")
            })
        else: # Es una Acción
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

# Ejecución principal del script
if st.button("🔥 EJECUTAR DIAGNÓSTICO INTEGRAL"):
    with st.spinner("Sincronizando bases de datos operativas..."):
        datos = [obtener_datos(t) for t in todos_tickers if obtener_datos(t)]
        df_verif = pd.DataFrame(datos) if datos else pd.DataFrame()
        
        if df_verif.empty or ticker_objetivo not in df_verif['Ticker'].values:
            st.error(f"🚨 **ERROR:** No se pudieron recuperar registros estables para '{ticker_objetivo}'.")
        else:
            df = pd.DataFrame(datos)
            obj = df[df['Ticker'] == ticker_objetivo].iloc[0]
            es_etf_target = obj["Tipo"] == "ETF"
            
            # CABECERA VISUAL CON LOGO NATIVO DE STREAMLIT
            st.markdown("---")
            c_head1, c_head2 = st.columns([1, 15])
            with c_head1:
                st.image(obj["Logo"], width=50)
            with c_head2:
                st.header(f"{obj['Nombre']} ({obj['Ticker']})")

            # INTERFAZ ULTRA-MEJORADA PARA MOBILE: MENÚ DESPLEGABLE DE CONTROL
            st.markdown("### 🎛️ Panel de Navegación Táctica")
            seccion_activa = st.selectbox(
                "Elegí el módulo analítico que querés desplegar en pantalla:",
                ["📋 Módulo Fundamental y Coyuntura", "🧮 Calculadora de Valor Intrínseco (DCF)", "📐 Estrategia Técnica y Timing (DMI)"]
            )
            st.markdown("---")

            # --- SECCIÓN 1: MODULO FUNDAMENTAL ---
            if seccion_activa == "📋 MÓDULO FUNDAMENTAL y Coyuntura":
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
                    st.subheader(f"💰 Política de Dividendos - {ticker_objetivo}")
                    d_rate, d_yield = obj.get("Div_Rate", 0), obj.get("Div_Yield", 0)
                    if pd.notna(d_rate) and d_rate > 0:
                        cdiv1, cdiv2 = st.columns(2)
                        with cdiv1: st.metric("Dividend Yield Anual", f"{d_yield*100:.2f}%")
                        with cdiv2: st.metric("Total Distribuido Último Año", f"{d_rate:.2f} USD")
                    else: st.info(f"ℹ️ {ticker_objetivo} no registra pago de dividendos activos en su estructura.")
                    
                    st.markdown("---")
                    st.subheader("🤖 Informe del Asesor Inteligente (Pros & Contras)")
                    cp, cc = st.columns(2)
                    with cp:
                        st.markdown("** MyFortalezas Operativas:**")
                        lq = obj["Liquidez Corriente"]
                        mn = obj["Margen Neto"]
                        txt_p = "• Ventaja competitiva sostenida en el mercado.\n• Captura óptima de flujos comerciales grandes.\n"
                        if pd.notna(lq) and lq > 1.5: txt_p += f"• Solvencia de corto plazo robusta ({lq:.2f}x).\n"
                        if pd.notna(mn) and mn > 0.15: txt_p += f"• Capacidad de defensa de márgenes netos ({mn*100:.1f}%).\n"
                        st.write(txt_p)
                    with cc:
                        st.markdown("** Riscos y Coyuntura:**")
                        db = obj["Deuda Neta/EBITDA"]
                        txt_c = "• Exposición a variables macroeconómicas globales.\n• Presión por elevados planes de reinversión en Capex que estresan transitoriamente la caja libre antes de traccionar los ingresos de los nuevos contratos comerciales.\n"
                        if pd.notna(db) and db > 2.5: txt_c += f"• Apalancamiento consolidado arriba de promedios sanos ({db:.2f}x).\n"
                        st.write(txt_c)
                else:
                    st.subheader("📋 Matriz Estructural de Fondos (ETFs)")
                    df_etf = df[df['Tipo'] == "ETF"].copy()
                    columnas_etf = [c for c in ["Ticker", "Nombre", "Precio Actual", "P/E Canasta", "Expense Ratio", "Dividend Yield", "Beta"] if c in df_etf.columns]
                    st.dataframe(df_etf[columnas_etf].set_index('Ticker').style.format({
                        "Precio Actual": "{:.2f} USD", "P/E Canasta": "{:.2f}",
                        "Expense Ratio": lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A",
                        "Dividend Yield": lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A", "Beta": "{:.2f}"
                    }, na_rep="N/A"), width="stretch")

            # --- SECCIÓN 2: MODELO DCF ---
            elif seccion_activa == "🧮 Calculadora de Valor Intrínseco (DCF)":
                if not es_etf_target:
                    st.subheader(f"🧮 Modelo de Flujos de Caja Descontados (DCF) - {ticker_objetivo}")
                    fcf, sh, pr = obj["FCF_Total"], obj["Acciones"], obj["Precio Actual"]
                    if pd.notna(fcf) and fcf > 0 and sh > 0:
                        fcf_a = fcf / sh
                        cd1, cd2, cd3 = st.columns(3)
                        with cd1: cw = st.slider("Crecimiento Estimado (Años 1-5):", 0, 40, 12, 1, "%d%%") / 100
                        with cd2: td = st.slider("Tasa de Descuento Exigida (WACC):", 5, 25, 10, 1, "%d%%") / 100
                        with cd3: mt = st.slider("Múltiplo Terminal Estimado:", 3, 20, 6, 1, "%dx")
                        
                        f_p = [fcf_a * ((1+cw)**i) / ((1+td)**i) for i in range(1, 6)]
                        v_t = (fcf_a * ((1+cw)**5) * mt) / ((1+td)**5)
                        v_i = sum(f_p) + v_t
                        
                        cr1, cr2 = st.columns(2)
                        with cr1:
                            st.metric("FCF por Acción Inicial", f"{fcf_a:.2f} USD")
                            st.metric("VALOR INTRÍNSECO TEÓRICO (Fair Value)", f"{v_i:.2f} USD")
                        with cr2:
                            st.metric("Precio Actual en Mercado", f"{pr:.2f} USD")
                            if v_i > pr: st.success(f"📈 **MARGEN DE SEGURIDAD: {((v_i-pr)/v_i)*100:.1f}%**")
                            else: st.error(f"📉 **SOBREPRECIO ESTIMADO: {((pr-v_i)/v_i)*100:.1f}%**")
                    else: st.info("ℹ️ El modelo DCF requiere flujos de caja corporativos (FCF) positivos para proyectar.")
                else: st.info("ℹ️ Los modelos de flujos descontados corporativos no aplican a ETFs. Revisar múltiplos en Sección 1.")

            # --- SECCIÓN 3: ESTRATEGIA TÉCNICA ---
            elif seccion_activa == "📐 Estrategia Técnica y Timing (DMI)":
                st.subheader(f"📐 Terminal de Indicadores Técnicos y Timing - {ticker_objetivo}")
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
                        
                        st.markdown("### 📈 Panel A: Tendencia (Precio vs. EMA 30)")
                        with st.expander("🔍 ¿Cómo leer este gráfico Panel A?"):
                            st.write("• **Línea Azul:** Precio diario real de mercado.\n• **Línea Roja (EMA 30):** Si el precio cotiza **por arriba**, la inercia es alcista; si cotiza **por debajo**, la presión es vendedora.")
                        df_p = pd.DataFrame({"Precio Cierre": cierre, "EMA 30": calc_ema_30}, index=h_tecn.index)
                        st.line_chart(df_p, height=300, use_container_width=True)
                        
                        st.markdown("### 📊 Panel B: Oscilador Direccional Completo (DMI 14 / ADX 14)")
                        with st.expander("🔍 ¿Cómo leer este gráfico Panel B?"):
                            st.write("• **+DI (Azul):** Fuerza Compradora. \n• **-DI (Roja):** Fuerza Vendedora. \n• **ADX (Verde):** Fuerza general del movimiento. Arriba de 20 puntos valida una tendencia sana e institucional.")
                        df_d = pd.DataFrame({"+DI": series_plus_di, "-DI": series_minus_di, "ADX": series_adx}, index=h_tecn.index)
                        st.line_chart(df_d, height=200, use_container_width=True)
                        
                        st.markdown("### 🎯 Conclusión del Diagnóstico Técnico")
                        if precio_hoy > ema_30_hoy and p_di_hoy > m_di_hoy and adx_hoy > 20: st.success("🟩 **ALGORITMO: STRATEGY LONG ACTIVADA (ALCISTA)**\n\nTodos los vectores técnicos de precio y flujo empujan en sintonía comprador.")
                        elif precio_hoy < ema_30_hoy and m_di_hoy > p_di_hoy and adx_hoy > 20: st.error("🚨 **ALGORITMO: ALERTA DE PRESIÓN BAJISTA (REDUCIR)**\n\nInercia vendedora al mando respaldada por fuerza direccional.")
                        elif adx_hoy < 20: st.warning("🟨 **ALGORITMO: FASE DE COMPRESIÓN (PACIENCIA)**\n\nTendencia ausente. Oscilaciones erráticas en rango lateral. Esperar definiciones.")
                        else: st.info("🟦 **ALGORITMO: ZONA DE TRANSICIÓN (CAUTELA)**\n\nLecturas cruzadas de momentum en zona de rango o balanceo de carteras.")
                except: st.info("Historial de mercado consolidándose.")

# --- FOOTER DE FIRMA Y BLINDAJE LEGAL ---
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #888888; font-size: 11px; max-width: 900px; margin: 0 auto; line-height: 1.4;'>"
    "<strong>AVISO LEGAL / DISCLAIMER INFORMATIVO:</strong> El contenido, cálculos automáticos, métricas y sugerencias operativas emitidos por esta plataforma "
    "tienen un propósito estrictamente educativo. No constituyen asesoramiento financiero ni recomendación implícita de compra/venta pública de valores. El desarrollador no se responsabiliza por decisiones operativas tomadas en base a estos datos."
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