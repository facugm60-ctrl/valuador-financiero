import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.figure_factory as ff
import sqlite3
import hashlib
import urllib.parse
import requests

# 1. ESTILOS Y FUENTE MONTSERRAT
st.set_page_config(page_title="Terminal Quanti Pro", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Montserrat', sans-serif !important;
    }
    
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    h1 {font-weight: 800; color: #FFFFFF; font-size: 32px !important;}
    h2 {font-weight: 700; color: #F0F2F6; font-size: 22px !important;}
    
    .stMetric label {font-size: 14px !important; font-weight: 600;}
    .stMetric div {font-size: 26px !important; font-weight: 700;}
    
    .stButton>button {
        width: 100%; background-color: #2ecc71; color: white;
        font-weight: bold; border-radius: 8px; border: none;
        padding: 0.6rem; font-size: 16px !important;
    }
    </style>
""", unsafe_allow_html=True)

# 2. BASE DE DATOS
def conectar_db():
    conn = sqlite3.connect("terminal_privada.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT UNIQUE, password TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS watchlist (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, ticker TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS cartera (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, ticker TEXT, nominales REAL, precio_compra REAL)")
    conn.commit()
    return conn, c

conn, cursor = conectar_db()

def hash_pass(password): return hashlib.sha256(password.encode()).hexdigest()

# 3. LOGIN CON SOPORTE PARA GUARDAR CONTRASEÑA
if "user_id" not in st.session_state:
    st.session_state.user_id = None

if st.session_state.user_id is None:
    st.title("🔐 Acceso Terminal Cuantitativa")
    col1, col2 = st.columns(2)
    
    with col1:
        with st.form("login_form"):
            st.subheader("Iniciar Sesión")
            u = st.text_input("Usuario", autocomplete="username")
            p = st.text_input("Contraseña", type="password", autocomplete="current-password")
            submit = st.form_submit_button("Entrar")
            if submit:
                cursor.execute("SELECT id FROM usuarios WHERE user=? AND password=?", (u, hash_pass(p)))
                res = cursor.fetchone()
                if res:
                    st.session_state.user_id = res[0]
                    st.session_state.username = u
                    st.rerun()
                else: st.error("Error de acceso.")
    
    with col2:
        with st.form("reg_form"):
            st.subheader("Nuevo Perfil")
            nu = st.text_input("Nuevo Usuario")
            np = st.text_input("Nueva Contraseña", type="password")
            reg_submit = st.form_submit_button("Crear Cuenta")
            if reg_submit and nu and np:
                try:
                    cursor.execute("INSERT INTO usuarios (user, password) VALUES (?, ?)", (nu, hash_pass(np)))
                    conn.commit()
                    st.success("¡Cuenta creada! Ya podés loguearte a la izquierda.")
                except: st.error("El usuario ya existe.")
    st.stop()

# 4. BACKEND ANALÍTICO
def traducir_espanol(texto):
    if not texto: return "Sin descripción."
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
        logo = f"https://icons.duckduckgo.com/ip3/{symbol.lower()}.com.ico"
        desc = traducir_espanol(inf.get("longBusinessSummary", "")) if symbol == st.session_state.get("t_act", "") else ""
        
        common = {"Ticker": symbol, "Nombre": inf.get("longName", symbol), "Precio Actual": inf.get('currentPrice', inf.get('previousClose', 1.0)), "Logo": logo, "Descripcion": desc}
        
        if "ebitda" in inf or "forwardPE" in inf:
            td, caj, eb = inf.get("totalDebt", 0), inf.get("totalCash", 0), inf.get("ebitda", 1)
            common.update({"Tipo": "ACCION", "Forward P/E": inf.get("forwardPE", 12), "EV/EBITDA": inf.get("enterpriseToEbitda", 7), "P/B Ratio": inf.get("priceToBook", 1.5), "Deuda Neta/EBITDA": (td-caj)/eb if eb else 0, "Liquidez Corriente": inf.get("currentRatio", 1.2), "Beta": inf.get("beta", 1), "Margen Neto": inf.get("profitMargins", 0.1), "ROE": inf.get("returnOnEquity", 0.1), "FCF_Total": inf.get("freeCashflow", 1e8), "Acciones": inf.get("sharesOutstanding", 1e7), "Div_Rate": inf.get("dividendRate", 0)})
        else:
            common.update({"Tipo": "ETF", "P/E Canasta": inf.get("trailingPE", 15), "Expense Ratio": inf.get("feesExpensesInvestmentPercentage", 0.001), "Dividend Yield": inf.get("dividendYield", 0.02), "Beta": inf.get("beta", 1)})
        return common
    except: return None

# 5. INTERFAZ PRINCIPAL
st.title(f"📈 Terminal Quanti Pro | Analista: {st.session_state.username}")
menu = st.radio("Sección:", ["📊 DASHBOARD", "🔍 SCREENING", "💼 CARTERA"], horizontal=True)

# --- DASHBOARD / WATCHLIST ---
if menu == "📊 DASHBOARD":
    st.subheader("📌 Mi Watchlist")
    cursor.execute("SELECT ticker FROM watchlist WHERE user_id=?", (st.session_state.user_id,))
    items = [r[0] for r in cursor.fetchall()]
    
    c1, c2 = st.columns([4, 1])
    with c2:
        nuevo = st.text_input("Agregar Ticker:").upper()
        if st.button("➕") and nuevo:
            cursor.execute("INSERT INTO watchlist (user_id, ticker) VALUES (?,?)", (st.session_state.user_id, nuevo))
            conn.commit()
            st.rerun()
    with c1:
        if items:
            df_w = pd.DataFrame([obtener_datos(t) for t in items if obtener_datos(t)])
            st.dataframe(df_w[["Ticker", "Nombre", "Precio Actual", "Tipo"]].set_index("Ticker"), use_container_width=True)

# --- SCREENING ---
elif menu == "🔍 SCREENING":
    c_s1, c_s2 = st.columns([1,2])
    t_obj = c_s1.text_input("Activo Principal:", value="VIST").upper()
    t_comp = c_s2.text_input("Competidores (coma):", value="YPF,XOM,PAM").upper()
    
    if st.button("🚀 ANALIZAR"):
        st.session_state.t_act = t_obj
        st.session_state.res = [obtener_datos(t.strip()) for t in ([t_obj] + t_comp.split(",")) if obtener_datos(t.strip())]
        st.session_state.analisis_ok = True

    if st.session_state.get("analisis_ok"):
        df = pd.DataFrame(st.session_state.res)
        obj = df[df['Ticker'] == st.session_state.t_act].iloc[0]
        
        st.markdown(f"### <img src='{obj['Logo']}' width='30'> {obj['Nombre']} ({obj['Ticker']})", unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["📝 FUNDAMENTAL", "📈 TÉCNICO", "🧮 VALUACIÓN MONTECARLO"])
        
        with tab1:
            st.write(obj["Descripcion"])
            df_m = df[df['Tipo'] == "ACCION"].copy().set_index("Ticker")
            if not df_m.empty:
                cols = ["Forward P/E", "EV/EBITDA", "Deuda Neta/EBITDA", "ROE", "Margen Neto"]
                st.dataframe(df_m[cols].style.highlight_min(subset=cols[:3], color="#1b4d22").highlight_max(subset=cols[3:], color="#1b4d22"), use_container_width=True)

        with tab2:
            h = yf.Ticker(obj["Ticker"]).history(period="1y")
            # Panel A
            cierre = h['Close']
            ema = cierre.ewm(span=30).mean()
            fig_a = go.Figure()
            fig_a.add_trace(go.Scatter(x=h.index, y=cierre, name="Precio", line=dict(color='#3498db')))
            fig_a.add_trace(go.Scatter(x=h.index, y=ema, name="EMA 30", line=dict(color='#e74c3c')))
            fig_a.update_layout(title="Panel A: Precio vs Media Móvil", height=300, template="plotly_dark", margin=dict(l=20,r=20,t=40,b=20))
            st.plotly_chart(fig_a, use_container_width=True)
            
            # Panel B (DMI/ADX)
            high, low = h['High'], h['Low']
            up, down = high.diff(), -low.diff()
            tr = pd.concat([high-low, abs(high-cierre.shift(1)), abs(low-cierre.shift(1))], axis=1).max(axis=1).ewm(span=14).mean()
            p_di = 100 * (up.clip(lower=0).ewm(span=14).mean() / tr)
            m_di = 100 * (down.clip(lower=0).ewm(span=14).mean() / tr)
            adx = 100 * (abs(p_di - m_di) / (p_di + m_di)).ewm(span=14).mean()
            
            fig_b = go.Figure()
            fig_b.add_trace(go.Scatter(x=h.index, y=p_di, name="+DI", line=dict(color='#2ecc71')))
            fig_b.add_trace(go.Scatter(x=h.index, y=m_di, name="-DI", line=dict(color='#e74c3c')))
            fig_b.add_trace(go.Scatter(x=h.index, y=adx, name="ADX", line=dict(color='#f1c40f', dash='dot')))
            fig_b.update_layout(title="Panel B: Oscilador Direccional (DMI/ADX)", height=250, template="plotly_dark", margin=dict(l=20,r=20,t=40,b=20))
            st.plotly_chart(fig_b, use_container_width=True)
            
            if cierre.iloc[-1] > ema.iloc[-1] and p_di.iloc[-1] > m_di.iloc[-1]: st.success("Recomendación: LONG (Tendencia y Flujo Alcista)")
            else: st.error("Recomendación: CAUTELA / BAJISTA")

        with tab3:
            st.subheader("Simulación de Montecarlo (Ajuste Macro Argentina)")
            c1, c2, c3 = st.columns(3)
            inf = c1.slider("Inflación Implícita Anual", 10, 150, 40) / 100
            dev = c2.slider("Devaluación FX Anual", 10, 150, 35) / 100
            wacc = c3.slider("Tasa WACC", 5, 25, 12) / 100
            
            fcf_p = obj["FCF_Total"] / obj["Acciones"]
            simulaciones = []
            for _ in range(1500):
                g_op = np.random.triangular(0.02, 0.1, 0.18)
                g_final = (1 + g_op) * (1 + inf) / (1 + dev) - 1
                v = sum([fcf_p * ((1+g_final)**i) / ((1+wacc)**i) for i in range(1,6)]) + (fcf_p * ((1+g_final)**5) * 6) / ((1+wacc)**5)
                simulaciones.append(v)
            
            # Gráfico de Campana
            fig_mc = ff.create_distplot([simulaciones], ["Valor Intrínseco"], bin_size=1, show_hist=False, colors=['#2ecc71'])
            fig_mc.add_vline(x=obj["Precio Actual"], line_dash="dash", line_color="white", annotation_text="Precio Hoy")
            fig_mc.update_layout(title="Distribución de Probabilidades del Valor Justo", template="plotly_dark", height=400)
            st.plotly_chart(fig_mc, use_container_width=True)
            st.write(f"Mediana del Fair Value: **USD {np.median(simulaciones):.2f}**")

# --- CARTERA ---
elif menu == "💼 CARTERA":
    st.subheader("Gestión de Portafolio")
    cursor.execute("SELECT ticker, nominales, precio_compra FROM cartera WHERE user_id=?", (st.session_state.user_id,))
    df_c = pd.DataFrame(cursor.fetchall(), columns=["Ticker", "Nominales", "Precio Compra"])
    
    edit = st.data_editor(df_c, num_rows="dynamic", use_container_width=True)
    if st.button("Guardar Cartera"):
        cursor.execute("DELETE FROM cartera WHERE user_id=?", (st.session_state.user_id,))
        for _, r in edit.iterrows():
            if r["Ticker"]: cursor.execute("INSERT INTO cartera (user_id, ticker, nominales, precio_compra) VALUES (?,?,?,?)", (st.session_state.user_id, r["Ticker"].upper(), r["Nominales"], r["Precio Compra"]))
        conn.commit()
        st.success("Guardado.")
        st.rerun()

st.markdown("---")
st.markdown("<p style='text-align: center; color: #888; font-size: 11px;'>Terminal Quanti Pro - Montserrat Font Edition. No constituye asesoramiento financiero.</p>", unsafe_allow_html=True)
