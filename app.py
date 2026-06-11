import streamlit as st
import psycopg2
import os
import hashlib
from datetime import datetime, date

# ─── Configuración de página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="⚽ Quiniela Mundial 2026",
    page_icon="⚽",
    layout="wide"
)

# ─── CSS personalizado ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    .partido-card {
        background: linear-gradient(135deg, #1a472a 0%, #2d5a27 50%, #1a3a5c 100%);
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        color: white;
    }
    .grupo-header {
        background: linear-gradient(90deg, #c8a951 0%, #e8c96b 100%);
        border-radius: 8px;
        padding: 8px 16px;
        color: #1a1a1a;
        font-weight: bold;
        font-size: 1.1em;
        margin: 12px 0 6px 0;
    }
    .pts-exacto { color: #00ff88; font-weight: bold; }
    .pts-ganador { color: #ffd700; font-weight: bold; }
    .pts-cero { color: #ff4444; }
    .top1 { background: linear-gradient(90deg, #ffd700, #ffaa00); border-radius: 8px; padding: 8px 12px; }
    .top2 { background: linear-gradient(90deg, #c0c0c0, #a0a0a0); border-radius: 8px; padding: 8px 12px; }
    .top3 { background: linear-gradient(90deg, #cd7f32, #a0522d); border-radius: 8px; padding: 8px 12px; }
</style>
""", unsafe_allow_html=True)

# ─── DATOS: 48 equipos y 12 grupos del Mundial 2026 ───────────────────────────
GRUPOS = {
    "A": ["Mexico", "Sudafrica", "Corea del Sur", "Republica Checa"],
    "B": ["Canada", "Bosnia y Herzegovina", "Qatar", "Suiza"],
    "C": ["Brasil", "Marruecos", "Escocia", "Haiti"],
    "D": ["Estados Unidos", "Australia", "Paraguay", "Turquia"],
    "E": ["Alemania", "Ecuador", "Costa de Marfil", "Curazao"],
    "F": ["Japon", "Arabia Saudi", "Peru", "Rumania"],
    "G": ["Belgica", "Iran", "Egipto", "Nueva Zelanda"],
    "H": ["Espana", "Uruguay", "Arabia Saudi", "Cabo Verde"],
    "I": ["Francia", "Senegal", "Noruega", "Irak"],
    "J": ["Argentina", "Austria", "Chile", "Argelia"],
    "K": ["Portugal", "Colombia", "Uzbekistan", "Jamaica"],
    "L": ["Inglaterra", "Croacia", "Ghana", "Panama"],
}

# Calendario fase de grupos del Mundial 2026 (todos los partidos)
# Formato: (local, visitante, fase, fecha_str, sede)
CALENDARIO_GRUPOS = [
    # ─── GRUPO A ───
    ("Mexico", "Sudafrica", "Grupo A", "2026-06-11", "Ciudad de México"),
    ("Corea del Sur", "Republica Checa", "Grupo A", "2026-06-11", "Guadalajara"),
    ("Sudafrica", "Republica Checa", "Grupo A", "2026-06-18", "Atlanta"),
    ("Mexico", "Corea del Sur", "Grupo A", "2026-06-18", "Guadalajara"),
    ("Mexico", "Republica Checa", "Grupo A", "2026-06-24", "Ciudad de México"),
    ("Sudafrica", "Corea del Sur", "Grupo A", "2026-06-24", "Dallas"),
    # ─── GRUPO B ───
    ("Canada", "Bosnia y Herzegovina", "Grupo B", "2026-06-12", "Toronto"),
    ("Qatar", "Suiza", "Grupo B", "2026-06-12", "Vancouver"),
    ("Bosnia y Herzegovina", "Suiza", "Grupo B", "2026-06-18", "Houston"),
    ("Canada", "Qatar", "Grupo B", "2026-06-18", "Toronto"),
    ("Canada", "Suiza", "Grupo B", "2026-06-24", "Vancouver"),
    ("Bosnia y Herzegovina", "Qatar", "Grupo B", "2026-06-24", "Kansas City"),
    # ─── GRUPO C ───
    ("Brasil", "Haiti", "Grupo C", "2026-06-12", "Los Angeles"),
    ("Marruecos", "Escocia", "Grupo C", "2026-06-12", "Nueva York"),
    ("Brasil", "Marruecos", "Grupo C", "2026-06-19", "Los Angeles"),
    ("Escocia", "Haiti", "Grupo C", "2026-06-19", "Philadelphia"),
    ("Brasil", "Escocia", "Grupo C", "2026-06-25", "San Francisco"),
    ("Haiti", "Marruecos", "Grupo C", "2026-06-25", "Miami"),
    # ─── GRUPO D ───
    ("Estados Unidos", "Paraguay", "Grupo D", "2026-06-13", "Dallas"),
    ("Australia", "Turquia", "Grupo D", "2026-06-13", "Kansas City"),
    ("Estados Unidos", "Australia", "Grupo D", "2026-06-19", "New York"),
    ("Paraguay", "Turquia", "Grupo D", "2026-06-19", "Houston"),
    ("Estados Unidos", "Turquia", "Grupo D", "2026-06-25", "Miami"),
    ("Australia", "Paraguay", "Grupo D", "2026-06-25", "Seattle"),
    # ─── GRUPO E ───
    ("Alemania", "Costa de Marfil", "Grupo E", "2026-06-13", "Philadelphia"),
    ("Ecuador", "Curazao", "Grupo E", "2026-06-13", "Boston"),
    ("Alemania", "Ecuador", "Grupo E", "2026-06-20", "Atlanta"),
    ("Costa de Marfil", "Curazao", "Grupo E", "2026-06-20", "Dallas"),
    ("Alemania", "Curazao", "Grupo E", "2026-06-26", "Nueva York"),
    ("Ecuador", "Costa de Marfil", "Grupo E", "2026-06-26", "Houston"),
    # ─── GRUPO F ───
    ("Japon", "Peru", "Grupo F", "2026-06-14", "Seattle"),
    ("Arabia Saudi", "Rumania", "Grupo F", "2026-06-14", "Miami"),
    ("Japon", "Arabia Saudi", "Grupo F", "2026-06-20", "Los Angeles"),
    ("Peru", "Rumania", "Grupo F", "2026-06-20", "San Francisco"),
    ("Japon", "Rumania", "Grupo F", "2026-06-26", "Boston"),
    ("Peru", "Arabia Saudi", "Grupo F", "2026-06-26", "Kansas City"),
    # ─── GRUPO G ───
    ("Belgica", "Nueva Zelanda", "Grupo G", "2026-06-14", "Atlanta"),
    ("Iran", "Egipto", "Grupo G", "2026-06-14", "Dallas"),
    ("Belgica", "Iran", "Grupo G", "2026-06-21", "Nueva York"),
    ("Egipto", "Nueva Zelanda", "Grupo G", "2026-06-21", "Miami"),
    ("Belgica", "Egipto", "Grupo G", "2026-06-27", "Philadelphia"),
    ("Iran", "Nueva Zelanda", "Grupo G", "2026-06-27", "Boston"),
    # ─── GRUPO H ───
    ("Espana", "Cabo Verde", "Grupo H", "2026-06-15", "San Francisco"),
    ("Uruguay", "Arabia Saudi", "Grupo H", "2026-06-15", "Seattle"),
    ("Espana", "Uruguay", "Grupo H", "2026-06-21", "Los Angeles"),
    ("Cabo Verde", "Arabia Saudi", "Grupo H", "2026-06-21", "Guadalajara"),
    ("Espana", "Arabia Saudi", "Grupo H", "2026-06-27", "Dallas"),
    ("Uruguay", "Cabo Verde", "Grupo H", "2026-06-27", "Montreal"),
    # ─── GRUPO I ───
    ("Francia", "Irak", "Grupo I", "2026-06-15", "Houston"),
    ("Senegal", "Noruega", "Grupo I", "2026-06-15", "Kansas City"),
    ("Francia", "Senegal", "Grupo I", "2026-06-22", "Miami"),
    ("Noruega", "Irak", "Grupo I", "2026-06-22", "Philadelphia"),
    ("Francia", "Noruega", "Grupo I", "2026-06-27", "Atlanta"),
    ("Irak", "Senegal", "Grupo I", "2026-06-27", "Los Angeles"),
    # ─── GRUPO J ───
    ("Argentina", "Argelia", "Grupo J", "2026-06-16", "Dallas"),
    ("Austria", "Chile", "Grupo J", "2026-06-16", "Nueva York"),
    ("Argentina", "Austria", "Grupo J", "2026-06-22", "Miami"),
    ("Chile", "Argelia", "Grupo J", "2026-06-22", "Boston"),
    ("Argentina", "Chile", "Grupo J", "2026-06-28", "Los Angeles"),
    ("Argelia", "Austria", "Grupo J", "2026-06-28", "Seattle"),
    # ─── GRUPO K ───
    ("Portugal", "Jamaica", "Grupo K", "2026-06-16", "Boston"),
    ("Colombia", "Uzbekistan", "Grupo K", "2026-06-16", "Houston"),
    ("Portugal", "Colombia", "Grupo K", "2026-06-23", "Kansas City"),
    ("Jamaica", "Uzbekistan", "Grupo K", "2026-06-23", "Atlanta"),
    ("Portugal", "Uzbekistan", "Grupo K", "2026-06-28", "Philadelphia"),
    ("Colombia", "Jamaica", "Grupo K", "2026-06-28", "Dallas"),
    # ─── GRUPO L ───
    ("Inglaterra", "Ghana", "Grupo L", "2026-06-17", "Nueva York"),
    ("Croacia", "Panama", "Grupo L", "2026-06-17", "San Francisco"),
    ("Inglaterra", "Croacia", "Grupo L", "2026-06-23", "Philadelphia"),
    ("Panama", "Ghana", "Grupo L", "2026-06-23", "Houston"),
    ("Inglaterra", "Panama", "Grupo L", "2026-06-28", "Boston"),
    ("Ghana", "Croacia", "Grupo L", "2026-06-28", "Kansas City"),
]

# Fases eliminatorias (se cargan después)
FASES_ELIMINATORIAS = ["16avos de Final", "Octavos de Final", "Cuartos de Final", "Semifinal", "Tercer lugar", "Final"]

# ─── Conexión a Neon ───────────────────────────────────────────────────────────
@st.cache_resource
def get_db_pool():
    import psycopg2.pool
    return psycopg2.pool.SimpleConnectionPool(1, 5, os.environ["DATABASE_URL"])

def get_connection():
    return get_db_pool().getconn()

def release_connection(conn):
    get_db_pool().putconn(conn)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ─── Crear tablas ──────────────────────────────────────────────────────────────
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Tabla de jugadores (usuarios)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jugadores (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(64) NOT NULL,
            es_admin BOOLEAN DEFAULT FALSE,
            registrado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Tabla de partidos
    cur.execute("""
        CREATE TABLE IF NOT EXISTS partidos (
            id SERIAL PRIMARY KEY,
            equipo_local VARCHAR(60) NOT NULL,
            equipo_visitante VARCHAR(60) NOT NULL,
            goles_local INTEGER DEFAULT NULL,
            goles_visitante INTEGER DEFAULT NULL,
            fase VARCHAR(30) NOT NULL,
            fecha DATE NOT NULL,
            sede VARCHAR(50),
            precargado BOOLEAN DEFAULT FALSE
        );
    """)

    # Tabla de predicciones
    cur.execute("""
        CREATE TABLE IF NOT EXISTS predicciones (
            id SERIAL PRIMARY KEY,
            jugador_id INTEGER REFERENCES jugadores(id),
            partido_id INTEGER REFERENCES partidos(id),
            pred_local INTEGER NOT NULL,
            pred_visitante INTEGER NOT NULL,
            puntos INTEGER DEFAULT 0,
            UNIQUE(jugador_id, partido_id)
        );
    """)

    conn.commit()
    cur.close()
    conn.close()

def migrar_db():
    """Agrega columnas y tablas nuevas si no existen (migracion segura)."""
    conn = get_connection()
    cur = conn.cursor()

    # --- Tabla partidos: columnas nuevas ---
    cur.execute("ALTER TABLE partidos ADD COLUMN IF NOT EXISTS precargado BOOLEAN DEFAULT FALSE;")
    cur.execute("ALTER TABLE partidos ADD COLUMN IF NOT EXISTS sede VARCHAR(50);")

    # --- Tabla jugadores: crearla si no existe (bases sin registro) ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jugadores (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(64) NOT NULL,
            es_admin BOOLEAN DEFAULT FALSE,
            registrado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # --- Tabla predicciones: reconstruir si viene del esquema viejo ---
    # El esquema viejo usaba columna "usuario" (texto), el nuevo usa jugador_id (FK)
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name='predicciones';
    """)
    cols = {row[0] for row in cur.fetchall()}

    if 'jugador_id' not in cols:
        # Esquema viejo detectado: renombrar tabla vieja y crear la nueva
        cur.execute("ALTER TABLE predicciones RENAME TO predicciones_old;")
        cur.execute("""
            CREATE TABLE predicciones (
                id SERIAL PRIMARY KEY,
                jugador_id INTEGER REFERENCES jugadores(id),
                partido_id INTEGER REFERENCES partidos(id),
                pred_local INTEGER NOT NULL,
                pred_visitante INTEGER NOT NULL,
                puntos INTEGER DEFAULT 0,
                UNIQUE(jugador_id, partido_id)
            );
        """)
        # No migramos datos viejos porque usaban nombre de texto sin FK
    else:
        # Tabla nueva: asegurarse de que puntos existe
        cur.execute("ALTER TABLE predicciones ADD COLUMN IF NOT EXISTS puntos INTEGER DEFAULT 0;")

    conn.commit()
    cur.close()
    conn.close()

def precargar_calendario():
    """Inserta todos los partidos de la fase de grupos si aún no están."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM partidos WHERE precargado = TRUE")
    count = cur.fetchone()[0]
    if count == 0:
        for local, visitante, fase, fecha_str, sede in CALENDARIO_GRUPOS:
            cur.execute("""
                INSERT INTO partidos (equipo_local, equipo_visitante, fase, fecha, sede, precargado)
                VALUES (%s, %s, %s, %s, %s, TRUE)
                ON CONFLICT DO NOTHING
            """, (local, visitante, fase, fecha_str, sede))
        conn.commit()
    cur.close()
    conn.close()

# ─── Funciones de usuarios ─────────────────────────────────────────────────────
def registrar_jugador(nombre, email, password):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO jugadores (nombre, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
            (nombre, email, hash_password(password))
        )
        uid = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return uid, None
    except Exception as e:
        return None, str(e)

def login_jugador(email, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, nombre, es_admin FROM jugadores WHERE email=%s AND password_hash=%s",
        (email, hash_password(password))
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row  # (id, nombre, es_admin) o None

@st.cache_data(ttl=60)
def get_todos_jugadores():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, nombre, email, registrado_en FROM jugadores ORDER BY registrado_en DESC")
        rows = cur.fetchall()
        cur.close()
        return rows
    finally:
        release_connection(conn)

# ─── Funciones de partidos ─────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def get_partidos():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, equipo_local, equipo_visitante, goles_local, goles_visitante, fase, fecha, sede FROM partidos ORDER BY fecha, id")
        rows = cur.fetchall()
        cur.close()
        return rows
    finally:
        release_connection(conn)

def add_partido(local, visitante, fase, fecha, sede=""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO partidos (equipo_local, equipo_visitante, fase, fecha, sede) VALUES (%s, %s, %s, %s, %s)",
        (local, visitante, fase, fecha, sede)
    )
    conn.commit()
    cur.close()
    st.cache_data.clear()
    release_connection(conn)

def set_resultado(partido_id, goles_local, goles_visitante):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE partidos SET goles_local=%s, goles_visitante=%s WHERE id=%s",
                (goles_local, goles_visitante, partido_id))
    cur.execute("SELECT id, pred_local, pred_visitante FROM predicciones WHERE partido_id=%s", (partido_id,))
    for pred_id, pl, pv in cur.fetchall():
        puntos = calcular_puntos(pl, pv, goles_local, goles_visitante)
        cur.execute("UPDATE predicciones SET puntos=%s WHERE id=%s", (puntos, pred_id))
    conn.commit()
    cur.close()
    conn.close()

# ─── Funciones de predicciones ─────────────────────────────────────────────────
def save_prediccion(jugador_id, partido_id, pred_local, pred_visitante):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO predicciones (jugador_id, partido_id, pred_local, pred_visitante)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (jugador_id, partido_id)
        DO UPDATE SET pred_local=EXCLUDED.pred_local, pred_visitante=EXCLUDED.pred_visitante, puntos=0
    """, (jugador_id, partido_id, pred_local, pred_visitante))
    conn.commit()
    cur.close()
    conn.close()

@st.cache_data(ttl=30)
def get_predicciones_jugador(jugador_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT p.id, p.equipo_local, p.equipo_visitante, p.goles_local, p.goles_visitante,
                   p.fase, p.fecha, pr.pred_local, pr.pred_visitante, pr.puntos
            FROM predicciones pr
            JOIN partidos p ON pr.partido_id = p.id
            WHERE pr.jugador_id = %s
            ORDER BY p.fecha
        """, (jugador_id,))
        rows = cur.fetchall()
        cur.close()
        return rows
    finally:
        release_connection(conn)

@st.cache_data(ttl=30)
def get_prediccion_existente(jugador_id, partido_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT pred_local, pred_visitante FROM predicciones WHERE jugador_id=%s AND partido_id=%s",
                    (jugador_id, partido_id))
        row = cur.fetchone()
        cur.close()
        return row
    finally:
        release_connection(conn)

@st.cache_data(ttl=30)
def get_tabla_posiciones():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT j.nombre, 
                   COALESCE(SUM(pr.puntos), 0) as total,
                   COUNT(CASE WHEN pr.puntos = 3 THEN 1 END) as exactos,
                   COUNT(CASE WHEN pr.puntos = 1 THEN 1 END) as ganadores,
                   COUNT(pr.id) as total_preds
            FROM jugadores j
            LEFT JOIN predicciones pr ON j.id = pr.jugador_id
            GROUP BY j.id, j.nombre
            ORDER BY total DESC, exactos DESC
        """)
        rows = cur.fetchall()
        cur.close()
        return rows
    finally:
        release_connection(conn)
    return rows

def calcular_puntos(pred_l, pred_v, real_l, real_v):
    if pred_l == real_l and pred_v == real_v:
        return 3
    pg = "L" if pred_l > pred_v else ("V" if pred_v > pred_l else "E")
    rg = "L" if real_l > real_v else ("V" if real_v > real_l else "E")
    return 1 if pg == rg else 0

# ─── Inicializar DB ─────────────────────────────────────────────────────────────
try:
    init_db()
    migrar_db()
    precargar_calendario()
except Exception as e:
    st.error(f"❌ Error de base de datos: {e}")
    st.stop()

# ─── Estado de sesión ──────────────────────────────────────────────────────────
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "usuario_id" not in st.session_state:
    st.session_state.usuario_id = None
if "es_admin" not in st.session_state:
    st.session_state.es_admin = False

# ─── Header ───────────────────────────────────────────────────────────────────
col_logo, col_title, col_user = st.columns([1, 5, 2])
with col_logo:
    st.markdown("## ⚽")
with col_title:
    st.markdown("# Quiniela Mundial 2026 🏆")
    st.caption(" Estados Unidos ·  México ·  Canadá — 11 Jun al 19 Jul 2026")
with col_user:
    if st.session_state.usuario:
        st.markdown(f"👤 **{st.session_state.usuario}**")
        if st.button("Cerrar sesión"):
            st.session_state.usuario = None
            st.session_state.usuario_id = None
            st.session_state.es_admin = False
            st.rerun()

st.markdown("---")

# ─── LOGIN / REGISTRO ──────────────────────────────────────────────────────────
if not st.session_state.usuario:
    tab_login, tab_registro = st.tabs(["🔑 Iniciar sesión", "📝 Registrarse"])

    with tab_login:
        st.subheader("Iniciar sesión")
        email_in = st.text_input("📧 Email", key="login_email")
        pass_in = st.text_input("🔒 Contraseña", type="password", key="login_pass")
        if st.button("Entrar →", type="primary"):
            if email_in and pass_in:
                resultado = login_jugador(email_in, pass_in)
                if resultado:
                    st.session_state.usuario_id = resultado[0]
                    st.session_state.usuario = resultado[1]
                    st.session_state.es_admin = resultado[2]
                    st.success(f"¡Bienvenido, {resultado[1]}! 🎉")
                    st.rerun()
                else:
                    st.error("Email o contraseña incorrectos.")
            else:
                st.warning("Completa todos los campos.")

    with tab_registro:
        st.subheader("Crear cuenta")
        st.info("Regístrate para participar en la quiniela.")
        r_nombre = st.text_input("👤 Nombre o apodo", placeholder="Ej: El Profe", key="reg_nombre")
        r_email = st.text_input("📧 Email", placeholder="tu@email.com", key="reg_email")
        r_pass = st.text_input("🔒 Contraseña", type="password", key="reg_pass")
        r_pass2 = st.text_input("🔒 Repetir contraseña", type="password", key="reg_pass2")
        if st.button("Crear cuenta ✅", type="primary"):
            if not all([r_nombre, r_email, r_pass, r_pass2]):
                st.warning("Completa todos los campos.")
            elif r_pass != r_pass2:
                st.error("Las contraseñas no coinciden.")
            elif len(r_pass) < 4:
                st.error("La contraseña debe tener al menos 4 caracteres.")
            else:
                uid, err = registrar_jugador(r_nombre, r_email, r_pass)
                if uid:
                    st.success(f"¡Cuenta creada! Ahora inicia sesión.")
                else:
                    if "unique" in str(err).lower():
                        st.error("Ese nombre o email ya está registrado.")
                    else:
                        st.error(f"Error: {err}")
    st.stop()

# ─── MENÚ PRINCIPAL (solo usuarios logueados) ──────────────────────────────────
opciones_menu = [
    "🏆 Tabla de Posiciones",
    "📅 Calendario del Mundial",
    "🎯 Hacer mis Predicciones",
    "📊 Mis Resultados",
    "👥 Jugadores Registrados",
]
if st.session_state.es_admin:
    opciones_menu += [
        "⚽ Admin: Agregar partido",
        "✅ Admin: Ingresar Resultados",
        "🔧 Admin: Panel",
    ]

menu = st.sidebar.selectbox("📋 Navegación", opciones_menu)
st.sidebar.markdown("---")
st.sidebar.markdown("**🌍 Mundial 2026**")
st.sidebar.markdown("48 equipos · 12 grupos · 104 partidos")
st.sidebar.markdown("🗓️ 11 Jun — 19 Jul 2026")

# ════════════════════════════════════════════════════════════════════════════════
# 1. TABLA DE POSICIONES
# ════════════════════════════════════════════════════════════════════════════════
if menu == "🏆 Tabla de Posiciones":
    st.header("🏆 Tabla de Posiciones")
    tabla = get_tabla_posiciones()

    if not tabla:
        st.info("Aún no hay jugadores registrados.")
    else:
        st.markdown("### Clasificación general")
        for i, (nombre, total, exactos, ganadores, total_preds) in enumerate(tabla):
            if i == 0:
                bg = "background: linear-gradient(90deg,#ffd700,#ffaa00); border-radius:10px; padding:10px;"
                icon = "🥇"
            elif i == 1:
                bg = "background: linear-gradient(90deg,#c0c0c0,#aaaaaa); border-radius:10px; padding:10px;"
                icon = "🥈"
            elif i == 2:
                bg = "background: linear-gradient(90deg,#cd7f32,#a0522d); border-radius:10px; padding:10px; color:white;"
                icon = "🥉"
            else:
                bg = "background:#f0f0f0; border-radius:10px; padding:10px;"
                icon = f"#{i+1}"
            
            c1, c2, c3, c4, c5 = st.columns([1, 4, 2, 2, 2])
            c1.markdown(f"**{icon}**")
            c2.markdown(f"**{nombre}**")
            c3.markdown(f"**{total} pts**")
            c4.markdown(f"🟢 {exactos} exactos")
            c5.markdown(f"🟡 {ganadores} ganador")

        st.markdown("---")
        st.caption("🟢 3 pts = marcador exacto | 🟡 1 pt = acertó ganador/empate | ⚫ 0 pts = falló")

# ════════════════════════════════════════════════════════════════════════════════
# 2. CALENDARIO DEL MUNDIAL
# ════════════════════════════════════════════════════════════════════════════════
elif menu == "📅 Calendario del Mundial":
    st.header("📅 Calendario del Mundial 2026")
    
    tab_grupos, tab_elim, tab_grupos_list = st.tabs(["⚽ Fase de Grupos", "🏆 Eliminatorias", "🌍 Los 12 Grupos"])

    with tab_grupos:
        st.subheader("Fase de Grupos (11 Jun — 27 Jun 2026)")
        partidos = get_partidos()
        partidos_grupos = [p for p in partidos if p[5].startswith("Grupo")]
        
        grupo_sel = st.selectbox("Filtrar por grupo:", ["Todos"] + [f"Grupo {g}" for g in "ABCDEFGHIJKL"])
        
        fecha_actual = None
        for pid, local, visitante, gl, gv, fase, fecha, sede in partidos_grupos:
            if grupo_sel != "Todos" and fase != grupo_sel:
                continue
            if fecha != fecha_actual:
                st.markdown(f"**📆 {fecha.strftime('%d de %B, %Y') if hasattr(fecha,'strftime') else fecha}**")
                fecha_actual = fecha
            
            resultado = f"{gl} - {gv}" if gl is not None else "vs"
            emoji_fase = f"**{fase}**"
            sede_str = f"📍 {sede}" if sede else ""
            
            c1, c2, c3, c4 = st.columns([3, 1, 3, 2])
            c1.markdown(f"{local}")
            c2.markdown(f"**{resultado}**")
            c3.markdown(f"{visitante}")
            c4.markdown(f"{emoji_fase} {sede_str}")

    with tab_elim:
        st.subheader("Fase Eliminatoria")
        st.info("Los partidos eliminatorios se generarán automáticamente según los resultados de grupos.")
        
        rondas_info = [
            ("16avos de Final", "29 Jun — 3 Jul", "32 equipos"),
            ("Octavos de Final", "4 Jul — 7 Jul", "16 equipos"),
            ("Cuartos de Final", "9 Jul — 10 Jul", "8 equipos"),
            ("Semifinales", "14 Jul — 15 Jul", "4 equipos"),
            ("Tercer lugar", "18 Jul", "Miami"),
            ("🏆 Gran Final", "19 Jul 2026", "Nueva York / Nueva Jersey"),
        ]
        for ronda, fecha_str, detalle in rondas_info:
            col1, col2, col3 = st.columns([3, 2, 2])
            col1.markdown(f"**{ronda}**")
            col2.markdown(f"🗓️ {fecha_str}")
            col3.markdown(f"👥 {detalle}")
        
        # Mostrar partidos eliminatorios si ya hay cargados
        partidos_elim = [p for p in get_partidos() if not p[5].startswith("Grupo")]
        if partidos_elim:
            st.markdown("### Partidos eliminatorios cargados:")
            for pid, local, visitante, gl, gv, fase, fecha, sede in partidos_elim:
                resultado = f"{gl} - {gv}" if gl is not None else "vs"
                st.markdown(f"**{fase}** | {local} **{resultado}** {visitante} — {sede}")

    with tab_grupos_list:
        st.subheader("🌍 Los 48 Equipos — 12 Grupos")
        for letra, equipos in GRUPOS.items():
            st.markdown(f'<div class="grupo-header">GRUPO {letra}</div>', unsafe_allow_html=True)
            for eq in equipos:
                st.markdown(f"&nbsp;&nbsp;&nbsp;• {eq}")

# ════════════════════════════════════════════════════════════════════════════════
# 3. HACER PREDICCIONES
# ════════════════════════════════════════════════════════════════════════════════
elif menu == "🎯 Hacer mis Predicciones":
    st.header(f"🎯 Predicciones de {st.session_state.usuario}")
    
    partidos = get_partidos()
    hoy = date.today()

    def to_date(val):
        try:
            if val is None:
                return hoy
            if hasattr(val, 'date') and callable(val.date):
                return val.date()
            if hasattr(val, 'year'):  # already a date
                return val
            return datetime.strptime(str(val)[:10], "%Y-%m-%d").date()
        except Exception:
            return hoy

    try:
        partidos_pendientes = [p for p in partidos if p[3] is None and to_date(p[6]) >= hoy]
        partidos_pasados_sin_pred = [p for p in partidos if p[3] is None and to_date(p[6]) < hoy]
    except Exception:
        # Si la comparacion de fechas falla por cualquier razon, mostrar todos sin resultado
        partidos_pendientes = [p for p in partidos if p[3] is None]
        partidos_pasados_sin_pred = []

    if not partidos_pendientes and not partidos_pasados_sin_pred:
        st.success("¡Ya predijiste todos los partidos disponibles! 🎉")
    
    if partidos_pasados_sin_pred:
        st.warning(f"⚠️ Hay {len(partidos_pasados_sin_pred)} partidos cuya fecha ya pasó y no puedes predecirlos.")

    if partidos_pendientes:
        # Agrupar por fase
        fases_disponibles = list(dict.fromkeys([p[5] for p in partidos_pendientes]))
        fase_sel = st.selectbox("Filtrar por fase:", ["Todos"] + fases_disponibles)
        
        st.info("💡 Ingresa tu predicción antes de que empiece el partido. 3 pts por exacto, 1 pt por ganador.")
        
        guardados = 0
        for partido in partidos_pendientes:
            pid, local, visitante, gl, gv, fase, fecha, sede = partido
            if fase_sel != "Todos" and fase != fase_sel:
                continue
            
            pred_existente = get_prediccion_existente(st.session_state.usuario_id, pid)
            val_l = pred_existente[0] if pred_existente else 0
            val_v = pred_existente[1] if pred_existente else 0
            etiqueta = "✏️ Editar" if pred_existente else "Nueva"
            
            with st.expander(f"{'✅' if pred_existente else '⏳'} {local} vs {visitante} — {fase} | {fecha} | 📍{sede}"):
                c1, c2, c3 = st.columns([3, 1, 3])
                c1.markdown(f"### {local}")
                c2.markdown("**vs**")
                c3.markdown(f"### {visitante}")
                
                cc1, cc2 = st.columns(2)
                new_l = cc1.number_input(f"Goles {local}", min_value=0, max_value=20, value=val_l, key=f"nl_{pid}")
                new_v = cc2.number_input(f"Goles {visitante}", min_value=0, max_value=20, value=val_v, key=f"nv_{pid}")
                
                if st.button(f"💾 {etiqueta} predicción", key=f"sbtn_{pid}"):
                    save_prediccion(st.session_state.usuario_id, pid, new_l, new_v)
                    st.success(f"✅ Guardado: {local} {new_l} - {new_v} {visitante}")
                    guardados += 1

# ════════════════════════════════════════════════════════════════════════════════
# 4. MIS RESULTADOS
# ════════════════════════════════════════════════════════════════════════════════
elif menu == "📊 Mis Resultados":
    st.header(f"📊 Resultados de {st.session_state.usuario}")
    
    preds = get_predicciones_jugador(st.session_state.usuario_id)
    
    if not preds:
        st.info("Aún no tienes predicciones. Ve a '🎯 Hacer mis Predicciones'.")
    else:
        total_pts = sum(p[9] for p in preds)
        exactos = sum(1 for p in preds if p[9] == 3 and p[3] is not None)
        ganadores = sum(1 for p in preds if p[9] == 1 and p[3] is not None)
        fallidos = sum(1 for p in preds if p[9] == 0 and p[3] is not None)
        pendientes = sum(1 for p in preds if p[3] is None)

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("🏆 Puntos totales", total_pts)
        c2.metric("🟢 Exactos", exactos)
        c3.metric("🟡 Ganadores", ganadores)
        c4.metric("⚫ Fallidos", fallidos)
        c5.metric("⏳ Pendientes", pendientes)
        
        st.markdown("---")
        
        fase_actual = None
        for pid, local, visitante, gl, gv, fase, fecha, pl, pv, puntos in preds:
            if fase != fase_actual:
                st.markdown(f"#### {fase}")
                fase_actual = fase
            
            if gl is not None:
                if puntos == 3:
                    icon = "🟢"
                    label = "Exacto (+3)"
                elif puntos == 1:
                    icon = "🟡"
                    label = "Ganador (+1)"
                else:
                    icon = "⚫"
                    label = "Falló (0)"
                real = f"{gl}-{gv}"
            else:
                icon = "⏳"
                label = "Pendiente"
                real = "—"
            
            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 2])
            c1.markdown(f"{icon} **{local} vs {visitante}**")
            c2.markdown(f"Tu pred: **{pl}-{pv}**")
            c3.markdown(f"Real: **{real}**")
            c4.markdown(f"**{label}**")
            c5.markdown(f"Fecha: {fecha}")

# ════════════════════════════════════════════════════════════════════════════════
# 5. JUGADORES REGISTRADOS
# ════════════════════════════════════════════════════════════════════════════════
elif menu == "👥 Jugadores Registrados":
    st.header("👥 Jugadores de la Quiniela")
    jugadores = get_todos_jugadores()
    tabla = get_tabla_posiciones()
    pts_dict = {nombre: (pts, ex, gn) for nombre, pts, ex, gn, _ in tabla}
    
    st.markdown(f"**Total de participantes: {len(jugadores)}**")
    st.markdown("---")
    
    for jid, nombre, email, reg_en in jugadores:
        pts, ex, gn = pts_dict.get(nombre, (0, 0, 0))
        c1, c2, c3 = st.columns([3, 2, 3])
        c1.markdown(f"👤 **{nombre}**")
        c2.markdown(f"**{pts} pts** (🟢{ex} / 🟡{gn})")
        reg_str = reg_en.strftime("%d/%m/%Y") if hasattr(reg_en, "strftime") else str(reg_en)
        c3.markdown(f"Registrado: {reg_str}")

# ════════════════════════════════════════════════════════════════════════════════
# ADMIN: AGREGAR PARTIDO
# ════════════════════════════════════════════════════════════════════════════════
elif menu == "⚽ Admin: Agregar partido" and st.session_state.es_admin:
    st.header("⚽ Agregar Partido")
    st.info("Usa esto para agregar partidos de la fase eliminatoria cuando se conozcan los cruces.")
    
    todos_equipos = sorted(set(eq for eqs in GRUPOS.values() for eq in eqs))
    
    with st.form("form_partido"):
        c1, c2 = st.columns(2)
        local = c1.selectbox("Equipo Local", todos_equipos + ["Por definir (local)", "Por definir (visitante)"])
        visitante = c2.selectbox("Equipo Visitante", todos_equipos + ["Por definir (local)", "Por definir (visitante)"])
        fase = st.selectbox("Fase", FASES_ELIMINATORIAS)
        c3, c4 = st.columns(2)
        fecha = c3.date_input("Fecha")
        sede = c4.text_input("Sede / Ciudad")
        if st.form_submit_button("➕ Agregar partido"):
            if local != visitante:
                add_partido(local, visitante, fase, fecha, sede)
                st.success(f"✅ Agregado: {local} vs {visitante}")
            else:
                st.error("Los equipos deben ser distintos.")

# ════════════════════════════════════════════════════════════════════════════════
# ADMIN: INGRESAR RESULTADOS
# ════════════════════════════════════════════════════════════════════════════════
elif menu == "✅ Admin: Ingresar Resultados" and st.session_state.es_admin:
    st.header("✅ Ingresar Resultados Reales")
    
    partidos = get_partidos()
    pendientes = [p for p in partidos if p[3] is None]
    jugados = [p for p in partidos if p[3] is not None]
    
    tab1, tab2 = st.tabs([f"⏳ Pendientes ({len(pendientes)})", f"✅ Con resultado ({len(jugados)})"])
    
    with tab1:
        if not pendientes:
            st.success("Todos los partidos tienen resultado.")
        fase_actual = None
        for pid, local, visitante, gl, gv, fase, fecha, sede in pendientes:
            if fase != fase_actual:
                st.markdown(f"#### {fase}")
                fase_actual = fase
            with st.expander(f"⚽ {local} vs {visitante} — {fecha} — 📍{sede}"):
                cc1, cc2 = st.columns(2)
                r_gl = cc1.number_input(f"Goles {local}", 0, 20, 0, key=f"rgl_{pid}")
                r_gv = cc2.number_input(f"Goles {visitante}", 0, 20, 0, key=f"rgv_{pid}")
                if st.button("✅ Guardar resultado", key=f"rbtn_{pid}"):
                    set_resultado(pid, r_gl, r_gv)
                    st.success(f"✅ {local} {r_gl} - {r_gv} {visitante}")
                    st.rerun()
    
    with tab2:
        for pid, local, visitante, gl, gv, fase, fecha, sede in jugados:
            st.markdown(f"✅ **{local} {gl} — {gv} {visitante}** | {fase} | {fecha}")

# ════════════════════════════════════════════════════════════════════════════════
# ADMIN: PANEL
# ════════════════════════════════════════════════════════════════════════════════
elif menu == "🔧 Admin: Panel" and st.session_state.es_admin:
    st.header("🔧 Panel de Administración")
    
    partidos = get_partidos()
    jugadores = get_todos_jugadores()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM predicciones")
    total_preds = cur.fetchone()[0]
    cur.close()
    conn.close()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("⚽ Partidos cargados", len(partidos))
    c2.metric("👥 Jugadores", len(jugadores))
    c3.metric("🎯 Predicciones", total_preds)
    
    st.markdown("---")
    st.subheader("👥 Todos los jugadores")
    for jid, nombre, email, reg_en in jugadores:
        st.markdown(f"- ID {jid}: **{nombre}** ({email})")
    
    st.markdown("---")
    st.subheader("🔐 Hacer admin a un usuario")
    st.info("Ejecuta en Neon: `UPDATE jugadores SET es_admin=TRUE WHERE email='tu@email.com';`")
