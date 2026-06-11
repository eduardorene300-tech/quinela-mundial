import streamlit as st
import psycopg2
import os
import hashlib
from datetime import datetime, date, timedelta
from contextlib import contextmanager

# ─── Configuración de página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="⚽ Quiniela Mundial 2026",
    page_icon="⚽",
    layout="wide"
)

# ─── CSS minimalista ───────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stButton button { width: 100%; }
    div[data-testid="column"] { padding: 0 4px; }
    .partido-row { border-bottom: 1px solid #eee; padding: 8px 0; }
</style>
""", unsafe_allow_html=True)

# ─── DATOS COMPLETOS ───────────────────────────────────────────────────────────
CALENDARIO_GRUPOS = [
    ("Mexico", "Sudafrica", "Grupo A", "2026-06-11", "15:00"),
    ("Corea del Sur", "Republica Checa", "Grupo A", "2026-06-11", "18:00"),
    ("Sudafrica", "Republica Checa", "Grupo A", "2026-06-18", "14:00"),
    ("Mexico", "Corea del Sur", "Grupo A", "2026-06-18", "20:00"),
    ("Mexico", "Republica Checa", "Grupo A", "2026-06-24", "16:00"),
    ("Sudafrica", "Corea del Sur", "Grupo A", "2026-06-24", "19:00"),
    ("Canada", "Bosnia y Herzegovina", "Grupo B", "2026-06-12", "13:00"),
    ("Qatar", "Suiza", "Grupo B", "2026-06-12", "16:00"),
    ("Bosnia y Herzegovina", "Suiza", "Grupo B", "2026-06-18", "18:00"),
    ("Canada", "Qatar", "Grupo B", "2026-06-18", "20:00"),
    ("Canada", "Suiza", "Grupo B", "2026-06-24", "14:00"),
    ("Bosnia y Herzegovina", "Qatar", "Grupo B", "2026-06-24", "17:00"),
    ("Brasil", "Haiti", "Grupo C", "2026-06-12", "12:00"),
    ("Marruecos", "Escocia", "Grupo C", "2026-06-12", "15:00"),
    ("Brasil", "Marruecos", "Grupo C", "2026-06-19", "14:00"),
    ("Escocia", "Haiti", "Grupo C", "2026-06-19", "17:00"),
    ("Brasil", "Escocia", "Grupo C", "2026-06-25", "13:00"),
    ("Haiti", "Marruecos", "Grupo C", "2026-06-25", "16:00"),
    ("Estados Unidos", "Paraguay", "Grupo D", "2026-06-13", "15:00"),
    ("Australia", "Turquia", "Grupo D", "2026-06-13", "18:00"),
    ("Estados Unidos", "Australia", "Grupo D", "2026-06-19", "14:00"),
    ("Paraguay", "Turquia", "Grupo D", "2026-06-19", "20:00"),
    ("Estados Unidos", "Turquia", "Grupo D", "2026-06-25", "16:00"),
    ("Australia", "Paraguay", "Grupo D", "2026-06-25", "19:00"),
    ("Alemania", "Costa de Marfil", "Grupo E", "2026-06-13", "13:00"),
    ("Ecuador", "Curazao", "Grupo E", "2026-06-13", "16:00"),
    ("Alemania", "Ecuador", "Grupo E", "2026-06-20", "15:00"),
    ("Costa de Marfil", "Curazao", "Grupo E", "2026-06-20", "18:00"),
    ("Alemania", "Curazao", "Grupo E", "2026-06-26", "14:00"),
    ("Ecuador", "Costa de Marfil", "Grupo E", "2026-06-26", "17:00"),
    ("Japon", "Peru", "Grupo F", "2026-06-14", "12:00"),
    ("Arabia Saudi", "Rumania", "Grupo F", "2026-06-14", "15:00"),
    ("Japon", "Arabia Saudi", "Grupo F", "2026-06-20", "14:00"),
    ("Peru", "Rumania", "Grupo F", "2026-06-20", "17:00"),
    ("Japon", "Rumania", "Grupo F", "2026-06-26", "13:00"),
    ("Peru", "Arabia Saudi", "Grupo F", "2026-06-26", "16:00"),
    ("Belgica", "Nueva Zelanda", "Grupo G", "2026-06-14", "13:00"),
    ("Iran", "Egipto", "Grupo G", "2026-06-14", "16:00"),
    ("Belgica", "Iran", "Grupo G", "2026-06-21", "15:00"),
    ("Egipto", "Nueva Zelanda", "Grupo G", "2026-06-21", "18:00"),
    ("Belgica", "Egipto", "Grupo G", "2026-06-27", "14:00"),
    ("Iran", "Nueva Zelanda", "Grupo G", "2026-06-27", "17:00"),
    ("Espana", "Cabo Verde", "Grupo H", "2026-06-15", "12:00"),
    ("Uruguay", "Arabia Saudi", "Grupo H", "2026-06-15", "15:00"),
    ("Espana", "Uruguay", "Grupo H", "2026-06-21", "14:00"),
    ("Cabo Verde", "Arabia Saudi", "Grupo H", "2026-06-21", "17:00"),
    ("Espana", "Arabia Saudi", "Grupo H", "2026-06-27", "13:00"),
    ("Uruguay", "Cabo Verde", "Grupo H", "2026-06-27", "16:00"),
    ("Francia", "Irak", "Grupo I", "2026-06-15", "13:00"),
    ("Senegal", "Noruega", "Grupo I", "2026-06-15", "16:00"),
    ("Francia", "Senegal", "Grupo I", "2026-06-22", "15:00"),
    ("Noruega", "Irak", "Grupo I", "2026-06-22", "18:00"),
    ("Francia", "Noruega", "Grupo I", "2026-06-27", "14:00"),
    ("Irak", "Senegal", "Grupo I", "2026-06-27", "17:00"),
    ("Argentina", "Argelia", "Grupo J", "2026-06-16", "15:00"),
    ("Austria", "Chile", "Grupo J", "2026-06-16", "18:00"),
    ("Argentina", "Austria", "Grupo J", "2026-06-22", "14:00"),
    ("Chile", "Argelia", "Grupo J", "2026-06-22", "17:00"),
    ("Argentina", "Chile", "Grupo J", "2026-06-28", "16:00"),
    ("Argelia", "Austria", "Grupo J", "2026-06-28", "19:00"),
    ("Portugal", "Jamaica", "Grupo K", "2026-06-16", "13:00"),
    ("Colombia", "Uzbekistan", "Grupo K", "2026-06-16", "16:00"),
    ("Portugal", "Colombia", "Grupo K", "2026-06-23", "15:00"),
    ("Jamaica", "Uzbekistan", "Grupo K", "2026-06-23", "18:00"),
    ("Portugal", "Uzbekistan", "Grupo K", "2026-06-28", "14:00"),
    ("Colombia", "Jamaica", "Grupo K", "2026-06-28", "17:00"),
    ("Inglaterra", "Ghana", "Grupo L", "2026-06-17", "15:00"),
    ("Croacia", "Panama", "Grupo L", "2026-06-17", "18:00"),
    ("Inglaterra", "Croacia", "Grupo L", "2026-06-23", "14:00"),
    ("Panama", "Ghana", "Grupo L", "2026-06-23", "17:00"),
    ("Inglaterra", "Panama", "Grupo L", "2026-06-28", "13:00"),
    ("Ghana", "Croacia", "Grupo L", "2026-06-28", "16:00"),
]

FASES_ELIMINATORIAS = ["Octavos", "Cuartos", "Semifinal", "Final"]

# ─── FUNCIÓN DE CONEXIÓN ÚNICA (CORREGIDA) ─────────────────────────────────────
# NO cerramos la conexión global, la mantenemos viva
@st.cache_resource
def get_db_connection():
    """Retorna una conexión única que se reutiliza"""
    return psycopg2.connect(os.environ["DATABASE_URL"])

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ─── CREAR TABLAS (UNA SOLA VEZ) ───────────────────────────────────────────────
@st.cache_resource
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Tabla jugadores
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jugadores (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(64) NOT NULL,
            es_admin BOOLEAN DEFAULT FALSE,
            registrado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabla partidos
    cur.execute("""
        CREATE TABLE IF NOT EXISTS partidos (
            id SERIAL PRIMARY KEY,
            equipo_local VARCHAR(60) NOT NULL,
            equipo_visitante VARCHAR(60) NOT NULL,
            goles_local INTEGER DEFAULT NULL,
            goles_visitante INTEGER DEFAULT NULL,
            fase VARCHAR(30) NOT NULL,
            fecha DATE NOT NULL,
            hora VARCHAR(10) DEFAULT '15:00'
        )
    """)
    
    # Tabla predicciones
    cur.execute("""
        CREATE TABLE IF NOT EXISTS predicciones (
            id SERIAL PRIMARY KEY,
            jugador_id INTEGER REFERENCES jugadores(id),
            partido_id INTEGER REFERENCES partidos(id),
            pred_local INTEGER NOT NULL,
            pred_visitante INTEGER NOT NULL,
            puntos INTEGER DEFAULT 0,
            UNIQUE(jugador_id, partido_id)
        )
    """)
    
    # Crear admin por defecto
    admin_pass = hash_password("admin123")
    cur.execute("""
        INSERT INTO jugadores (nombre, email, password_hash, es_admin)
        VALUES ('Admin', 'admin@quiniela.com', %s, TRUE)
        ON CONFLICT (email) DO NOTHING
    """, (admin_pass,))
    
    # Precargar partidos
    cur.execute("SELECT COUNT(*) FROM partidos")
    if cur.fetchone()[0] == 0:
        for local, visitante, fase, fecha_str, hora in CALENDARIO_GRUPOS:
            cur.execute("""
                INSERT INTO partidos (equipo_local, equipo_visitante, fase, fecha, hora)
                VALUES (%s, %s, %s, %s, %s)
            """, (local, visitante, fase, fecha_str, hora))
    
    conn.commit()
    # NO cerramos la conexión aquí, la mantenemos viva
    return True

# ─── FUNCIONES DE CONSULTA (NO CIERRAN CONEXIÓN) ───────────────────────────────
@st.cache_data(ttl=300)
def get_todos_jugadores():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre FROM jugadores ORDER BY nombre")
    rows = cur.fetchall()
    return rows

@st.cache_data(ttl=300)
def get_partidos():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, equipo_local, equipo_visitante, goles_local, goles_visitante, fase, fecha, hora FROM partidos ORDER BY fecha, hora")
    rows = cur.fetchall()
    return rows

@st.cache_data(ttl=300)
def get_tabla_posiciones():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT j.nombre, COALESCE(SUM(pr.puntos), 0) as total,
               COUNT(CASE WHEN pr.puntos = 3 THEN 1 END) as exactos,
               COUNT(CASE WHEN pr.puntos = 1 THEN 1 END) as ganadores
        FROM jugadores j
        LEFT JOIN predicciones pr ON j.id = pr.jugador_id
        GROUP BY j.id, j.nombre
        ORDER BY total DESC, exactos DESC
    """)
    rows = cur.fetchall()
    return rows

