import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

st.set_page_config(page_title="Valuador Pro", layout="wide")
st.title("📊 Plataforma de Valuación de Empresas Públicas y ETFs")
st.markdown("Análisis fundamental de acciones, métricas estructurales de ETFs e inteligencia técnica avanzada.")

# Inputs de usuario
col1, col2 = st.columns([1, 2])
with col1:
    ticker_objetivo = st.text_input("Ticker Objetivo (ej. VIST, SPY, TXAR.BA):", value="VIST").upper()
with col2:
    comp_in = st.text_input("Competidores (separados por coma):", value="YPF, XOM, PAM")
    competidores = [c.strip().upper() for c in comp_in.split(",") if c.strip()]

todos_tickers = [ticker_objetivo] + competidores

def obtener_datos(symbol):
    try:
        t = yf.Ticker(symbol)
        inf = t.info
        if not inf: return None
        
        # Detectamos si es un ETF o una Acción Corporativa
        es_etf = inf.get("quoteType") == "ETF"
        
        if es_etf:
            return {
                "Ticker": symbol, "Nombre": inf.get("longName", "N/A"),
                "Tipo": "ETF", "Precio Actual": inf.get('currentPrice', inf.get('previousClose', 0)),
                "P/E Canasta": inf.get("trailingPE"), "Expense Ratio": inf.get("feesExpensesInvestmentPercentage"),
                "Dividend Yield": inf.get("dividendYield"), "Beta": inf.get("beta"),
                "FCF_Total": None, "Acciones": None # Atributos corporativos nulos
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

if st.button("🔥 Correr Análisis de Valuación"):
    with st.spinner("Conectando con los servidores de Wall Street..."):
        datos = [obtener_datos(t) for t in todos_tickers if obtener_datos(t)]
        
        # Validación de seguridad antibugs
        df_verif = pd.DataFrame(datos) if datos else pd.DataFrame()
        if df_verif.empty or ticker_objetivo not in df_verif['Ticker'].values:
            st.error(f"🚨 **ERROR DE INDEXACIÓN:** No se pudieron recopilar datos válidos para el activo objetivo **'{ticker_objetivo}'**. Verificar si el ticker requiere algún sufijo (ej. para activos locales usar '.BA' como TXAR.BA o GGAL.BA).")
        else:
            df = pd.DataFrame(datos)
            obj = df[df['Ticker'] == ticker_objetivo].iloc[0]
            es_etf_target = obj["Tipo"] == "ETF"
            
            # --- RAMA 1: ENTORNO EXCLUSIVO PARA ACCIONES CORPORATIVAS ---
            if not es_etf_target:
                st.subheader("📋 Matriz Completa de Datos Financieros (Acciones)")
                df_m = df[df['Tipo'] == "ACCION"].copy().drop(columns=["FCF_Total", "Acciones", "Tipo", "P/E Canasta", "Expense Ratio", "Dividend Yield"])
                
                v_min = ["Forward P/E", "EV/EBITDA", "P/B Ratio", "Deuda Neta/EBITDA"]
                v_max = ["Liquidez Corriente", "Margen Neto", "ROE"]
                
                st.dataframe(df_m.style.apply(
                    lambda s: ['background-color: rgba(46,204,113,0.4); font-weight:bold' if v == s[s>0].min() else '' for v in s], subset=v_min
                ).apply(
                    lambda s: ['background-color: rgba(46,204,113,0.4); font-weight:bold' if v == s.max() else '' for v in s], subset=v_max
                ).format({
                    "Precio Actual": "{:.2f} USD", "Forward P/E": "{:.2f}", "P/B Ratio": "{:.2f}", 
                    "EV/EBITDA": "{:.2f}", "Deuda Neta/EBITDA": "{:.2f}x", "Liquidez Corriente": "{:.2f}x", "Beta": "{:.2f}",
                    "Margen Neto": lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A", "ROE": lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A"
                }, na_rep="N/A"), width="stretch")
                
                df_s = df[(df['Ticker'] != ticker_objetivo) & (df['Tipo'] == "ACCION")]
                meds = df_s.median(numeric_only=True) if not df_s.empty else None
                
                st.subheader("🤖 Informe del Asesor Inteligente")
                c_inf1, c_inf2 = st.columns(2)
                with c_inf1:
                    st.markdown(f"**Auditoría de Balance para {ticker_objetivo}:**")
                    txt = ""
                    db = obj["Deuda Neta/EBITDA"]
                    if pd.notna(db):
                        if db > 3: txt += f"• ⚠️ **Apalancamiento Elevado:** Ratio en {db:.2f}x. Monitorear carga financiera.\n"
                        elif db < 0: txt += f"• 🛡️ **Solvencia Estructural:** Caja neta positiva ({db:.2f}x).\n"
                        else: txt += f"• 👍 **Riesgo de Deuda Bajo:** Ratio saludable en {db:.2f}x.\n"
                    lq = obj["Liquidez Corriente"]
                    if pd.notna(lq):
                        if lq < 1: txt += f"• 🚨 **Falta de Liquidez:** Corto plazo ajustado ({lq:.2f}x).\n"
                        else: txt += f"• 👍 **Fondo de Maniobra Sólido:** Cubre deudas corrientes con {lq:.2f}x.\n"
                    st.write(txt)
                with c_inf2:
                    st.markdown("**🎯 Conclusión Estratégica:**")
                    pe_o = obj["Forward P/E"]
                    pe_m = meds["Forward P/E"] if meds is not None else None
                    if pd.notna(db) and db > 3: st.error("🚨 **EVITAR:** Estructura de capital bajo presión crítica.")
                    elif pd.notna(pe_o) and pd.notna(pe_m) and pe_o < pe_m: st.success("🟩 **COMPRAR / SUBVALUADA:** Múltiplos atractivos frente al sector de referencia.")
                    else: st.info("🟪 **MANTENER:** Cotización en rangos de equilibrio razonables.")

                st.markdown("---")
                st.subheader(f"🧮 Calculadora de Valor Intrínseco (DCF) - {ticker_objetivo}")
                fcf, sh, pr = obj["FCF_Total"], obj["Acciones"], obj["Precio Actual"]
                if pd.notna(fcf) and pd.notna(sh) and sh > 0 and fcf > 0:
                    fcf_a = fcf / sh
                    cd1, cd2, cd3 = st.columns(3)
                    with cd1: cw = st.slider("Crecimiento Estimado (Años 1-5):", 0, 40, 12, 1, "%d%%") / 100
                    with cd2: td = st.slider("Tasa de Descuento (WACC):", 5, 25, 10, 1, "%d%%") / 100
                    with cd3: mt = st.slider("Múltiplo Terminal Solicitado:", 3, 20, 6, 1, "%dx")
                    
                    f_p = [fcf_a * ((1+cw)**i) / ((1+td)**i) for i in range(1, 6)]
                    v_t = (fcf_a * ((1+cw)**5) * mt) / ((1+td)**5)
                    v_i = sum(f_p) + v_t
                    
                    cr1, cr2 = st.columns(2)
                    with cr1:
                        st.metric("FCF por Acción Actual:", f"{fcf_a:.2f} USD")
                        st.metric("VALOR INTRÍNSECO TEÓRICO:", f"{v_i:.2f} USD")
                    with cr2:
                        st.metric("Precio en Mercado:", f"{pr:.2f} USD")
                        if v_i > pr: st.success(f"📈 **Margen de Seguridad: {((v_i-pr)/v_i)*100:.1f}%**")
                        else: st.error(f"📉 **Sobreprecio Estimado: {((pr-v_i)/v_i)*100:.1f}%**")
                else: st.info(f"ℹ️ Módulo DCF en espera: Requiere flujo de caja libre positivo corporativo.")

            # --- RAMA 2: ENTORNO AUTOMÁTICO EXCLUSIVO PARA VALUAR ETFS ---
            else:
                st.subheader("📋 Matriz de Eficiencia y Diversificación (Estructura de ETFs)")
                cols_drop = ["Forward P/E", "EV/EBITDA", "P/B Ratio", "Deuda Neta/EBITDA", "Liquidez Corriente", "Margen Neto", "ROE", "FCF_Total", "Acciones", "Tipo"]
                df_etf = df[df['Tipo'] == "ETF"].copy().drop(columns=cols_drop)
                
                st.dataframe(df_etf.style.apply(
                    lambda s: ['background-color: rgba(46,204,113,0.4); font-weight:bold' if v == s[s>0].min() else '' for v in s], subset=["Expense Ratio"]
                ).apply(
                    lambda s: ['background-color: rgba(46,204,113,0.4); font-weight:bold' if v == s.max() else '' for v in s], subset=["Dividend Yield"]
                ).format({
                    "Precio Actual": "{:.2f} USD", "P/E Canasta": "{:.2f}",
                    "Expense Ratio": lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A",
                    "Dividend Yield": lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A", "Beta": "{:.2f}"
                }, na_rep="N/A"), width="stretch")
                
                st.subheader("🤖 Auditoría de Portafolio de Inversión (Asesor ETF)")
                cetf1, cetf2 = st.columns(2)
                with cetf1:
                    st.markdown(f"**Análisis de Costos y Rentabilidad para {ticker_objetivo}:**")
                    er = obj["Expense Ratio"]
                    dy = obj["Dividend Yield"]
                    txt_etf = ""
                    if pd.notna(er):
                        if er > 0.005: txt_etf += f"• ⚠️ **Administración Cara:** El Expense Ratio es de {er*100:.2f}% anual. Estructura costosa para el largo plazo.\n"
                        else: txt_etf += f"• 👍 **Estructura Ultra-Eficiente:** Costo de arrastre muy bajo ({er*100:.2f}% anual). Ideal para indexación pasiva.\n"
                    if pd.notna(dy) and dy > 0:
                        txt_etf += f"• 💰 **Distribución de Renta:** Devenga un Dividend Yield del {dy*100:.2f}% anual de forma directa a tu cuenta.\n"
                    st.write(txt_etf)
                with cetf2:
                    st.markdown("**🎯 Diagnóstico de Perfil de Riesgo:**")
                    bt = obj["Beta"]
                    if pd.notna(bt):
                        if bt > 1.2: st.warning(f"⚡ **PERFIL AGRESIVO (Beta: {bt:.2f}):** El fondo amplifica los movimientos del mercado. Alta volatilidad sistémica.")
                        elif bt < 0.8: st.success(f"🛡️ **PERFIL DEFENSIVO (Beta: {bt:.2f}):** Comportamiento descorrelacionado o amortiguado. Ideal para perfiles conservadores.")
                        else: st.info(f"⚖️ **PERFIL MODERADO (Beta: {bt:.2f}):** Se desplaza en perfecta sintonía y equilibrio con el mercado general (S&P 500).")

            # --- SECCIÓN TÉCNICA UNIFICADA (Aplica perfectamente a Acciones y ETFs) ---
            st.markdown("---")
            st.subheader(f"📐 Terminal de Datos Técnicos y Estructura de Precios - {ticker_objetivo}")
            
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
                    with m1:
                        st.metric(label="Precio vs. EMA 30", value=f"{precio_hoy:.2f} USD", delta=f"{precio_hoy - ema_30_hoy:.2f} USD vs EMA 30")
                        st.caption("🟩 **Fase Alcista:**" if precio_hoy > ema_30_hoy else "🟥 **Fase Bajista:**")
                    with m2:
                        dmi_diff = p_di_hoy - m_di_hoy
                        st.metric(label="Fuerza Direccional (Cruce DMI)", value=f"+DI {p_di_hoy:.1f} | -DI {m_di_hoy:.1f}", delta=f"{dmi_diff:.1f} Net Comprador" if dmi_diff > 0 else f"{dmi_diff:.1f} Net Vendedor")
                        st.caption("🟢 **Compradores lideran**" if dmi_diff > 0 else "🔴 **Vendedores lideran**")
                    with m3:
                        st.metric(label="Intensidad de Tendencia (ADX)", value=f"{adx_hoy:.1f} Puntos", delta="Tendencia Activa" if adx_hoy > 20 else "Lateralización", delta_color="normal" if adx_hoy > 20 else "off")
                        st.caption("⚡ **Movimiento Fuerte**" if adx_hoy > 25 else "💤 **Rango Lateral**")
                    
                    st.markdown("---")
                    st.markdown("### 📈 Panel A: Tendencia de Mediano Plazo (Precio vs. EMA 30)", help="Línea azul: precio real. Línea roja: media móvil exponencial de 30 días.")
                    df_precio_panel = pd.DataFrame({"Precio Cierre (USD)": cierre, "EMA 30 Ruedas": calc_ema_30}, index=h_tecn.index)
                    st.line_chart(df_precio_panel, height=350, use_container_width=True)
                    
                    st.markdown("### 📊 Panel B: Oscilador Direccional Completo (DMI 14 / ADX 14)", help="+DI (Azul): Fuerza Compradora. -DI (Roja): Fuerza Vendedora. ADX (Verde): Intensidad.")
                    df_dmi_panel = pd.DataFrame({"+DI": series_plus_di, "-DI": series_minus_di, "ADX": series_adx}, index=h_tecn.index)
                    st.line_chart(df_dmi_panel, height=250, use_container_width=True)
                    
                    st.markdown("---")
                    st.subheader("🎯 Diagnóstico Técnico y Recomendación Profesional")
                    rec_col1, rec_col2 = st.columns(2)
                    with rec_col1:
                        st.markdown("**🔍 Resumen Crítico de las Lecturas:**")
                        if precio_hoy > ema_30_hoy: st.write(f"• **Estructura:** El activo mantiene una condición alcista saludable por encima de la EMA 30.")
                        else: st.write(f"• **Estructura:** El activo muestra debilidad estructural por debajo de la EMA 30.")
                        if p_di_hoy > m_di_hoy: st.write(f"• **Flujo:** Dominio de los compradores (`+DI` > `-DI`). Hay presión de demanda.")
                        else: st.write(f"• **Flujo:** Control absoluto de la oferta (`-DI` > `+DI`). Los vendedores dominan.")
                        if adx_hoy > 25: st.write(f"• **Fuerza:** El ADX en `{adx_hoy:.1f} pts` confirma una tendencia madura y activa.")
                        else: st.write(f"• **Fuerza:** El ADX en `{adx_hoy:.1f} pts` delata fatiga o compresión lateral.")
                    with rec_col2:
                        st.markdown("**🚀 Sugerencia Operativa y Timing:**")
                        if precio_hoy > ema_30_hoy and p_di_hoy > m_di_hoy and adx_hoy > 20:
                            st.success("🟩 **ACCIONAR: ESTRATEGIA ALCISTA (LONG)**\n\nIndicadores alineados. Tendencia, flujo y fuerza a favor del movimiento. Zona óptima de entradas.")
                        elif precio_hoy < ema_30_hoy and m_di_hoy > p_di_hoy and adx_hoy > 20:
                            st.error("🚨 **ACCIONAR: REDUCIR EXPOSICIÓN / EVITAR**\n\nEstructura bajista activa. Vendedores al mando con fuerza. Evitar compras hasta recuperar la media.")
                        elif adx_hoy < 20:
                            st.warning("🟨 **ACCIONAR: PACIENCIA / OPERAR RANGOS**\n\nTendencia ausente. El precio oscilará de forma errática. Esperar quiebre con aumento de volumen.")
                        else:
                            st.info("🟦 **ACCIONAR: MONITOREO / CAUTELA**\n\nSeñales mixtas en el precio y osciladores. Mercado en zona de transición.")
                else:
                    st.info("Historial insuficiente.")
            except:
                st.info("Módulo analítico en espera.")