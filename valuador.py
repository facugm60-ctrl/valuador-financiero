import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

st.set_page_config(page_title="Valuador Financiero Avanzado", layout="wide")

st.title("📊 Plataforma de Valuación de Empresas Públicas")
st.markdown("Analizá ratios financieros en tiempo real y descubrí las mejores alternativas del sector.")

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
            
        return {
            "Ticker": ticker_symbol,
            "Nombre": info.get("longName", "N/A"),
            "Precio Actual": info.get('currentPrice', info.get('previousClose', 0)),
            "P/E Trailing": info.get("trailingPE"),
            "Forward P/E": info.get("forwardPE"),
            "P/B Ratio": info.get("priceToBook"),
            "EV/EBITDA": info.get("enterpriseToEbitda"),
            "Beta": info.get("beta"),
            "Margen Neto": info.get("profitMargins"),
            "ROE": info.get("returnOnEquity")
        }
    except:
        return None

# --- FUNCIONES DE ESTILO PARA RESALTAR LOS MEJORES RATIOS ---
def resaltar_maximo(s):
    ''' Resalta el valor más alto en verde (Ideal para Márgenes y ROE) '''
    is_max = s == s.max()
    return ['background-color: rgba(46, 204, 113, 0.4); font-weight: bold' if v else '' for v in is_max]

