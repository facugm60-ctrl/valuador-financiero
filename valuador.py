import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import streamlit.components.v1 as components

st.set_page_config(page_title="Valuador Pro", layout="wide")
st.title("📊 Plataforma de Valuación de Empresas Públicas")
st.markdown("Ratios, salud de balance, flujos descontados y análisis técnico avanzado.")

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

            # 4. NUEVA SECCIÓN: BACKEND DE ANÁLISIS TÉCNICO MATEMÁTICO
            st.markdown("---")
            st.subheader(f"📐 Auditoría de Indicadores Técnicos Clave - {ticker_objetivo}")
            
            try:
                # Descargamos historial diario de 1 año para computar indicadores
                h_tecn = yf.Ticker(ticker_objetivo).history(period="1y")
                if len(h_tecn) > 50:
                    cierre = h_tecn['Close']
                    precio_hoy = cierre.iloc[-1]
                    
                    # Cómputo de la Media Móvil Exponencial institucional (EMA 200 aproximada por ruedas disponibles)
                    ema_ruedas = min(200, len(cierre))
                    ema_inst = cierre.ewm(span=ema_ruedas, adjust=False).mean().iloc[-1]
                    
                    # Cómputo del RSI clásico de 14 ruedas
                    delta = cierre.diff()
                    ganancia = delta.clip(lower=0)
                    perdida = -delta.clip(upper=0)
                    ema_gan = ganancia.ewm(com=13, adjust=False).mean()
                    ema_per = perdida.ewm(com=13, adjust=False).mean()
                    rs = index_rsi = 100 - (100 / (1 + (ema_gan / ema_per))).iloc[-1]
                    
                    # Desglose del informe técnico en pantalla
                    ct1, ct2, ct3 = st.columns(3)
                    
                    with ct1:
                        st.markdown("**📈 Tendencia Estructural (EMA)**")
                        if precio_hoy > ema_inst:
                            st.markdown(f"🟢 **TENDENCIA ALCISTA:** El precio ({precio_hoy:.2f} USD) cotiza **por encima** de su media estructural ({ema_inst:.2f} USD). Dominio comprador de largo plazo.")
                        else:
                            st.markdown(f"🔴 **TENDENCIA BAJISTA:** El precio ({precio_hoy:.2f} USD) cotiza **por debajo** de su media estructural ({ema_inst:.2f} USD). Presión vendedora dominante.")
                            
                    with ct2:
                        st.markdown("**⚡ Impulso de Mercado (RSI)**")
                        if rs >= 70:
                            st.markdown(f"🚨 **SOBRECOMPRA ({rs:.1f} pts):** El activo muestra una aceleración excesiva. Riesgo latente de corrección por agotamiento de compradores.")
                        elif rs <= 30:
                            st.markdown(f"🛒 **SOBREVENTA ({rs:.1f} pts):** Castigo excesivo en el precio. Zona de capitulación histórica que suele activar algoritmos de rebote.")
                        else:
                            st.markdown(f"⚖️ **RANGO NEUTRO ({rs:.1f} pts):** Flujo de fuerza equilibrado. El precio se desplaza sin distorsiones extremas de codicia o pánico.")
                            
                    with ct3:
                        st.markdown("**💰 Flujo y Convergencia (MACD/Precio)**")
                        # Miramos el impulso de corto plazo contra el de mediano
                        ema12 = cierre.ewm(span=12, adjust=False).mean().iloc[-1]
                        ema26 = cierre.ewm(span=26, adjust=False).mean().iloc[-1]
                        if ema12 > ema26:
                            st.markdown("🟢 **MOMENTUM ACELERANDO:** El flujo de dinero de corto plazo está entrando con mayor velocidad que el promedio mensual. Fuerza a favor del movimiento.")
                        else:
                            st.markdown("🔴 **MOMENTUM DESACELERANDO:** Pérdida de tracción. El promedio de corto plazo se cruza a la baja, indicando salida distributiva de capital.")
                else:
                    st.info("Historial de mercado insuficiente para automatizar el dictamen técnico.")
            except:
                st.info("No se pudieron pre-calcular los indicadores en el backend.")

            # 5. GRÁFICO INTERACTIVO DE TRADINGVIEW
            st.subheader("🖥️ Terminal Táctica de TradingView")
            st.caption("💡 Tip de Analista: Podés meter herramientas de dibujo a la izquierda y cambiar indicadores (RSI, MACD, Medias) dándole al botón 'fx' de arriba.")
            
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
              "container_id": "tradingview_advanced_chart"
            }});
            </script>
            """
            components.html(tradingview_html, height=620, scrolling=False)
        else:
            st.error("No se pudieron recopilar datos.")