@st.cache_data(ttl=300)
def get_mis_predicciones(jugador_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.id, p.equipo_local, p.equipo_visitante, p.goles_local, p.goles_visitante,
               p.fase, p.fecha, p.hora, pr.pred_local, pr.pred_visitante, pr.puntos
        FROM predicciones pr
        JOIN partidos p ON pr.partido_id = p.id
        WHERE pr.jugador_id = %s
        ORDER BY p.fecha, p.hora
    """, (jugador_id,))
    rows = cur.fetchall()
    return rows

def get_prediccion(jugador_id, partido_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT pred_local, pred_visitante FROM predicciones WHERE jugador_id=%s AND partido_id=%s",
                (jugador_id, partido_id))
    row = cur.fetchone()
    return row

# ─── FUNCIONES DE ESCRITURA (CON TRANSACCIONES) ────────────────────────────────
def registrar_usuario(nombre, email, password):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO jugadores (nombre, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
            (nombre, email, hash_password(password))
        )
        uid = cur.fetchone()[0]
        conn.commit()
        st.cache_data.clear()
        return uid, None
    except Exception as e:
        return None, str(e)

def login(email, password):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, nombre, es_admin FROM jugadores WHERE email=%s AND password_hash=%s",
        (email, hash_password(password))
    )
    row = cur.fetchone()
    return row

def guardar_prediccion(jugador_id, partido_id, pred_local, pred_visitante):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Verificar estado del partido
        cur.execute("SELECT fecha, hora, goles_local FROM partidos WHERE id = %s", (partido_id,))
        fecha, hora, goles = cur.fetchone()
        
        if goles is not None:
            return False, "Partido ya finalizado"
        
        ahora = datetime.now()
        fecha_hora = datetime.combine(fecha, datetime.strptime(hora, "%H:%M").time())
        if fecha_hora <= ahora:
            return False, "El partido ya comenzó"
        
        cur.execute("""
            INSERT INTO predicciones (jugador_id, partido_id, pred_local, pred_visitante)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (jugador_id, partido_id)
            DO UPDATE SET pred_local=EXCLUDED.pred_local, pred_visitante=EXCLUDED.pred_visitante, puntos=0
        """, (jugador_id, partido_id, pred_local, pred_visitante))
        
        conn.commit()
        st.cache_data.clear()
        return True, "Predicción guardada"
    except Exception as e:
        return False, str(e)

def set_resultado(partido_id, goles_local, goles_visitante):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("UPDATE partidos SET goles_local=%s, goles_visitante=%s WHERE id=%s",
                (goles_local, goles_visitante, partido_id))
    
    cur.execute("SELECT jugador_id, pred_local, pred_visitante FROM predicciones WHERE partido_id=%s", (partido_id,))
    for jugador_id, pl, pv in cur.fetchall():
        if pl == goles_local and pv == goles_visitante:
            puntos = 3
        elif (pl > pv and goles_local > goles_visitante) or (pl < pv and goles_local < goles_visitante) or (pl == pv and goles_local == goles_visitante):
            puntos = 1
        else:
            puntos = 0
        cur.execute("UPDATE predicciones SET puntos=%s WHERE partido_id=%s AND jugador_id=%s", 
                   (puntos, partido_id, jugador_id))
    
    conn.commit()
    st.cache_data.clear()

def add_partido(local, visitante, fase, fecha, hora):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO partidos (equipo_local, equipo_visitante, fase, fecha, hora) VALUES (%s, %s, %s, %s, %s)",
        (local, visitante, fase, fecha, hora)
    )
    conn.commit()
    st.cache_data.clear()

# ─── INICIALIZAR ───────────────────────────────────────────────────────────────
try:
    init_db()
except Exception as e:
    st.error(f"Error de conexión: {e}")
    st.stop()

# ─── ESTADO DE SESIÓN ──────────────────────────────────────────────────────────
if "user_id" not in st.session_state:
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.is_admin = False

# ─── HEADER ────────────────────────────────────────────────────────────────────
st.title("⚽ Quiniela Mundial 2026")
st.caption("11 Jun - 19 Jul 2026 | USA · México · Canadá")

# ─── LOGIN / REGISTRO ──────────────────────────────────────────────────────────
if not st.session_state.user_id:
    with st.sidebar:
        st.subheader("🔐 Acceso")
        tab1, tab2 = st.tabs(["Login", "Registro"])
        
        with tab1:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Contraseña", type="password", key="login_pass")
            if st.button("Entrar", use_container_width=True):
                user = login(email, password)
                if user:
                    st.session_state.user_id = user[0]
                    st.session_state.user_name = user[1]
                    st.session_state.is_admin = user[2]
                    st.rerun()
                else:
                    st.error("Email o contraseña incorrectos")
        
        with tab2:
            nombre = st.text_input("Nombre", key="reg_nombre")
            email = st.text_input("Email", key="reg_email")
            pwd = st.text_input("Contraseña", type="password", key="reg_pass")
            pwd2 = st.text_input("Repetir", type="password", key="reg_pass2")
            if st.button("Registrarse", use_container_width=True):
                if not nombre or not email or not pwd:
                    st.error("Completa todos los campos")
                elif pwd != pwd2:
                    st.error("Las contraseñas no coinciden")
                elif len(pwd) < 4:
                    st.error("Mínimo 4 caracteres")
                else:
                    uid, err = registrar_usuario(nombre, email, pwd)
                    if uid:
                        st.success("¡Registrado! Ahora inicia sesión")
                    else:
                        st.error("Email o nombre ya existe" if "unique" in str(err).lower() else f"Error: {err}")
    st.stop()

# ─── SIDEBAR CON MENÚ ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"**👤 {st.session_state.user_name}**")
    if st.button("🚪 Cerrar sesión", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    
    st.divider()
    
    menu = st.radio("📋 Menú", 
                   ["🏆 Tabla", "🎯 Predecir", "📊 Mis resultados", "📅 Calendario"],
                   label_visibility="collapsed")
    
    if st.session_state.is_admin:
        st.divider()
        st.markdown("**🔧 Admin**")
        admin_menu = st.radio("", ["⚽ Resultados", "➕ Partido"], label_visibility="collapsed")

# ════════════════════════════════════════════════════════════════════════════════
# 1. TABLA DE POSICIONES
if menu == "🏆 Tabla":
    st.header("🏆 Clasificación")
    tabla = get_tabla_posiciones()
    
    if not tabla:
        st.info("No hay jugadores registrados")
    else:
        for i, (nombre, pts, exactos, ganadores) in enumerate(tabla, 1):
            if i == 1:
                icon = "🥇"
            elif i == 2:
                icon = "🥈"
            elif i == 3:
                icon = "🥉"
            else:
                icon = f"{i}."
            st.markdown(f"{icon} **{nombre}** — **{pts} pts** (🟢{exactos} / 🟡{ganadores})")

# ════════════════════════════════════════════════════════════════════════════════
# 2. PREDICCIONES
elif menu == "🎯 Predecir":
    st.header(f"🎯 Predecir - {st.session_state.user_name}")
    
    partidos = get_partidos()
    ahora = datetime.now()
    
    disponibles = []
    for p in partidos:
        pid, local, visitante, gl, gv, fase, fecha, hora = p
        if gl is None:
            fecha_hora = datetime.combine(fecha, datetime.strptime(hora, "%H:%M").time())
            if fecha_hora > ahora:
                disponibles.append(p)
    
    if not disponibles:
        st.info("No hay partidos disponibles para predecir")
    else:
        for p in disponibles:
            pid, local, visitante, gl, gv, fase, fecha, hora = p
            pred = get_prediccion(st.session_state.user_id, pid)
            val_l = pred[0] if pred else 0
            val_v = pred[1] if pred else 0
            
            fecha_hora = datetime.combine(fecha, datetime.strptime(hora, "%H:%M").time())
            resto = fecha_hora - ahora
            horas = int(resto.total_seconds() // 3600)
            mins = int((resto.total_seconds() % 3600) // 60)
            
            col1, col2, col3, col4, col5 = st.columns([2, 1, 2, 1, 1])
            
            with col1:
                st.write(f"**{local}**")
                g_l = st.number_input("", 0, 10, val_l, key=f"l_{pid}", label_visibility="collapsed")
            with col2:
                st.write("vs")
            with col3:
                st.write(f"**{visitante}**")
                g_v = st.number_input("", 0, 10, val_v, key=f"v_{pid}", label_visibility="collapsed")
            with col4:
                if st.button("💾", key=f"s_{pid}", use_container_width=True):
                    ok, msg = guardar_prediccion(st.session_state.user_id, pid, g_l, g_v)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            with col5:
                st.caption(f"{fecha.day}/{fecha.month} {hora}")
            
            st.caption(f"⏰ {horas}h {mins}m")
            st.divider()

# ════════════════════════════════════════════════════════════════════════════════
# 3. MIS RESULTADOS
elif menu == "📊 Mis resultados":
    st.header(f"📊 Mis resultados - {st.session_state.user_name}")
    
    predicciones = get_mis_predicciones(st.session_state.user_id)
    
    if not predicciones:
        st.info("Aún no tienes predicciones")
    else:
        total = sum(p[10] for p in predicciones if p[10])
        st.metric("🏆 Puntos totales", total)
        st.divider()
        
        for p in predicciones:
            pid, local, visitante, gl, gv, fase, fecha, hora, pl, pv, pts = p
            if gl is not None:
                if pts == 3:
                    icon = "🟢"
                elif pts == 1:
                    icon = "🟡"
                else:
                    icon = "⚫"
                st.write(f"{icon} {local} {pl}-{pv} vs {visitante} → Real: {gl}-{gv} ({pts} pts)")
            else:
                st.write(f"⏳ {local} {pl}-{pv} vs {visitante} ({fecha.day}/{fecha.month} {hora})")

# ════════════════════════════════════════════════════════════════════════════════
# 4. CALENDARIO
elif menu == "📅 Calendario":
    st.header("📅 Calendario")
    
    partidos = get_partidos()
    ahora = datetime.now()
    
    for p in partidos:
        pid, local, visitante, gl, gv, fase, fecha, hora = p
        
        if gl is not None:
            resultado = f"{gl}-{gv}"
            icon = "✅"
        else:
            resultado = "vs"
            fecha_hora = datetime.combine(fecha, datetime.strptime(hora, "%H:%M").time())
            icon = "🔴" if fecha_hora <= ahora else "⏳"
        
        st.write(f"{icon} **{fecha.day}/{fecha.month} {hora}** — {local} {resultado} {visitante}")

# ════════════════════════════════════════════════════════════════════════════════
# ADMIN: RESULTADOS
if st.session_state.is_admin and admin_menu == "⚽ Resultados":
    st.header("⚽ Ingresar resultados")
    
    partidos = get_partidos()
    pendientes = [p for p in partidos if p[3] is None]
    
    if not pendientes:
        st.success("Todos los partidos tienen resultado")
    else:
        for p in pendientes:
            pid, local, visitante, gl, gv, fase, fecha, hora = p
            
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                gl_new = st.number_input(f"{local}", 0, 20, key=f"gl_{pid}")
            with col2:
                gv_new = st.number_input(f"{visitante}", 0, 20, key=f"gv_{pid}")
            with col3:
                if st.button(f"✅ {fecha.day}/{fecha.month}", key=f"r_{pid}"):
                    set_resultado(pid, gl_new, gv_new)
                    st.success(f"{local} {gl_new}-{gv_new} {visitante}")
                    st.rerun()
            st.divider()

# ════════════════════════════════════════════════════════════════════════════════
# ADMIN: AGREGAR PARTIDO
if st.session_state.is_admin and admin_menu == "➕ Partido":
    st.header("➕ Agregar partido")
    
    with st.form("new_match"):
        col1, col2 = st.columns(2)
        with col1:
            local = st.text_input("Equipo local")
        with col2:
            visitante = st.text_input("Equipo visitante")
        
        fase = st.selectbox("Fase", FASES_ELIMINATORIAS)
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            fecha = st.date_input("Fecha")
        with col_f2:
            hora = st.text_input("Hora", "15:00")
        
        if st.form_submit_button("Agregar partido", use_container_width=True):
            if local and visitante:
                add_partido(local, visitante, fase, fecha, hora)
                st.success(f"Partido agregado: {local} vs {visitante}")
                st.rerun()
            else:
                st.error("Completa todos los campos")
