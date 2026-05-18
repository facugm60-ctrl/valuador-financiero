import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import streamlit.components.v1 as components

st.set_page_config(page_title="Valuador Pro", layout="wide")
st.title("📊 Plataforma de Valuación de Empresas Públicas")
st.markdown("Ratios, salud de balance, flujos descontados y análisis táctico avanzado.")

# Inputs
col1, col2 = st.columns([1, 2])
with col1:
    ticker_objetivo = st.text_input("Ticker Objetivo:", value="VIST").upper()
with col2:
    comp_in = st.text_input("Competidores:", value="YPF, XOM, PAM")
    competidores = [c.strip().upper() for c in comp_in.split(",") if c.strip()]

todos_tickers = [ticker_objetivo] + competidores

def obtener_ratios(symbol):
    try:
        t = yf.Ticker(symbol)
        inf = t.info
        if not inf or 'currentPrice' not in inf: return None
        td = inf.get("totalDebt", 0)
        caj = inf.get("totalCash", 0)
        eb = inf.get("ebitda", 1)
        nd_eb = (td - caj) / eb if eb else None
        return {
            "Ticker": symbol, "Nombre": inf.get("longName", "N/A"),
            "Precio Actual": inf.get('currentPrice', 0),
            "Forward P/E": inf.get("forwardPE"), "EV/EBITDA": inf.get("enterpriseToEbitda"),
            "P/B Ratio": inf.get("priceToBook"), "Deuda Neta/EBITDA": nd_eb,
            "Liquidez Corriente": inf.get("currentRatio"), "Beta": inf.get("beta"),
            "Margen Neto": inf.get("profitMargins"), "ROE": inf.get("returnOnEquity"),
            "FCF_Total": inf.get("freeCashflow"), "Acciones": inf.get("sharesOutstanding")
        }
    except: return None

