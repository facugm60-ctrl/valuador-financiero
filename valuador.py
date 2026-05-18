import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

st.set_page_config(page_title="Valuador Financiero Avanzado", layout="wide")

st.title("📊 Plataforma de Valuación de Empresas Públicas")
st.markdown("Analizá ratios financieros, salud de balance y calculá el Valor Intrínseco en tiempo real.")

# Entrada de datos
col1, col2 = st.columns([1, 2])
with col1:
    ticker_objetivo = st.text_input("Introduce el Ticker Objetivo:", value="VIST").upper()
with col2:
    competidores_input = st.text_input("Introduce Competidores (separados por coma):", value="YPF, XOM, PAM")
    competidores = [c.strip().upper() for c in competidores_input.split(",") if c.strip()]

todos_los_tickers = [ticker_objetivo] + competidores

def obtener_ratios(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        if not info or ('currentPrice' not in info and 'previousClose' not in info):
            return None
            
        total_deuda = info.get("totalDebt", 0)
        caja = info.get("totalCash", 0)
        ebitda = info.get("ebitda", 0)
        
        deuda_neta = total_deuda - caja
        net_debt_ebitda = deuda_neta / ebitda if ebitda and ebitda > 0 else None
            
        return {
            "Ticker": ticker_symbol,
            "Nombre": info.get("longName", "N/A"),
            "Precio Actual": info.get('currentPrice', info.get('previousClose', 0)),
            "Forward P/E": info.get("forwardPE"),
            "EV/EBITDA": info.get("enterpriseToEbitda"),
            "P/B Ratio": info.get("priceToBook"),
            "Deuda Neta/EBITDA": net_debt_ebitda,
            "Liquidez Corriente": info.get("currentRatio"),
            "Beta": info.get("beta"),
            "Margen Neto": info.get("profitMargins"),
            "ROE": info.get("returnOnEquity"),
            # Datos crudos necesarios para el modelo DCF matemático
            "FCF_Total": info.get("freeCashflow"),
            "Acciones_Circulacion": info.get("sharesOutstanding")
        }
    except:
        return None

# --- FUNCIONES DE ESTILO INTELIGENTE ---
def resaltar_maximo(s):
    is_max = s == s.max()
    return ['background-color: rgba(46, 204, 113, 0.4); font-weight: bold' if v else '' for v in is_max]

def resaltar_minimo(s):
    valores_validos = s[s > 0]
    if valores_validos.empty: return ['' for _ in s]
    is_min = s == valores_validos.min()
    return ['background-color: rgba(46, 204, 113, 0.4); font-weight: bold' if v else '' for v in is_min]


if st.button("🔥 Correr Análisis de Valuación"):
    with st.spinner("Conectando con Wall Street y procesando balances..."):
        datos = []
        for t in todos_los_tickers:
            res = obtener_ratios(t)
            if res: datos.append(res)
            
        if datos:
            df = pd.DataFrame(datos)
            
            # --- SECCIÓN 1: MATRIZ COMPLETA DE DATOS ---
            st.subheader("📋 Matriz Completa de Datos Financieros y de Balance")
            
            df_mostrar = df.copy().drop(columns=["FCF_Total", "Acciones_Circulacion"])
            styled_df = df_mostrar.style.apply(resaltar_minimo, subset=["Forward P/E", "EV/EBITDA", "P/B Ratio", "Deuda Neta/EBITDA"])\
                                      .apply(resaltar_maximo, subset=["Liquidez Corriente", "Margen Neto", "ROE"])\
                                      .format({
                                          "Precio Actual": "{:.2f} USD", "Forward P/E": "{:.2f}",
                                          "P/B Ratio": "{:.2f}", "EV/EBITDA": "{:.2f}", 
                                          "Deuda Neta/EBITDA": "{:.2f}x", "Liquidez Corriente": "{:.2f}x",
                                          "Beta": "{:.2f}",
                                          "Margen Neto": lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A",
                                          "ROE": lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A"
                                      }, na_rep="N/A")
            
            st.dataframe(styled_df, width="stretch", column_config={
                "Forward P/E": st.column_config.NumberColumn("Forward P/E ❓", help="Mide cuántas veces pagás las ganancias estimadas del próximo año. Menor implica descuento."),
                "EV/EBITDA": st.column_config.NumberColumn("EV/EBITDA ❓", help="Mide el valor de adquisición del negocio sobre su caja operativa bruta. Clave para comparar el sector."),
                "P/B Ratio": st.column_config.NumberColumn("P/B Ratio ❓", help="Precio / Valor en Libros: Compara la valuación de mercado con el patrimonio neto contable."),
                "Deuda Neta/EBITDA": st.column_config.NumberColumn("Deuda Neta/EBITDA ❓", help="Ratio de Apalancamiento: Ideal menor a 2.5x. Si es negativo significa caja neta positiva."),
                "Liquidez Corriente": st.column_config.NumberColumn("Liquidez Corriente ❓", help="Capacidad de pago de corto plazo. Ideal mayor a 1.0x."),
                "Beta": st.column_config.NumberColumn("Beta ❓", help="Volatilidad contra el S&P 500 (Mercado = 1)."),
                "Margen Neto": st.column_config.NumberColumn("Margen Neto ❓", help="Qué porcentaje de los ingresos se convierte en ganancia neta real."),
                "ROE": st.column_config.NumberColumn("ROE ❓", help="Rentabilidad sobre el capital aportado por los socios.")
            })
            
            # --- SECCIÓN 2: MEDIANAS SECTORIALES ---
            df_sector = df[df['Ticker'] != ticker_objetivo]
            medianas = df_sector.median(numeric_only=True) if not df_sector.empty else None
            datos_obj = df[df['Ticker'] == ticker_objetivo].iloc[0]
            
            # --- SECCIÓN 3: ALGORITMO AUDITOR Y ASESOR INTELIGENTE ---
            st.subheader("🤖 Informe del Asesor Inteligente de Inversión")
            
            puntuaciones = {}
            for index, row in df.iterrows():
                ticker = row["Ticker"]
                score = 0
                if pd.notna(row["Forward P/E"]) and medianas is not None and row["Forward P/E"] < medianas["Forward P/E"]: score += 1
                if pd.notna(row["EV/EBITDA"]) and medianas is not None and row["EV/EBITDA"] < medianas["EV/EBITDA"]: score += 1
                if pd.notna(row["ROE"]) and medianas is not None and row["ROE"] > medianas["ROE"]: score += 1
                if pd.notna(row["Deuda Neta/EBITDA"]):
                    if row["Deuda Neta/EBITDA"] > 3.0: score -= 2  
                    elif row["Deuda Neta/EBITDA"] < 1.5: score += 1 
                if pd.notna(row["Liquidez Corriente"]) and row["Liquidez Corriente"] >= 1.2: score += 1
                puntuaciones[ticker] = score

            mejor_ticker = max(puntuaciones, key=puntuaciones.get)
            
            col_inf1, col_inf2 = st.columns(2)
            with col_inf1:
                st.markdown(f"**Auditoría de Balance y Riesgo para {ticker_objetivo}:**")
                analisis_txt = ""
                deb_obj = datos_obj["Deuda Neta/EBITDA"]
                if pd.notna(deb_obj):
                    if deb_obj > 3.0:
                        analisis_txt += f"• ⚠️ **Riesgo de Deuda:** El ratio Deuda Neta/EBITDA es de {deb_obj:.2f}x. Es un nivel de apalancamiento peligroso.\n"
                    elif deb_obj < 0:
                        analisis_txt += f"• 🛡️ **Excelente Solvencia:** Su Deuda Neta es negativa ({deb_obj:.2f}x). Posee más efectivo que pasivos financieros totales.\n"
                    else:
                        analisis_txt += f"• 👍 **Deuda Controlada:** El ratio Deuda Neta/EBITDA se encuentra en un rango saludable de {deb_obj:.2f}x.\n"
                
                liq_obj = datos_obj["Liquidez Corriente"]
                if pd.notna(liq_obj):
                    if liq_obj < 1.0:
                        analisis_txt += f"• 🚨 **Alerta de Liquidez:** Registra una liquidez de {liq_obj:.2f}x. Estrés financiero potencial.\n"
                    else:
                        analisis_txt += f"• 👍 **Fondeo de Corto Plazo:** Cubre perfectamente sus compromisos inmediatos ({liq_obj:.2f}x).\n"
                st.write(analisis_txt)

            with col_inf2:
                st.markdown("**🎯 Sugerencia Estratégica del Sistema:**")
                if pd.notna(datos_obj["Deuda Neta/EBITDA"]) and datos_obj["Deuda Neta/EBITDA"] > 3.0:
                    st.error(f"🚨 **RECOMENDACIÓN: EVITAR / ALTO RIESGO**\n\nA pesar de los múltiplos, **{ticker_objetivo}** presenta un nivel de endeudamiento crítico.")
                elif mejor_ticker == ticker_objetivo and puntuaciones[ticker_objetivo] >= 3:
                    st.success(f"🟩 **RECOMENDACIÓN: COMPRAR / FOCO EN {ticker_objetivo}**\n\nEl activo pasa las auditorías de riesgo. Combina múltiplos atractivos con un balance muy sólido.")
                elif mejor_ticker != ticker_objetivo:
                    st.warning(f"🟨 **RECOMENDACIÓN: EVALUAR ALTERNATIVAS**\n\nEl algoritmo detectó un perfil financiero/riesgo más óptimo en **{mejor_ticker}**.")
                else:
                    st.info(f"🟪 **RECOMENDACIÓN: MANTENER / RANGOS MEDIOS**\n\nEl activo cotiza en línea con sus competidores.")

            # --- NUEVA SECCIÓN 4: MODELO DE VALUACIÓN INTRÍNSECA (DCF SIMPLIFICADO) ---
            st.markdown("---")
            st.subheader(f"🧮 Calculadora de Valor Intrínseco (DCF) para {ticker_objetivo}")
            st.markdown("Proyectá los flujos futuros de la empresa para determinar si cotiza con descuento teórico (Margen de Seguridad).")
            
            fcf_total = datos_obj["FCF_Total"]
            shares = datos_obj["Acciones_Circulacion"]
            precio_actual = datos_obj["Precio Actual"]
            
            if pd.notna(fcf_total) and pd.notna(shares) and shares > 0 and fcf_total > 0:
                fcf_por_accion = fcf_total / shares
                
                # Sliders interactivos en pantalla para simular escenarios
                col_dcf1, col_dcf2, col_dcf3 = st.columns(3)
                with col_dcf1:
                    crecimiento = st.slider("Crecimiento Anual Estimado (Años 1-5):", min_value=0, max_value=40, value=12, step=1, format="%d%%") / 100
                with col_dcf2:
                    tasa_descuento = st.slider("Tasa de Descuento Exigida (WACC):", min_value=5, max_value=25, value=10, step=1, format="%d%%") / 100
                with col_dcf3:
                    multiplo_terminal = st.slider("Múltiplo EV/EBITDA Terminal (Año 5):", min_value=3, max_value=20, value=6, step=1, format="%dx")
                
                # Ejecución matemática del DCF
                flujos_proyectados = []
                fcf_temp = fcf_por_accion
                
                # Proyectamos y descontamos los flujos de los próximos 5 años
                for ano in range(1, 6):
                    fcf_temp = fcf_temp * (1 + crecimiento)
                    fcf_descontado = fcf_temp / ((1 + tasa_descuento) ** ano)
                    flujos_proyectados.append(fcf_descontado)
                
                # Calculamos el Valor Terminal en base al múltiplo y lo descontamos
                valor_terminal_accion = fcf_temp * multiplo_terminal
                valor_terminal_descontado = valor_terminal_accion / ((1 + tasa_descuento) ** 5)
                
                # Valor intrínseco total = Suma de flujos descontados + Valor terminal descontado
                valor_intrinseco = sum(flujos_proyectados) + valor_terminal_descontado
                
                # Estructura de resultados visuales
                col_res1, col_res2 = st.columns(2)
                with col_res1:
                    st.metric("Flujo de Caja Libre Actual por Acción:", f"{fcf_por_accion:.2f} USD")
                    st.metric("VALOR INTRÍNSECO TEÓRICO (Fair Value):", f"{valor_intrinseco:.2f} USD")
                
                with col_res2:
                    st.metric("Precio Actual en Mercado:", f"{precio_actual:.2f} USD")
                    
                    if valor_intrinseco > precio_actual:
                        margen_seguridad = ((valor_intrinseco - precio_actual) / valor_intrinseco) * 100
                        st.success(f"📈 **Margen de Seguridad: {margen_seguridad:.1f}%**\n\nEl activo cotiza por debajo de su valor intrínseco estimado. Presenta una oportunidad atractiva bajo las premisas seleccionadas.")
                    else:
                        sobreprecio = ((precio_actual - valor_intrinseco) / valor_intrinseco) * 100
                        st.error(f"📉 **Sobreprecio: {sobreprecio:.1f}%**\n\nEl precio de mercado supera el valor estimado por los flujos descontados. El activo podría estar exigiendo premisas de crecimiento demasiado agresivas.")
            else:
                st.info(f"ℹ️ Yahoo Finance no reporta Flujo de Caja Libre (FCF) positivo reciente para {ticker_objetivo}. No se puede ejecutar el modelo DCF de forma automatizada para este activo.")
        else:
            st.error("No se pudieron recopilar datos.")