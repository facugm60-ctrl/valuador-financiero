import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

st.set_page_config(page_title="Valuador Financiero Avanzado", layout="wide")

st.title("📊 Plataforma de Valuación de Empresas Públicas")
st.markdown("Analizá ratios financieros, salud de balance y descubrí las mejores alternativas en tiempo real.")

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
            
        # Extraemos variables de balance para calcular salud financiera
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
            "ROE": info.get("returnOnEquity")
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
    with st.spinner("Conectando con Wall Street y auditando balances..."):
        datos = []
        for t in todos_los_tickers:
            res = obtener_ratios(t)
            if res: datos.append(res)
            
        if datos:
            df = pd.DataFrame(datos)
            
            # --- SECCIÓN 1: MATRIZ COMPLETA DE DATOS ---
            st.subheader("📋 Matriz Completa de Datos Financieros y de Balance")
            st.caption("💡 Las celdas resaltadas en VERDE indican la empresa líder del grupo en ese indicador en particular.")
            
            df_mostrar = df.copy()
            
            # Aplicamos los estilos condicionales por columna
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
            
            # Configuramos encabezados con explicaciones flotantes detalladas
            st.dataframe(styled_df, width="stretch", column_config={
                "Forward P/E": st.column_config.NumberColumn("Forward P/E ❓", help="Mide cuántas veces pagás las ganancias estimadas del próximo año. Menor implica descuento."),
                "EV/EBITDA": st.column_config.NumberColumn("EV/EBITDA ❓", help="Mide el valor de adquisición del negocio sobre su caja operativa bruta. Clave para comparar el sector."),
                "P/B Ratio": st.column_config.NumberColumn("P/B Ratio ❓", help="Precio / Valor en Libros: Compara la valuación de mercado con el patrimonio neto contable."),
                "Deuda Neta/EBITDA": st.column_config.NumberColumn("Deuda Neta/EBITDA ❓", help="Ratio de Apalancamiento: Indica cuántos años de EBITDA requiere la empresa para cancelar su deuda neta. Ideal menor a 2.5x. Si es negativo significa que tiene más caja que deuda."),
                "Liquidez Corriente": st.column_config.NumberColumn("Liquidez Corriente ❓", help="Mide la capacidad de pagar deudas de corto plazo (Activo Corriente / Pasivo Corriente). Debe ser mayor a 1.0x para estar tranquilos."),
                "Beta": st.column_config.NumberColumn("Beta ❓", help="Volatilidad contra el S&P 500 (Mercado = 1). Mayor a 1 es agresiva; menor a 1 es defensiva."),
                "Margen Neto": st.column_config.NumberColumn("Margen Neto ❓", help="Qué porcentaje de los ingresos totales se convierte en ganancia neta real."),
                "ROE": st.column_config.NumberColumn("ROE ❓", help="Rentabilidad sobre el capital aportado por los socios. Mide la eficiencia del management.")
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
                
                # Reglas de Valoración Relativa
                if pd.notna(row["Forward P/E"]) and medianas is not None and row["Forward P/E"] < medianas["Forward P/E"]: score += 1
                if pd.notna(row["EV/EBITDA"]) and medianas is not None and row["EV/EBITDA"] < medianas["EV/EBITDA"]: score += 1
                if pd.notna(row["ROE"]) and medianas is not None and row["ROE"] > medianas["ROE"]: score += 1
                
                # NUEVAS: Reglas Estrictas de Seguridad de Balance (Evitar quiebras)
                if pd.notna(row["Deuda Neta/EBITDA"]):
                    if row["Deuda Neta/EBITDA"] > 3.0: score -= 2  # Castigo duro por apalancamiento peligroso
                    elif row["Deuda Neta/EBITDA"] < 1.5: score += 1 # Premio por balance limpio
                if pd.notna(row["Liquidez Corriente"]) and row["Liquidez Corriente"] >= 1.2: score += 1
                
                puntuaciones[ticker] = score

            mejor_ticker = max(puntuaciones, key=puntuaciones.get)
            
            col_inf1, col_inf2 = st.columns(2)
            with col_inf1:
                st.markdown(f"**Auditoría de Balance y Riesgo para {ticker_objetivo}:**")
                analisis_txt = ""
                
                # Diagnóstico de Apalancamiento
                deb_obj = datos_obj["Deuda Neta/EBITDA"]
                if pd.notna(deb_obj):
                    if deb_obj > 3.0:
                        analisis_txt += f"• ⚠️ **Riesgo de Deuda:** El ratio Deuda Neta/EBITDA es de {deb_obj:.2f}x. Es un nivel de apalancamiento peligroso que puede comprometer la solvencia.\n"
                    elif deb_obj < 0:
                        analisis_txt += f"• 🛡️ **Excelente Solvencia:** Su Deuda Neta es negativa ({deb_obj:.2f}x). Significa que la empresa posee una 'caja neta' formidable, teniendo más dinero en efectivo que pasivos financieros totales.\n"
                    else:
                        analisis_txt += f"• 👍 **Deuda Controlada:** El ratio Deuda Neta/EBITDA se encuentra en un rango muy saludable de {deb_obj:.2f}x.\n"
                
                # Diagnóstico de Liquidez
                liq_obj = datos_obj["Liquidez Corriente"]
                if pd.notna(liq_obj):
                    if liq_obj < 1.0:
                        analisis_txt += f"• 🚨 **Alerta de Liquidez:** Registra una liquidez de {liq_obj:.2f}x. No cubre sus deudas de corto plazo con sus activos corrientes. Estrés financiero potencial.\n"
                    else:
                        analisis_txt += f"• • **Fondeo de Corto Plazo:** Cubre perfectamente sus compromisos inmediatos con una liquidez corriente de {liq_obj:.2f}x.\n"
                        
                st.write(analisis_txt)

            with col_inf2:
                st.markdown("**🎯 Sugerencia Estratégica del Sistema:**")
                
                # Verificamos si el activo objetivo tiene alarmas graves de balance
                if pd.notna(datos_obj["Deuda Neta/EBITDA"]) and datos_obj["Deuda Neta/EBITDA"] > 3.0:
                    st.error(f"🚨 **RECOMENDACIÓN: EVITAR / ALTO RIESGO**\n\nA pesar de los múltiplos de precio, **{ticker_objetivo}** presenta un nivel de endeudamiento crítico que activa el protocolo de exclusión por riesgo de balance.")
                elif mejor_ticker == ticker_objetivo and puntuaciones[ticker_objetivo] >= 3:
                    st.success(f"🟩 **RECOMENDACIÓN: COMPRAR / FOCO EN {ticker_objetivo}**\n\nEl activo pasa las auditorías de riesgo. Combina múltiplos de descuento con un balance limpio y sólido.")
                elif mejor_ticker != ticker_objetivo:
                    st.warning(f"🟨 **RECOMENDACIÓN: EVALUAR ALTERNATIVAS**\n\nEl algoritmo detectó un perfil financiero/riesgo más óptimo y equilibrado en **{mejor_ticker}**. Sugerimos trasladar el foco del análisis a este competidor.")
                else:
                    st.info(f"🟪 **RECOMENDACIÓN: MANTENER / RANGOS MEDIOS**\n\nEl activo cotiza en línea con sus competidores y sus ratios de deuda se mantienen estables dentro de los parámetros permitidos.")
        else:
            st.error("No se pudieron recopilar datos.")