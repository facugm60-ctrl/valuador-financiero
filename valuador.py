import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

st.set_page_config(page_title="Valuador Financiero Pro", layout="wide")

st.title("📊 Plataforma de Valuación de Empresas Públicas")
st.markdown("Analizá ratios financieros, salud de balance, flujos descontados y tendencias en tiempo real.")

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
            "FCF_Total": info.get("freeCashflow"),
            "Acciones_Circulacion": info.get("sharesOutstanding")
        }
    except:
        return None

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
                "Forward P/E": st.column_config.NumberColumn("Forward P/E ❓", help="Precio / Ganancia estimada del proximo ano. Menor es mas barato."),
                "EV/EBITDA": st.column_config.NumberColumn("EV/EBITDA ❓", help="Valor de adquisicion / Caja operativa bruta. Clave del sector."),
                "P/B Ratio": st.column_config.NumberColumn("P/B Ratio ❓", help="Precio / Valor en Libros contable. Respaldo patrimonial."),
                "Deuda Neta/EBITDA": st.column_config.NumberColumn("Deuda Neta/EBITDA ❓", help="Apalancamiento: ideal menor a 2.5x. Negativo implica mas caja que deuda."),
                "Liquidez Corriente": st.column_config.NumberColumn("Liquidez Corriente ❓", help="Capacidad de pago de corto plazo. Ideal mayor a 1.0x."),
                "Beta": st.column_config.NumberColumn("Beta ❓", help="Volatilidad contra el mercado (S&P500 = 1)."),
                "Margen Neto": st.column_config.NumberColumn("Margen Neto ❓", help="Porcentaje de ingresos que se convierte en utilidad neta."),
                "ROE": st.column_config.NumberColumn("ROE ❓", help="Rentabilidad financiera sobre el capital de los socios.")
            })
            
            df_sector = df[df['Ticker'] != ticker_objetivo]
            medianas = df_sector.median(numeric_only=True) if not df_sector.empty else None
            datos_obj = df[df['Ticker'] == ticker_objetivo].iloc[0]
            
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
                    if deb_obj > 3.0: analisis_txt += f"• ⚠️ **Riesgo de Deuda:** Deuda Neta/EBITDA en {deb_obj:.2f}x. Apalancamiento alto.\n"
                    elif deb_obj < 0: analisis_txt += f"• 🛡️ **Excelente Solvencia:** Caja neta positiva ({deb_obj:.2f}x). Mas efectivo que deuda.\n"
                    else: analisis_txt += f"• 👍 **Deuda Controlada:** Ratio Deuda Neta/EBITDA saludable en {deb_obj:.2f}x.\n"
                liq_obj = datos_obj["Liquidez Corriente"]
                if pd.notna(liq_obj):
                    if liq_obj < 1.0: analisis_txt += f"• 🚨 **Alerta de Liquidez:** Liquidez de {liq_obj:.2f}x. No cubre el corto plazo.\n"
                    else: analisis_txt += f"• 👍 **Fondeo Sólido:** Cubre compromisos inmediatos con {liq_obj:.2f}x.\n"
                st.write(analisis_txt)

            with col_inf2:
                st.markdown("**🎯 Sugerencia Estratégica del Sistema:**")
                if pd.notna(datos_obj["Deuda Neta/EBITDA"]) and datos_obj["Deuda Neta/EBITDA"] > 3.0:
                    st.error(f"🚨 **RECOMENDACIÓN: EVITAR / ALTO RIESGO**\n\n**{ticker_objetivo}** presenta endeudamiento critico.")
                elif mejor_ticker == ticker_objetivo and puntuaciones[ticker_objetivo] >= 3:
                    st.success(f"🟩 **RECOMENDACIÓN: COMPRAR / FOCO EN {ticker_objetivo}**\n\nCombina descuento con un balance muy solido.")
                elif mejor_ticker != ticker_objetivo:
                    st.warning(f"🟨 **RECOMENDACIÓN: EVALUAR ALTERNATIVAS**\n\nEl algoritmo detecto mejor perfil financiero/riesgo en **{mejor_ticker}**.")
                else:
                    st.info(f"🟪 **RECOMENDACIÓN: MANTENER / RANGOS MEDIOS**\n\nEl activo cotiza en linea con sus competidores.")

            # --- SECCIÓN 4: MODELO DCF ---
            st.markdown("---")
            st.subheader(f"🧮 Calculadora de Valor Intrínseco (DCF) para {ticker_objetivo}")
            fcf_total, shares, precio_actual = datos_obj["FCF_Total"], datos_obj["Acciones_Circulacion"], datos_obj["Precio Actual"]
            
            if pd.notna(fcf_total) and pd.notna(shares) and shares > 0 and fcf_total > 0:
                fcf_por_accion = fcf_total / shares
                col_dcf1, col_dcf2, col_dcf3 = st.columns(3)
                with col_dcf1:
                    crecimiento = st.slider("Crecimiento Anual Estimado (Años 1-5):", min_value=0, max_value=40, value=12, step=1, format="%d%%") / 100
                with col_dcf2:
                    tasa_descuento = st.slider("Tasa de Descuento Exigida (WACC):", min_value=5, max_value=25, value=10, step=1, format="%d%%") / 100
                with col_dcf3:
                    multiplo_terminal = st.slider("Múltiplo EV/EBITDA Terminal (Año 5):", min_value=3, max_value=20, value=6, step=1, format="%dx")
                
                flujos_proyectados = []
                fcf_temp = fcf_por_accion
                for ano in range(1, 6):
                    fcf_temp = fcf_temp * (1 + crecimiento)
                    flujos_proyectados.append(fcf_temp / ((1 + tasa_descuento) ** ano))
                
                valor_terminal_descontado = (fcf_temp * multipl