def resaltar_minimo(s):
    ''' Resalta el valor más bajo en verde (Ideal para Múltiplos donde menor es más barato) '''
    # Ignoramos valores menores o iguales a cero para evitar distorsiones por pérdidas
    valores_validos = s[s > 0]
    if valores_validos.empty:
        return ['' for _ in s]
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
            
            # --- SECCIÓN 1: MATRIZ COMPLETA CON RESALTADOS Y TOOLTIPS EN ENCABEZADOS ---
            st.subheader("📋 Matriz Completa de Datos Financieros")
            st.caption("💡 Las celdas resaltadas en VERDE indican la empresa que lidera ese ratio específico (múltiplos más bajos o rentabilidades más altas).")
            
            df_mostrar = df.copy()
            
            # Aplicamos los estilos condicionales columna por columna
            styled_df = df_mostrar.style.apply(resaltar_minimo, subset=["P/E Trailing", "Forward P/E", "P/B Ratio", "EV/EBITDA"])\
                                      .apply(resaltar_maximo, subset=["Margen Neto", "ROE"])\
                                      .format({
                                          "Precio Actual": "{:.2f} USD",
                                          "P/E Trailing": "{:.2f}", 
                                          "Forward P/E": "{:.2f}",
                                          "P/B Ratio": "{:.2f}", 
                                          "EV/EBITDA": "{:.2f}", 
                                          "Beta": "{:.2f}",
                                          "Margen Neto": lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A",
                                          "ROE": lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A"
                                      }, na_rep="N/A")
            
            # Renombramos los encabezados inyectándoles tooltips nativos de Streamlit para las columnas
            # Al pasar el cursor sobre el símbolo (?), el usuario verá la descripción completa del ratio
            st.dataframe(styled_df, width="stretch", column_config={
                "P/E Trailing": st.column_config.NumberColumn("P/E Trailing ❓", help="Price to Earnings Histórico: Cuántas veces paga el precio actual las ganancias del último año cerrado."),
                "Forward P/E": st.column_config.NumberColumn("Forward P/E ❓", help="Price to Earnings Proyectado: Relación precio/ganancias estimadas para los próximos 12 meses. Menor implica descuento."),
                "P/B Ratio": st.column_config.NumberColumn("P/B Ratio ❓", help="Price to Book Value: Compara el valor de mercado con el valor contable en libros. Útil para ver el respaldo patrimonial."),
                "EV/EBITDA": st.column_config.NumberColumn("EV/EBITDA ❓", help="Enterprise Value / EBITDA: Mide el valor de adquisición del negocio sobre su caja operativa bruta. Es el ratio rey para comparar el sector."),
                "Beta": st.column_config.NumberColumn("Beta ❓", help="Beta de Volatilidad: Mide el riesgo de la acción frente al mercado (S&P 500 = 1). Mayor a 1 es más agresiva, menor a 1 es defensiva."),
                "Margen Neto": st.column_config.NumberColumn("Margen Neto ❓", help="Profit Margin: Qué porcentaje de los ingresos totales se convierte en ganancia neta real después de costos e impuestos."),
                "ROE": st.column_config.NumberColumn("ROE ❓", help="Return on Equity: La rentabilidad del negocio sobre el capital aportado por los accionistas. Mayor es más eficiente.")
            })
            
            # --- SECCIÓN 2: TARJETAS COMPARATIVAS ---
            df_sector = df[df['Ticker'] != ticker_objetivo]
            medianas = df_sector.median(numeric_only=True) if not df_sector.empty else None
            datos_obj = df[df['Ticker'] == ticker_objetivo].iloc[0]
            
            st.subheader(f"⚡ Resumen de {ticker_objetivo} vs Mediana de Competidores")
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            
            pe_obj, pe_med = datos_obj["Forward P/E"], medianas["Forward P/E"] if medianas is not None else None
            ev_obj, ev_med = datos_obj["EV/EBITDA"], medianas["EV/EBITDA"] if medianas is not None else None
            roe_obj, roe_med = datos_obj["ROE"], medianas["ROE"] if medianas is not None else None
            beta_obj = datos_obj["Beta"]

            if pd.notna(pe_obj) and pd.notna(pe_med) and pe_med != 0:
                kpi1.metric("Forward P/E", f"{pe_obj:.2f}x", f"{((pe_obj - pe_med) / pe_med) * 100:.1f}% vs Sector", delta_color="inverse")
            else:
                kpi1.metric("Forward P/E", f"{pe_obj:.2f}x" if pd.notna(pe_obj) else "N/A")

            if pd.notna(ev_obj) and pd.notna(ev_med) and ev_med != 0:
                kpi2.metric("EV/EBITDA", f"{ev_obj:.2f}x", f"{((ev_obj - ev_med) / ev_med) * 100:.1f}% vs Sector", delta_color="inverse")
            else:
                kpi2.metric("EV/EBITDA", f"{ev_obj:.2f}x" if pd.notna(ev_obj) else "N/A")

            if pd.notna(roe_obj) and pd.notna(roe_med):
                kpi3.metric("ROE", f"{roe_obj*100:.1f}%", f"{(roe_obj - roe_med)*100:+.1f}% vs Sector")
            else:
                kpi3.metric("ROE", f"{roe_obj*100:.1f}%" if pd.notna(roe_obj) else "N/A")
                
            kpi4.metric("Beta (Riesgo)", f"{beta_obj:.2f}" if pd.notna(beta_obj) else "N/A")

            # --- SECCIÓN 3: ALGORITMO ASESOR INTELIGENTE ---
            st.subheader("🤖 Informe del Asesor Inteligente de Inversión")
            
            puntuaciones = {}
            for index, row in df.iterrows():
                ticker = row["Ticker"]
                score = 0
                if pd.notna(row["Forward P/E"]) and medianas is not None and pd.notna(medianas["Forward P/E"]) and row["Forward P/E"] < medianas["Forward P/E"]: score += 1
                if pd.notna(row["EV/EBITDA"]):
                    if row["EV/EBITDA"] < 8: score += 1
                    if medianas is not None and pd.notna(medianas["EV/EBITDA"]) and row["EV/EBITDA"] < medianas["EV/EBITDA"]: score += 1
                if pd.notna(row["ROE"]):
                    if row["ROE"] > 0.15: score += 1
                    if medianas is not None and pd.notna(medianas["ROE"]) and row["ROE"] > medianas["ROE"]: score += 1
                puntuaciones[ticker] = score

            mejor_ticker = max(puntuaciones, key=puntuaciones.get)
            
            col_inf1, col_inf2 = st.columns(2)
            with col_inf1:
                st.markdown(f"**Análisis de Múltiplos para {ticker_objetivo}:**")
                analisis_txt = ""
                if pd.notna(pe_obj) and pd.notna(pe_med):
                    if pe_obj < pe_med:
                        analisis_txt += f"• **Valuación Atractiva:** Muestra descuento en valuación relativa frente a sus pares con un Forward P/E de {pe_obj:.2f}x.\n"
                    else:
                        analisis_txt += f"• **Prima de Riesgo:** Cotiza más cara que la mediana de sus competidores ({pe_obj:.2f}x vs {pe_med:.2f}x).\n"
                if pd.notna(roe_obj):
                    if roe_obj > 0.20:
                        analisis_txt += f"• **Alta Eficiencia:** El ROE del {roe_obj*100:.1f}% es excelente, demostrando un uso brillante del capital contable.\n"
                    else:
                        analisis_txt += f"• **Rentabilidad Moderada:** Su ROE de {roe_obj*100:.1f}% es inferior a los estándares óptimos del grupo.\n"
                st.write(analisis_txt)

            with col_inf2:
                st.markdown("**🎯 Sugerencia Estratégica del Sistema:**")
                if mejor_ticker == ticker_objetivo and puntuaciones[ticker_objetivo] >= 3:
                    st.success(f"🟩 **RECOMENDACIÓN: COMPRAR / FOCO EN {ticker_objetivo}**\n\nEl activo analizado combina múltiplos de descuento con retornos sobre el capital superiores a la media sectorial. Es la opción más sólida del grupo.")
                elif mejor_ticker != ticker_objetivo:
                    st.warning(f"🟨 **RECOMENDACIÓN: MANTENER EN OBSERVACIÓN / EVALUAR ALTERNATIVAS**\n\nEl sistema sugiere que **{ticker_objetivo}** pierde atractivo frente a sus pares en la combinación de precio/rentabilidad. \n\n**Foco Alternativo:** El algoritmo detectó un perfil financiero más equilibrado y eficiente en **{mejor_ticker}**. Sugerimos profundizar el análisis en esa empresa.")
                else:
                    st.info(f"🟪 **RECOMENDACIÓN: EVALUACIÓN MIXTA**\n\nEl activo cotiza en rangos equilibrados. No registra ventajas competitivas extremas ni desarbitrajes claros sobre el resto de las alternativas.")
        else:
            st.error("No se pudieron recopilar datos.")