if st.button("🔥 Correr Análisis de Valuación"):
    with st.spinner("Procesando balances y algoritmos técnicos..."):
        datos = [obtener_ratios(t) for t in todos_tickers if obtener_ratios(t)]
        if datos:
            df = pd.DataFrame(datos)
            
            # 1. TABLA PRINCIPAL
            st.subheader("📋 Matriz Completa de Datos Financieros")
            df_m = df.copy().drop(columns=["FCF_Total", "Acciones"])
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
            
            df_s = df[df['Ticker'] != ticker_objetivo]
            meds = df_s.median(numeric_only=True) if not df_s.empty else None
            obj = df[df['Ticker'] == ticker_objetivo].iloc[0]
            
            # 2. ASESOR FUNDAMENTAL
            st.subheader("🤖 Informe del Asesor Inteligente")
            c_inf1, c_inf2 = st.columns(2)
            with c_inf1:
                st.markdown(f"**Auditoría para {ticker_objetivo}:**")
                txt = ""
                db = obj["Deuda Neta/EBITDA"]
                if pd.notna(db):
                    if db > 3: txt += f"• ⚠️ **Deuda Alta:** Ratio en {db:.2f}x. Riesgo elevado.\n"
                    elif db < 0: txt += f"• 🛡️ **Excelente Solvencia:** Caja neta positiva ({db:.2f}x).\n"
                    else: txt += f"• 👍 **Deuda Controlada:** Ratio saludable en {db:.2f}x.\n"
                lq = obj["Liquidez Corriente"]
                if pd.notna(lq):
                    if lq < 1: txt += f"• 🚨 **Alerta Liquidez:** {lq:.2f}x. No cubre el corto plazo.\n"
                    else: txt += f"• 👍 **Corto Plazo Sólido:** Cubre compromisos con {lq:.2f}x.\n"
                st.write(txt)
            with c_inf2:
                st.markdown("**🎯 Sugerencia Estratégica:**")
                pe_o = obj["Forward P/E"]
                pe_m = meds["Forward P/E"] if meds is not None else None
                if pd.notna(db) and db > 3: st.error("🚨 **EVITAR:** Alto riesgo por endeudamiento crítico.")
                elif pd.notna(pe_o) and pd.notna(pe_m) and pe_o < pe_m: st.success("🟩 **COMPRAR:** Activo con descuento relativo y balance estable.")
                else: st.info("🟪 **MANTENER:** Cotiza en rangos medios en línea con sus pares.")

            # 3. DCF
            st.markdown("---")
            st.subheader(f"🧮 Calculadora de Valor Intrínseco (DCF) - {ticker_objetivo}")
            fcf, sh, pr = obj["FCF_Total"], obj["Acciones"], obj["Precio Actual"]
            if pd.notna(fcf) and pd.notna(sh) and sh > 0 and fcf > 0:
                fcf_a = fcf / sh
                cd1, cd2, cd3 = st.columns(3)
                with cd1: cw = st.slider("Crecimiento Anual (Años 1-5):", 0, 40, 12, 1, "%d%%") / 100
                with cd2: td = st.slider("Tasa Descuento (WACC):", 5, 25, 10, 1, "%d%%") / 100
                with cd3: mt = st.slider("Múltiplo Terminal EV/EBITDA:", 3, 20, 6, 1, "%dx")
                
                f_p = [fcf_a * ((1+cw)**i) / ((1+td)**i) for i in range(1, 6)]
                v_t = (fcf_a * ((1+cw)**5) * mt) / ((1+td)**5)
                v_i = sum(f_p) + v_t
                
                cr1, cr2 = st.columns(2)
                with cr1:
                    st.metric("FCF por Acción Actual:", f"{fcf_a:.2f} USD")
                    st.metric("VALOR INTRÍNSECO TEÓRICO:", f"{v_i:.2f} USD")
                with cr2:
                    st.metric("Precio en Mercado:", f"{pr:.2f} USD")
                    if v_i > pr: st.success(f"📈 **Margen de Seguridad: {((v_i-pr)/v_i)*100:.1f}%** (Subvaluada)")
                    else: st.error(f"📉 **Sobreprecio: {((pr-v_i)/v_i)*100:.1f}%** (Sobrevaluada)")
            else: st.info(f"ℹ️ Sin Flujo de Caja Libre positivo para {ticker_objetivo}.")

            # 4. AUDITORÍA TÉCNICA
            st.markdown("---")
            st.subheader(f"📐 Reporte de Indicadores Técnicos de tu Perfil (EMA 30 + DMI) - {ticker_objetivo}")
            try:
                h_tecn = yf.Ticker(ticker_objetivo).history(period="1y")
                if len(h_tecn) > 40:
                    cierre = h_tecn['Close']
                    high = h_tecn['High']
                    low = h_tecn['Low']
                    precio_hoy = cierre.iloc[-1]
                    ema_30 = cierre.ewm(span=30, adjust=False).mean().iloc[-1]
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
                    plus_di = (plus_dm_14 / tr_14) * 100
                    minus_di = (minus_dm_14 / tr_14) * 100
                    dx = (np.abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
                    adx = dx.ewm(alpha=1/14, adjust=False).mean().iloc[-1]
                    p_di_hoy = plus_di.iloc[-1]
                    m_di_hoy = minus_di.iloc[-1]
                    
                    ct1, ct2 = st.columns(2)
                    with ct1:
                        st.markdown("**🟡 Tendencia de Corto/Mediano Plazo (EMA 30)**")
                        if precio_hoy > ema_30: st.markdown(f"🟩 **MOMENTUM POSITIVO:** El precio ({precio_hoy:.2f} USD) cotiza **por encima** de tu EMA 30 ({ema_30:.2f} USD).")
                        else: st.markdown(f"🟥 **MOMENTUM NEGATIVO:** El precio ({precio_hoy:.2f} USD) perforó **a la baja** tu EMA 30 ({ema_30:.2f} USD).")
                    with ct2:
                        st.markdown("**📊 Fuerza y Dirección del Flujo (DMI / ADX 14)**")
                        dir_txt = f"🟢 **CONTROL COMPRADOR:** +DI ({p_di_hoy:.1f}) > -DI ({m_di_hoy:.1f})." if p_di_hoy > m_di_hoy else f"🔴 **CONTROL VENDEDOR:** -DI ({m_di_hoy:.1f}) > +DI ({p_di_hoy:.1f})."
                        fuerza_txt = f"El **ADX en {adx:.1f} pts** confirma una **tendencia fuerte**." if adx > 25 else f"El **ADX en {adx:.1f} pts** indica **compresión o rango lateral**."
                        st.markdown(f"{dir_txt}\n\n{fuerza_txt}")
                else: st.info("Datos insuficientes para el reporte técnico.")
            except: st.info("No se pudieron pre-calcular los indicadores.")

            # 5. GRÁFICO INTERACTIVO CONFIGURADO CON TUS COMPONENTES (EMA30 + DMI)
            st.subheader("🖥️ Terminal Táctica de TradingView")
            
            tradingview_html = f"""
            <div id="tradingview_advanced_chart" style="height:600px;"></div>
            <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
            <script type="text/javascript">
            new TradingView.widget({{
              "width": "100%",
              "height": 600,
              "symbol": "{ticker_objetivo}",
              "interval": "D",
              "timezone": "Etc/UTC",
              "theme": "dark",
              "style": "1",
              "locale": "es",
              "toolbar_bg": "#f1f3f6",
              "enable_publishing": false,
              "hide_side_toolbar": false,
              "allow_symbol_change": true,
              "container_id": "tradingview_advanced_chart",
              "studies": [
                "MASimple@tv-basicstudies", // Forzamos a que pinte medias móviles nativas
                "DirectionalMovementIndex@tv-basicstudies" // Forzamos a que levante el DMI abajo
              ]
            }});
            </script>
            """
            components.html(tradingview_html, height=620, scrolling=False)
        else:
            st.error("No se pudieron recopilar datos.")