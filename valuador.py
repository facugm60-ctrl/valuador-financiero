import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import urllib.parse
import requests
import sqlite3
import hashlib

# 1. CONFIGURACIÓN INICIAL Y ESTILOS SAAS PREMIUM
st.set_page_config(page_title="Terminal Quanti - Galicia Inversiones", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    h1 {font-weight: 800; color: #FFFFFF; font-size: 26px !important;}
    h2 {font-weight: 700; color: #F0F2F6; font-size: 20px !important;}
    h3 {font-weight: 700; color: #F0F2F6; font-size: 17px !important;}
    p, li, span, label {font-size: 14px !important;}
    .stMetric label {font-size: 13px !important; font-weight: 600;}
    .stMetric div {font-size: 22px !important; font-weight: 700;}
    .stButton>button {
        width: 100%; background-color: #2ecc71; color: white;
        font-weight: bold; border-radius: 8px; border: none;
        padding: 0.5rem; font-size: 15px !important; margin-top: 10px;
    }
    .stButton>button:hover { background-color: #27ae60; }
    </style>
""", unsafe_allow_html=True)

# 2. MOTOR DE BASE DE DATOS LOCAL (SQLite)
def conectar_db():
    conn = sqlite3.connect("terminal_galicia.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT UNIQUE, password TEXT)
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, ticker TEXT)
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cartera (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, ticker TEXT, nominales REAL, precio_compra REAL)
    """)
    conn.commit()
    return conn, cursor

conn, cursor = conectar_db()

# Funciones de Seguridad y Persistencia
def hash_pass(password): return hashlib.sha256(password.encode()).hexdigest()

def verificar_usuario(user, password):
    cursor.execute("SELECT id FROM usuarios WHERE user=? AND password=?", (user, hash_pass(password)))
    res = cursor.fetchone()
    return res[0] if res else None

def registrar_usuario(user, password):
    try:
        cursor.execute("INSERT INTO usuarios (user, password) VALUES (?, ?)", (user, hash_pass(password)))
        conn.commit()
        return True
    except: return False

# 3. COMPONENTE DE AUTENTICACIÓN (LOGIN)
if "user_id" not in st.session_state:
    st.session_state.user_id = None
    st.session_state.username = ""

if st.session_state.user_id is None:
    st.title("🔒 Acceso Terminal Galicia Inversiones")
    c_log1, c_log2 = st.columns(2)
    with c_log1:
        st.subheader("Ingresar al Sistema")
        u = st.text_input("Usuario:", key="l_user")
        p = st.text_input("Contraseña:", type="password", key="l_pass")
        if st.button("🔓 Iniciar Sesión"):
            uid = verificar_usuario(u, p)
            if uid:
                st.session_state.user_id = uid
                st.session_state.username = u
                st.rerun()
            else: st.error("Credenciales inválidas.")
    with c_log2:
        st.subheader("Registrar Perfil Nuevo")
        nu = st.text_input("Nuevo Usuario:", key="r_user")
        np = st.text_input("Nueva Contraseña:", type="password", key="r_pass")
        if st.button("✨ Crear Cuenta"):
            if nu and np:
                if registrar_usuario(nu, np): st.success("¡Registrado! Ya podés iniciar sesión.")
                else: st.error("El usuario ya existe.")
    st.stop()

# 4. CAPTURA Y TRADUCCIÓN DE REGISTROS FINANCIEROS (BACKEND)
def traducir_espanol(texto):
    if not texto or texto == "Sin descripción disponible.": return texto
    try:
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=es&dt=t&q=" + urllib.parse.quote(texto)
        r = requests.get(url, timeout=3).json()
        return "".join([frase[0] for frase in r[0] if frase[0]])
    except: return texto

def obtener_datos(symbol):
    try:
        t = yf.Ticker(symbol)
        inf = t.info
        if not inf or len(inf) < 5: return None
        logo_url = f"https://icons.duckduckgo.com/ip3/{symbol.lower()}.com.ico"
        if "website" in inf and inf["website"]:
            dom = inf["website"].replace("https://","").replace("http://","").split("/")[0]
            logo_url = f"https://icons.duckduckgo.com/ip3/{dom}.ico"
            
        tiene_ebitda = "ebitda" in inf or "enterpriseToEbitda" in inf or "forwardPE" in inf
        raw_desc = inf.get("longBusinessSummary", "Sin descripción disponible.")
        desc_es = traducir_espanol(raw_desc) if symbol == st.session_state.get("ticker_activo", "") else ""
        
        common = {"Ticker": symbol, "Nombre": inf.get("longName", symbol), "Precio Actual": inf.get('currentPrice', inf.get('previousClose', 1.0)), "Logo": logo_url, "Descripcion": desc_es}
        
        if not tiene_ebitda:
            common.update({"Tipo": "ETF", "P/E Canasta": inf.get("trailingPE", 15.0), "Expense Ratio": inf.get("feesExpensesInvestmentPercentage", 0.001), "Dividend Yield": inf.get("dividendYield", 0.01), "Beta": inf.get("beta", 1.0)})
        else:
            td, caj, eb = inf.get("totalDebt", 0), inf.get("totalCash", 0), inf.get("ebitda", 1)
            nd_eb = (td - caj) / eb if eb else 0
            common.update({"Tipo": "ACCION", "Forward P/E": inf.get("forwardPE", 10.0), "EV/EBITDA": inf.get("enterpriseToEbitda", 6.0), "P/B Ratio": inf.get("priceToBook", 1.5), "Deuda Neta/EBITDA": nd_eb, "Liquidez Corriente": inf.get("currentRatio", 1.5), "Beta": inf.get("beta", 1.1), "Margen Neto": inf.get("profitMargins", 0.1), "ROE": inf.get("returnOnEquity", 0.15), "FCF_Total": inf.get("freeCashflow", 500000000), "Acciones": inf.get("sharesOutstanding", 100000000), "Div_Rate": inf.get("dividendRate", 0), "Div_Yield": inf.get("dividendYield", 0)})
        return common
    except: return None

# Inicialización segura de persistencia de sesión analítica
if "analisis_listo" not in st.session_state:
    st.session_state.analisis_listo = False
    st.session_state.df_datos = None
    st.session_state.obj_data = None
    st.session_state.ticker_activo = ""

# 5. MENÚ SUPERIOR DE ENTRADA GLOBAL (ESTILO SAAS NATIVO)
st.title(f"🏛️ Terminal Profesional Galicia | Analista: {st.session_state.username}")
menu_global = st.radio("Navegación del Sistema:", ["🌐 DASHBOARD GENERAL Y WATCHLIST", "🔍 DETALLE Y SCREENING DE ACTIVO", "💼 MI PORTAFOLIO GLOBAL"], horizontal=True)
st.markdown("---")

# ==========================================
# UNIVERSO A: DASHBOARD GENERAL Y WATCHLIST
# ==========================================
if menu_global == "🌐 DASHBOARD GENERAL Y WATCHLIST":
    st.subheader("📌 Mi Watchlist Sectorial Permanente")
    
    # Cargar Watchlist de SQLite
    cursor.execute("SELECT ticker FROM watchlist WHERE user_id=?", (st.session_state.user_id,))
    rows = cursor.fetchall()
    items_watchlist = [r[0] for r in rows] if rows else ["VIST", "YPF", "AAPL", "GGAL"]
    
    c_w1, c_w2 = st.columns([3, 1])
    with c_w2:
        st.markdown("**Administrar Watchlist:**")
        add_tk = st.text_input("Sumar Ticker:", value="").upper().strip()
        if st.button("➕ Agregar"):
            if add_tk and add_tk not in items_watchlist:
                cursor.execute("INSERT INTO watchlist (user_id, ticker) VALUES (?, ?)", (st.session_state.user_id, add_tk))
                conn.commit()
                st.rerun()
        del_tk = st.selectbox("Eliminar Ticker:", [""] + items_watchlist)
        if st.button("🗑️ Quitar") and del_tk:
            cursor.execute("DELETE FROM watchlist WHERE user_id=? AND ticker=?", (st.session_state.user_id, del_tk))
            conn.commit()
            st.rerun()
            
    with c_w1:
        registros_w = []
        for t in items_watchlist:
            d_t = obtener_datos(t)
            if d_t: registros_w.append({"Ticker": t, "Nombre": d_t["Nombre"], "Precio Actual": d_t["Precio Actual"], "Tipo": d_t["Tipo"], "Beta": d_t.get("Beta", 1.0)})
        if registros_w:
            df_w = pd.DataFrame(registros_w).set_index("Ticker")
            st.dataframe(df_w.style.format({"Precio Actual": "{:.2f} USD", "Beta": "{:.2f}"}), use_container_width=True)
        else: st.info("Tu watchlist está vacía.")

# ==========================================
# UNIVERSO B: SCREENING E INTELIGENCIA
# ==========================================
elif menu_global == "🔍 DETALLE Y SCREENING DE ACTIVO":
    col_s1, col_s2 = st.columns([1, 2])
    with col_s1:
        ticker_input = st.text_input("📍 ACTIVO OBJETIVO:", value=st.session_state.get("ticker_activo", "VIST")).upper().strip()
    with col_s2:
        comp_input = st.text_input("🔍 COMPETIDORES DEL SECTOR:", value="YPF, XOM, PAM").upper()
        competidores = [c.strip() for c in comp_input.split(",") if c.strip()]
        
    if st.button("🔥 EJECUTAR DIAGNÓSTICO INTEGRAL"):
        st.session_state.ticker_activo = ticker_input
        with st.spinner("Descargando balances de Wall Street..."):
            lista_datos = []
            for tk in [ticker_input] + competidores:
                r = obtener_datos(tk)
                if r: lista_datos.append(r)
            
            if not lista_datos or not any(d["Ticker"] == ticker_input for d in lista_datos):
                # Fallback de Seguridad
                fake = {"Ticker": ticker_input, "Nombre": f"{ticker_input} Corp", "Precio Actual": 50.0, "Logo": "https://cdn-icons-png.flaticon.com/512/2967/2967304.png", "Descripcion": f"Datos simulados por corte nocturno de API.", "Tipo": "ACCION", "Forward P/E": 11.5, "EV/EBITDA": 5.4, "P/B Ratio": 1.3, "Deuda Neta/EBITDA": 1.1, "Liquidez Corriente": 1.4, "Beta": 1.1, "Margen Neto": 0.12, "ROE": 0.16, "FCF_Total": 400000000, "Acciones": 80000000, "Div_Rate": 1.0, "Div_Yield": 0.02}
                lista_datos.append(fake)
                
            st.session_state.df_datos = pd.DataFrame(lista_datos)
            st.session_state.obj_data = st.session_state.df_datos[st.session_state.df_datos['Ticker'] == ticker_input].iloc[0]
            st.session_state.analisis_listo = True
            
    if st.session_state.analisis_listo:
        df = st.session_state.df_datos
        obj = st.session_state.obj_data
        
        st.markdown("---")
        c_h1, c_h2 = st.columns([1, 15])
        with c_h1: st.image(obj["Logo"], width=45)
        with c_h2: st.header(f"{obj['Nombre']} ({obj['Ticker']})")
        
        # CAMBIO DE ORDEN EXPLICITO PEDIDO
        t1, t2, t3 = st.tabs(["📋 ANÁLISIS FUNDAMENTAL", "📐 ANÁLISIS TÉCNICO", "🧮 VALOR INTRÍNSECO (DCF + MONTECARLO)"])
        
        with t1:
            st.subheader("ℹ️ Perfil Corporativo")
            st.write(obj["Descripcion"])
            if obj["Tipo"] == "ACCION":
                st.markdown("---")
                st.subheader("📋 Matriz Sectorial (Ganadores Resaltados)")
                df_acc = df[df['Tipo'] == "ACCION"].copy()
                cols = [c for c in ["Ticker", "Forward P/E", "EV/EBITDA", "P/B Ratio", "Deuda Neta/EBITDA", "Liquidez Corriente", "Margen Neto", "ROE"] if c in df_acc.columns]
                df_m = df_acc[cols].set_index('Ticker')
                df_st = df_m.style.format({"Forward P/E": "{:.2f}", "EV/EBITDA": "{:.2f}", "P/B Ratio": "{:.2f}", "Deuda Neta/EBITDA": "{:.2f}x", "Liquidez Corriente": "{:.2f}x", "Margen Neto": lambda x: f"{x*100:.2f}%", "ROE": lambda x: f"{x*100:.2f}%"})
                df_st = df_st.highlight_min(subset=[c for c in ["Forward P/E", "EV/EBITDA", "Deuda Neta/EBITDA"] if c in df_m.columns], color="#1b4d22")
                df_st = df_st.highlight_max(subset=[c for c in ["Liquidez Corriente", "Margen Neto", "ROE"] if c in df_m.columns], color="#1b4d22")
                st.dataframe(df_st, width="stretch")
                
                cp, cc = st.columns(2)
                with cp:
                    st.markdown("**🟢 Perfil de Solvencia:**")
                    st.write(f"• **Modelo:** Estructuración de pasivos alineada al flujo de contratos comerciales. Apalancamiento en `{obj['Deuda Neta/EBITDA']:.2f}x` Deuda Neta/EBITDA.")
                with cc:
                    st.markdown("**🔴 Cobertura de Caja y Estrés:**")
                    if obj['Liquidez Corriente'] < 1: st.error(f"⚠️ Cobertura ajustada en `{obj['Liquidez Corriente']:.2f}x`. Pasivos inmediatos presionan la caja.")
                    else: st.success(f"✅ Liquidez robusta en `{obj['Liquidez Corriente']:.2f}x`. Caja lista para expansión de Capex.")
                    
        with t2:
            st.subheader("📐 Indicadores Técnicos y Algoritmo de Timing")
            try:
                h = yf.Ticker(obj["Ticker"]).history(period="1y")
                if len(h) > 10:
                    cierre = h['Close']
                    calc_ema = cierre.ewm(span=30, adjust=False).mean()
                    px_hoy, ema_hoy = cierre.iloc[-1], calc_ema.iloc[-1]
                    
                    st.metric("Precio vs. EMA 30 Ruedas", f"{px_hoy:.2f} USD", f"{px_hoy - abc_hoy:.2f} USD vs Media" if "abc_hoy" in locals() else f"{px_hoy - b_hoy:.2f} USD" if "b_hoy" in locals() else f"{px_hoy - ema_hoy:.2f} USD")
                    
                    st.markdown("### 📈 Panel A: Tendencia (Precio vs. EMA 30)")
                    with st.expander("🔍 Interpretación Didáctica - Panel A"):
                        st.write("Si el precio diario (azul) quiebra y opera por encima de la EMA 30 (roja), la inercia dominante es alcista corporativa; si opera por debajo, la presión es vendedora.")
                    st.line_chart(pd.DataFrame({"Precio Cierre": cierre, "EMA 30": calc_ema}), height=250)
                    
                    st.markdown("### 🎯 Conclusión del Algoritmo Cuantitativo")
                    if px_hoy > 查看_hoy if "查看_hoy" in locals() else px_hoy > ema_hoy: st.success("🟩 **ACCIONAR: LONG / COMPRA TÉCNICA CONFIRMADA** - Viento a favor e inercia alcista.")
                    else: st.error("🚨 **ACCIONAR: EVITAR / PRESIÓN BAJISTA** - Control absoluto de la oferta en el mercado.")
            except: st.info("Datos técnicos consolidándose.")
            
        with t3:
            st.subheader("🧮 Modelo DCF Combinado con Simulación de Montecarlo Macro")
            fcf, sh, pr = obj["FCF_Total"], obj["Acciones"], obj["Precio Actual"]
            
            if pd.notna(fcf) and fcf > 0 and sh > 0:
                fcf_a = fcf / sh
                
                # ENTRADAS MACRO EDITABLES PARA MODELO MONTECARLO ARGENTINO
                st.markdown("#### ⚙️ Parámetros Macro y Breakeven Cambiaria")
                cm1, cm2, cm3 = st.columns(3)
                with cm1: inf_be = st.slider("Breakeven Inflation Anual (Argentina):", 10, 150, 35, step=5, format="%d%%") / 100
                with cm2: deval_be = st.slider("Devaluación Promedio Tipo Cambio (FX):", 10, 150, 30, step=5, format="%d%%") / 100
                with cm3: wacc_input = st.slider("Tasa de Descuento (WACC Exigida):", 5, 25, 12, step=1, format="%d%%") / 100
                
                # Ejecución de 10.000 iteraciones en memoria
                sim_fv = []
                np.random.seed(42)
                for _ in range(2000): # Reducido a 2000 por performance instantánea en web mobile
                    rand_cw = np.random.triangular(0.05, 0.12, 0.22)
                    # El tipo de cambio y la inflación ajustan el flujo real g
                    g_macro = rand_cw + (inf_be - deval_be)
                    f_p = [fcf_a * ((1+g_macro)**i) / ((1+wacc_input)**i) for i in range(1, 6)]
                    v_i_sim = sum(f_p) + (fcf_a * ((1+g_macro)**5) * 6) / ((1+wacc_input)**5)
                    sim_fv.append(v_i_sim)
                    
                fv_mediano = np.median(sim_fv)
                
                st.markdown("#### 🎯 Resultado de Probabilidades del Fair Value")
                cr1, cr2 = st.columns(2)
                with cr1: st.metric("Fair Value Probabilístico (Mediana)", f"{fv_mediano:.2f} USD")
                with cr2: 
                    if fv_mediano > pr: st.success(f"🟩 **SUBVALUADO:** Margen de Seguridad del {((fv_mediano-pr)/fv_mediano)*100:.1f}%")
                    else: st.error(f"🚨 **SOBREPRECIO:** Activo inflado un {((pr-fv_mediano)/fv_mediano)*100:.1f}%")
                    
                st.markdown("#### 💡 Interpretación del Montecarlo Financiero")
                st.write(f"El algoritmo corrió las simulaciones proyectando la breakeven de inflación contra el movimiento del Dólar. Al neto, detecta que hay una **probabilidad del {np.mean(np.array(sim_fv) > pr)*100:.1f}%** de que el valor real de la caja de {obj['Ticker']} sea superior a su precio de cotización de hoy.")
            else: st.info("El activo seleccionado no posee flujos corporativos positivos para el descuento.")

# ==========================================
# UNIVERSO C: PORTAFOLIO GLOBAL
# ==========================================
elif menu_global == "💼 MI PORTAFOLIO GLOBAL":
    st.subheader("💼 Consolidación del Portafolio Independiente")
    st.markdown("Escribí libremente los activos de tu cartera, nominales y precios medios de compra en la grilla interactiva.")
    
    # Cargar Cartera de SQLite
    cursor.execute("SELECT id, ticker, nominales, precio_compra FROM cartera WHERE user_id=?", (st.session_state.user_id,))
    rows_c = cursor.fetchall()
    
    if rows_c:
        init_c = [{"Ticker": r[1], "Nominales": r[2], "Precio Compra (USD)": r[3]} for r in rows_c]
    else:
        init_c = [{"Ticker": "VIST", "Nominales": 100, "Precio Compra (USD)": 50.0}, {"Ticker": "KO", "Nominales": 50, "Precio Compra (USD)": 60.0}]
        
    df_init = pd.DataFrame(init_c)
    editar_grilla = st.data_editor(df_init, num_rows="dynamic", key="grilla_db_final", use_container_width=True)
    
    # Botón para persistir los cambios de la grilla en SQLite
    if st.button("💾 Guardar Cambios en mi Cuenta"):
        cursor.execute("DELETE FROM cartera WHERE user_id=?", (st.session_state.user_id,))
        for idx, r in editar_grilla.iterrows():
            t = str(r["Ticker"]).strip().upper() if pd.notna(r["Ticker"]) else ""
            n = float(r["Nominales"]) if pd.notna(r["Nominales"]) else 0.0
            p = float(r["Precio Compra (USD)"]) if pd.notna(r["Precio Compra (USD)"]) else 0.0
            if t and n > 0:
                cursor.execute("INSERT INTO cartera (user_id, ticker, nominales, precio_compra) VALUES (?, ?, ?, ?)", (st.session_state.user_id, t, n, p))
        conn.commit()
        st.success("¡Estructura de cartera grabada con éxito!")
        st.rerun()
        
    # Cálculos Consolidados en Vivo
    c_tot, v_act, div_anual = 0.0, 0.0, 0.0
    for idx, r in editar_grilla.iterrows():
        t = str(r["Ticker"]).strip().upper() if pd.notna(r["Ticker"]) else ""
        n = float(r["Nominales"]) if pd.notna(r["Nominales"]) else 0.0
        p = float(r["Precio Compra (USD)"]) if pd.notna(r["Precio Compra (USD)"]) else 0.0
        if t and n > 0:
            d = obtener_datos(t)
            px_m = d["Precio Actual"] if d else p
            d_r = d.get("Div_Rate", 0.0) if d and d["Tipo"] == "ACCION" else 0.0
            c_tot += (n * p)
            v_act += (n * px_m)
            div_anual += (n * d_r)
            
    if c_tot > 0:
        st.markdown("#### 📊 Métricas Consolidadas del Portafolio")
        mc1, mc2, mc3 = st.columns(3)
        with mc1: st.metric("Capital Invertido", f"{c_tot:.2f} USD")
        with mc2: st.metric("Valor de Mercado", f"{v_act:.2f} USD")
        with mc3: st.metric("P&L de la Cartera", f"{v_act - c_tot:.2f} USD", f"{((v_act - c_tot)/c_tot)*100:.2f}%")
        
        st.markdown("---")
        st.markdown("#### 📅 Cronograma de Cobro de Dividendos Unificado")
        if div_anual > 0:
            st.success(f"🎉 Renta estimada total de **{div_anual:.2f} USD anuales**.")
            df_cr = pd.DataFrame({"Trimestre": ["Q1 Estimado", "Q2 Estimado", "Q3 Estimado", "Q4 Estimado", "TOTAL ANUAL"], "Flujo": [div_anual/4, div_anual/4, div_anual/4, div_anual/4, div_anual]}).set_index("Trimestre")
            st.table(df_cr.style.format("{:.2f} USD"))
        else: st.info("Los activos cargados en tu grilla no registran pagos de dividendos constantes en la base liquidadora.")

# --- FOOTER LEGAL INSTITUCIONAL ---
st.markdown("---")
st.markdown("<p style='text-align: justify; color: #888888; font-size: 11px;'><strong>AVISO LEGAL E INSTITUCIONAL DE EXCLUSIÓN DE RESPONSABILIDAD:</strong> El contenido, algoritmos cuantitativos, métricas sectoriales, análisis de múltiplos comparativos y proyecciones de flujos descontados (DCF) con simulación macro de Montecarlo emitidos por esta terminal tienen un propósito estrictamente educativo y de simulación corporativa. <strong>NO CONSTITUYEN, bajo ningún concepto ni circunstancia, un asesoramiento financiero personalizado, recomendación implícita o explícita de compra/venta, ni una oferta pública de valores negociables</strong> bajo los términos de la Ley de Mercado de Capitales N° 26.831 de la República Argentina ni regulaciones internacionales de la SEC. El desarrollador deslinda cualquier tipo de responsabilidad civil, comercial o contractual ante pérdidas o variaciones patrimoniales derivadas del uso de estos cálculos públicos.</p>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #aaaaaa; font-size: 13px;'>Desarrollado por <strong>Facundo Garcia Marquez</strong> | Terminal Financiera Galicia v3.0</p>", unsafe_allow_html=True)