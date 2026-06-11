import streamlit as st
import psycopg2
import os
import hashlib
from datetime import datetime, date
from functools import lru_cache

# ─── Configuración de página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="⚽ Quiniela Mundial 2026",
    page_icon="⚽",
    layout="wide"
)

# ─── CSS personalizado ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    .grupo-header {
        background: linear-gradient(90deg, #c8a951 0%, #e8c96b 100%);
        border-radius: 8px;
        padding: 8px 16px;
        color: #1a1a1a;
        font-weight: bold;
        margin: 12px 0 6px 0;
    }
    .medalla-oro { background: linear-gradient(135deg, #ffd700, #ffaa00); border-radius: 10px; padding: 10px; margin: 5px 0; }
    .medalla-plata { background: linear-gradient(135deg, #c0c0c0, #a0a0a0); border-radius: 10px; padding: 10px; margin: 5px 0; }
    .medalla-bronce { background: linear-gradient(135deg, #cd7f32, #a0522d); border-radius: 10px; padding: 10px; margin: 5px 0; color: white; }
    .jugador-normal { background: #f0f0f0; border-radius: 10px; padding: 10px; margin: 5px 0; }
</style>
""", unsafe_allow_html=True)

# ─── DATOS ─────────────────────────────────────────────────────────────────────
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

CALENDARIO_GRUPOS = [
    ("Mexico", "Sudafrica", "Grupo A", "2026-06-11", "Ciudad de México"),
    ("Corea del Sur", "Republica Checa", "Grupo A", "2026-06-11", "Guadalajara"),
    ("Sudafrica", "Republica Checa", "Grupo A", "2026-06-18", "Atlanta"),
    ("Mexico", "Corea del Sur", "Grupo A", "2026-06-18", "Guadalajara"),
    ("Mexico", "Republica Checa", "Grupo A", "2026-06-24", "Ciudad de México"),
    ("Sudafrica", "Corea del Sur", "Grupo A", "2026-06-24", "Dallas"),
    ("Canada", "Bosnia y Herzegovina", "Grupo B", "2026-06-12", "Toronto"),
    ("Qatar", "Suiza", "Grupo B", "2026-06-12", "Vancouver"),
    ("Bosnia y Herzegovina", "Suiza", "Grupo B", "2026-06-18", "Houston"),
    ("Canada", "Qatar", "Grupo B", "2026-06-18", "Toronto"),
    ("Canada", "Suiza", "Grupo B", "2026-06-24", "Vancouver"),
    ("Bosnia y Herzegovina", "Qatar", "Grupo B", "2026-06-24", "Kansas City"),
    ("Brasil", "Haiti", "Grupo C", "2026-06-12", "Los Angeles"),
    ("Marruecos", "Escocia", "Grupo C", "2026-06-12", "Nueva York"),
    ("Brasil", "Marruecos", "Grupo C", "2026-06-19", "Los Angeles"),
    ("Escocia", "Haiti", "Grupo C", "2026-06-19", "Philadelphia"),
    ("Brasil", "Escocia", "Grupo C", "2026-06-25", "San Francisco"),
    ("Haiti", "Marruecos", "Grupo C", "2026-06-25", "Miami"),
    ("Estados Unidos", "Paraguay", "Grupo D", "2026-06-13", "Dallas"),
    ("Australia", "Turquia", "Grupo D", "2026-06-13", "Kansas City"),
    ("Estados Unidos", "Australia", "Grupo D", "2026-06-19", "New York"),
    ("Paraguay", "Turquia", "Grupo D", "2026-06-19", "Houston"),
    ("Estados Unidos", "Turquia", "Grupo D", "2026-06-25", "Miami"),
    ("Australia", "Paraguay", "Grupo D", "2026-06-25", "Seattle"),
    ("Alemania", "Costa de Marfil", "Grupo E", "2026-06-13", "Philadelphia"),
    ("Ecuador", "Curazao", "Grupo E", "2026-06-13", "Boston"),
    ("Alemania", "Ecuador", "Grupo E", "2026-06-20", "Atlanta"),
    ("Costa de Marfil", "Curazao", "Grupo E", "2026-06-20", "Dallas"),
    ("Alemania", "Curazao", "Grupo E", "2026-06-26", "Nueva York"),
    ("Ecuador", "Costa de Marfil", "Grupo E", "2026-06-26", "Houston"),
    ("Japon", "Peru", "Grupo F", "2026-06-14", "Seattle"),
    ("Arabia Saudi", "Rumania", "Grupo F", "2026-06-14", "Miami"),
    ("Japon", "Arabia Saudi", "Grupo F", "2026-06-20", "Los Angeles"),
    ("Peru", "Rumania", "Grupo F", "2026-06-20", "San Francisco"),
    ("Japon", "Rumania", "Grupo F", "2026-06-26", "Boston"),
    ("Peru", "Arabia Saudi", "Grupo F", "2026-06-26", "Kansas City"),
    ("Belgica", "Nueva Zelanda", "Grupo G", "2026-06-14", "Atlanta"),
    ("Iran", "Egipto", "Grupo G", "2026-06-14", "Dallas"),
    ("Belgica", "Iran", "Grupo G", "2026-06-21", "Nueva York"),
    ("Egipto", "Nueva Zelanda", "Grupo G", "2026-06-21", "Miami"),
    ("Belgica", "Egipto", "Grupo G", "2026-06-27", "Philadelphia"),
    ("Iran", "Nueva Zelanda", "Grupo G", "2026-06-27", "Boston"),
    ("Espana", "Cabo Verde", "Grupo H", "2026-06-15", "San Francisco"),
    ("Uruguay", "Arabia Saudi", "Grupo H", "2026-06-15", "Seattle"),
    ("Espana", "Uruguay", "Grupo H", "2026-06-21", "Los Angeles"),
    ("Cabo Verde", "Arabia Saudi", "Grupo H", "2026-06-21", "Guadalajara"),
    ("Espana", "Arabia Saudi", "Grupo H", "2026-06-27", "Dallas"),
    ("Uruguay", "Cabo Verde", "Grupo H", "2026-06-27", "Montreal"),
    ("Francia", "Irak", "Grupo I", "2026-06-15", "Houston"),
    ("Senegal", "Noruega", "Grupo I", "2026-06-15", "Kansas City"),
    ("Francia", "Senegal", "Grupo I", "2026-06-22", "Miami"),
    ("Noruega", "Irak", "Grupo I", "2026-06-22", "Philadelphia"),
    ("Francia", "Noruega", "Grupo I", "2026-06-27", "Atlanta"),
    ("Irak", "Senegal", "Grupo I", "2026-06-27", "Los Angeles"),
    ("Argentina", "Argelia", "Grupo J", "2026-06-16", "Dallas"),
    ("Austria", "Chile", "Grupo J", "2026-06-16", "Nueva York"),
    ("Argentina", "Austria", "Grupo J", "2026-06-22", "Miami"),
    ("Chile", "Argelia", "Grupo J", "2026-06-22", "Boston"),
    ("Argentina", "Chile", "Grupo J", "2026-06-28", "Los Angeles"),
    ("Argelia", "Austria", "Grupo J", "2026-06-28", "Seattle"),
    ("Portugal", "Jamaica", "Grupo K", "2026-06-16", "Boston"),
    ("Colombia", "Uzbekistan", "Grupo K", "2026-06-16", "Houston"),
    ("Portugal", "Colombia", "Grupo K", "2026-06-23", "Kansas City"),
    ("Jamaica", "Uzbekistan", "Grupo K", "2026-06-23", "Atlanta"),
    ("Portugal", "Uzbekistan", "Grupo K", "2026-06-28", "Philadelphia"),
    ("Colombia", "Jamaica", "Grupo K", "2026-06-28", "Dallas"),
    ("Inglaterra", "Ghana", "Grupo L", "2026-06-17", "Nueva York"),
    ("Croacia", "Panama", "Grupo L", "2026-06-17", "San Francisco"),
    ("Inglaterra", "Croacia", "Grupo L", "2026-06-23", "Philadelphia"),
    ("Panama", "Ghana", "Grupo L", "2026-06-23", "Houston"),
    ("Inglaterra", "Panama", "Grupo L", "2026-06-28", "Boston"),
    ("Ghana", "Croacia", "Grupo L", "2026-06-28", "Kansas City"),
]

FASES_ELIMINATORIAS = ["16avos de Final", "Octavos de Final", "Cuartos de Final", "Semifinal", "Tercer lugar", "Final"]

# ─── Conexión a Neon ───────────────────────────────────────────────────────────
@st.cache_resource
def get_db_connection():
    return psycopg2.connect(os.environ["DATABASE_URL"])

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ─── Crear tablas ───────────────────────────────────────────────────────────────
@st.cache_resource
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
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
    
    cur.execute("ALTER TABLE partidos ADD COLUMN IF NOT EXISTS precargado BOOLEAN DEFAULT FALSE;")
    cur.execute("ALTER TABLE partidos ADD COLUMN IF NOT EXISTS sede VARCHAR(50);")
    cur.execute("ALTER TABLE predicciones ADD COLUMN IF NOT EXISTS puntos INTEGER DEFAULT 0;")
    
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

# ─── Funciones optimizadas ─────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_todos_jugadores():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre, email, registrado_en FROM jugadores ORDER BY registrado_en DESC")
    rows = cur.fetchall()
    cur.close()
    return rows

@st.cache_data(ttl=300)
def get_partidos():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, equipo_local, equipo_visitante, goles_local, goles_visitante, fase, fecha, sede FROM partidos ORDER BY fecha, id")
    rows = cur.fetchall()
    cur.close()
    return rows

@st.cache_data(ttl=300)
def get_tabla_posiciones():
    """Obtiene la tabla completa de posiciones de todos los jugadores"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT j.id, j.nombre, 
               COALESCE(SUM(pr.puntos), 0) as total,
               COUNT(CASE WHEN pr.puntos = 3 THEN 1 END) as exactos,
               COUNT(CASE WHEN pr.puntos = 1 THEN 1 END) as ganadores,
               COUNT(pr.id) as total_predicciones
        FROM jugadores j
        LEFT JOIN predicciones pr ON j.id = pr.jugador_id
        GROUP BY j.id, j.nombre
        ORDER BY total DESC, exactos DESC
    """)
    rows = cur.fetchall()
    cur.close()
    return rows

@st.cache_data(ttl=300)
def get_predicciones_jugador(jugador_id):
    conn = get_db_connection()
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

def get_prediccion_existente(jugador_id, partido_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT pred_local, pred_visitante FROM predicciones WHERE jugador_id=%s AND partido_id=%s",
                (jugador_id, partido_id))
    row = cur.fetchone()
    cur.close()
    return row

# ─── Funciones de escritura ────────────────────────────────────────────────────
def registrar_jugador(nombre, email, password):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO jugadores (nombre, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
            (nombre, email, hash_password(password))
        )
        uid = cur.fetchone()[0]
        conn.commit()
        cur.close()
        st.cache_data.clear()
        return uid, None
    except Exception as e:
        return None, str(e)

def login_jugador(email, password):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, nombre, es_admin FROM jugadores WHERE email=%s AND password_hash=%s",
        (email, hash_password(password))
    )
    row = cur.fetchone()
    cur.close()
    return row

def save_prediccion(jugador_id, partido_id, pred_local, pred_visitante):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO predicciones (jugador_id, partido_id, pred_local, pred_visitante)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (jugador_id, partido_id)
        DO UPDATE SET pred_local=EXCLUDED.pred_local, pred_visitante=EXCLUDED.pred_visitante, puntos=0
    """, (jugador_id, partido_id, pred_local, pred_visitante))
    conn.commit()
    cur.close()
    st.cache_data.clear()

def set_resultado(partido_id, goles_local, goles_visitante):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE partidos SET goles_local=%s, goles_visitante=%s WHERE id=%s",
                (goles_local, goles_visitante, partido_id))
    
    cur.execute("SELECT jugador_id, pred_local, pred_visitante FROM predicciones WHERE partido_id=%s", (partido_id,))
    for jugador_id, pl, pv in cur.fetchall():
        puntos = calcular_puntos(pl, pv, goles_local, goles_visitante)
        cur.execute("UPDATE predicciones SET puntos=%s WHERE partido_id=%s AND jugador_id=%s", 
                   (puntos, partido_id, jugador_id))
    
    conn.commit()
    cur.close()
    st.cache_data.clear()

def add_partido(local, visitante, fase, fecha, sede=""):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO partidos (equipo_local, equipo_visitante, fase, fecha, sede) VALUES (%s, %s, %s, %s, %s)",
        (local, visitante, fase, fecha, sede)
    )
    conn.commit()
    cur.close()
    st.cache_data.clear()

def calcular_puntos(pred_l, pred_v, real_l, real_v):
    if pred_l == real_l and pred_v == real_v:
        return 3
    pg = "L" if pred_l > pred_v else ("V" if pred_v > pred_l else "E")
    rg = "L" if real_l > real_v else ("V" if real_v > real_l else "E")
    return 1 if pg == rg else 0

# ─── Inicializar DB ─────────────────────────────────────────────────────────────
try:
    init_db()
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
    st.caption("Estados Unidos · México · Canadá — 11 Jun al 19 Jul 2026")
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

    with tab_registro:
        st.subheader("Crear cuenta")
        r_nombre = st.text_input("👤 Nombre", key="reg_nombre")
        r_email = st.text_input("📧 Email", key="reg_email")
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
                    st.success("¡Cuenta creada! Ahora inicia sesión.")
                else:
                    st.error("Ese nombre o email ya está registrado." if "unique" in str(err).lower() else f"Error: {err}")
    st.stop()

# ─── MENÚ ──────────────────────────────────────────────────────────────────────
opciones_menu = ["🏆 Tabla de Posiciones", "📅 Calendario", "🎯 Predicciones", "📊 Mis resultados", "👥 Jugadores"]
if st.session_state.es_admin:
    opciones_menu += ["⚽ Resultados", "➕ Partido"]

menu = st.sidebar.selectbox("📋 Menú", opciones_menu)

# ════════════════════════════════════════════════════════════════════════════════
# 1. TABLA DE POSICIONES - Aquí se ve quién va ganando
if menu == "🏆 Tabla de Posiciones":
    st.header("🏆 Tabla de Posiciones")
    st.subheader("Clasificación General")
    
    tabla = get_tabla_posiciones()
    
    if not tabla:
        st.info("Aún no hay jugadores registrados.")
    else:
        # Mostrar estadísticas generales
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("👥 Participantes", len(tabla))
        with col2:
            lider = tabla[0][1] if tabla else "—"
            st.metric("🥇 Líder", lider)
        with col3:
            max_puntos = tabla[0][2] if tabla else 0
            st.metric("🏆 Puntos líder", max_puntos)
        
        st.markdown("---")
        
        # Mostrar tabla detallada
        for i, (jid, nombre, total, exactos, ganadores, total_preds) in enumerate(tabla, 1):
            # Medallas para los primeros 3
            if i == 1:
                st.markdown(f'<div class="medalla-oro">', unsafe_allow_html=True)
                icono = "🥇"
                bg_class = "oro"
            elif i == 2:
                st.markdown(f'<div class="medalla-plata">', unsafe_allow_html=True)
                icono = "🥈"
                bg_class = "plata"
            elif i == 3:
                st.markdown(f'<div class="medalla-bronce">', unsafe_allow_html=True)
                icono = "🥉"
                bg_class = "bronce"
            else:
                st.markdown(f'<div class="jugador-normal">', unsafe_allow_html=True)
                icono = f"#{i}"
                bg_class = "normal"
            
            # Mostrar jugador
            col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 2])
            with col1:
                st.markdown(f"## {icono}")
            with col2:
                st.markdown(f"### {nombre}")
                if i == 1:
                    st.caption("👑 Líder del torneo")
            with col3:
                st.markdown(f"**{total} puntos**")
            with col4:
                st.markdown(f"🟢 {exactos} exactos")
            with col5:
                st.markdown(f"🟡 {ganadores} ganador")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.caption("🟢 3 puntos = Marcador exacto | 🟡 1 punto = Acertó ganador o empate")

# ════════════════════════════════════════════════════════════════════════════════
# 2. CALENDARIO
elif menu == "📅 Calendario":
    st.header("📅 Calendario del Mundial 2026")
    
    partidos = get_partidos()
    
    # Filtros
    col_filtro1, col_filtro2 = st.columns(2)
    with col_filtro1:
        fases_opciones = list(set([p[5] for p in partidos]))
        fase_filter = st.selectbox("Filtrar por fase:", ["Todas"] + sorted(fases_opciones))
    with col_filtro2:
        mostrar_solo_futuros = st.checkbox("Mostrar solo partidos futuros", value=False)
    
    hoy = date.today()
    
    for pid, local, visitante, gl, gv, fase, fecha, sede in partidos:
        # Aplicar filtros
        if fase_filter != "Todas" and fase != fase_filter:
            continue
        if mostrar_solo_futuros and fecha < hoy:
            continue
        
        resultado = f"{gl}-{gv}" if gl is not None else "vs"
        
        # Color según estado
        if gl is not None:
            status = "✅"
        elif fecha < hoy:
            status = "⏰"
        else:
            status = "⏳"
        
        st.markdown(f"{status} **{fecha}** — {local} **{resultado}** {visitante} — *{sede}*")

# ════════════════════════════════════════════════════════════════════════════════
# 3. PREDICCIONES
elif menu == "🎯 Predicciones":
    st.header(f"🎯 Tus Predicciones - {st.session_state.usuario}")
    
    partidos = get_partidos()
    pendientes = [p for p in partidos if p[3] is None]
    
    if not pendientes:
        st.success("🎉 ¡Ya predijiste todos los partidos!")
    else:
        st.info(f"Te faltan {len(pendientes)} partidos por predecir")
        
        for partido in pendientes:
            pid, local, visitante, gl, gv, fase, fecha, sede = partido
            pred = get_prediccion_existente(st.session_state.usuario_id, pid)
            val_l, val_v = pred if pred else (0, 0)
            
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 2, 1])
                with col1:
                    st.write(f"**{local}**")
                    new_l = st.number_input("", 0, 10, val_l, key=f"l_{pid}", label_visibility="collapsed")
                with col2:
                    st.write("vs")
                with col3:
                    st.write(f"**{visitante}**")
                    new_v = st.number_input("", 0, 10, val_v, key=f"v_{pid}", label_visibility="collapsed")
                with col4:
                    if st.button(f"💾", key=f"save_{pid}"):
                        save_prediccion(st.session_state.usuario_id, pid, new_l, new_v)
                        st.success(f"✅ {local} {new_l}-{new_v} {visitante}")
                        st.rerun()
                st.caption(f"{fase} - {fecha} - {sede}")
                st.divider()

# ════════════════════════════════════════════════════════════════════════════════
# 4. MIS RESULTADOS
elif menu == "📊 Mis resultados":
    st.header(f"📊 Tus Resultados - {st.session_state.usuario}")
    
    preds = get_predicciones_jugador(st.session_state.usuario_id)
    
    if not preds:
        st.info("Aún no tienes predicciones.")
    else:
        total = sum(p[9] for p in preds)
        exactos = sum(1 for p in preds if p[9] == 3)
        ganadores = sum(1 for p in preds if p[9] == 1)
        pendientes = sum(1 for p in preds if p[3] is None)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🏆 Puntos", total)
        col2.metric("🟢 Exactos", exactos)
        col3.metric("🟡 Ganadores", ganadores)
        col4.metric("⏳ Pendientes", pendientes)
        
        st.divider()
        
        for p in preds:
            pid, local, visitante, gl, gv, fase, fecha, pl, pv, pts = p
            if gl is not None:
                icon = "🟢" if pts == 3 else "🟡" if pts == 1 else "⚫"
                st.write(f"{icon} **{local}** {pl}-{pv} vs **{visitante}** → Real: {gl}-{gv} → **{pts} pts**")
            else:
                st.write(f"⏳ **{local}** {pl}-{pv} vs **{visitante}** (Pendiente - {fecha})")

# ════════════════════════════════════════════════════════════════════════════════
# 5. JUGADORES
elif menu == "👥 Jugadores":
    st.header("👥 Todos los Jugadores")
    
    tabla = get_tabla_posiciones()
    tabla_dict = {nombre: (total, exactos, ganadores) for _, nombre, total, exactos, ganadores, _ in tabla}
    
    for jid, nombre, email, reg in get_todos_jugadores():
        total, exactos, ganadores = tabla_dict.get(nombre, (0, 0, 0))
        with st.expander(f"👤 {nombre}"):
            st.write(f"📧 {email}")
            st.write(f"🏆 {total} puntos")
            st.write(f"🟢 {exactos} marcadores exactos")
            st.write(f"🟡 {ganadores} ganadores acertados")
            st.write(f"📅 Registrado: {reg.strftime('%d/%m/%Y') if hasattr(reg, 'strftime') else reg}")

# ════════════════════════════════════════════════════════════════════════════════
# ADMIN: RESULTADOS
elif menu == "⚽ Resultados" and st.session_state.es_admin:
    st.header("⚽ Ingresar Resultados")
    
    partidos = get_partidos()
    pendientes = [p for p in partidos if p[3] is None]
    
    if not pendientes:
        st.success("✅ Todos los partidos ya tienen resultado")
    else:
        for pid, local, visitante, gl, gv, fase, fecha, sede in pendientes:
            with st.container():
                st.markdown(f"**{fase}** - {fecha} - {sede}")
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    gl_new = st.number_input(f"Goles {local}", 0, 20, 0, key=f"gl_{pid}")
                with col2:
                    gv_new = st.number_input(f"Goles {visitante}", 0, 20, 0, key=f"gv_{pid}")
                with col3:
                    if st.button(f"✅ Guardar", key=f"res_{pid}"):
                        set_resultado(pid, gl_new, gv_new)
                        st.success(f"✅ {local} {gl_new}-{gv_new} {visitante}")
                        st.rerun()
                st.divider()

# ════════════════════════════════════════════════════════════════════════════════
# ADMIN: AGREGAR PARTIDO
elif menu == "➕ Partido" and st.session_state.es_admin:
    st.header("➕ Agregar Partido")
    
    with st.form("nuevo_partido"):
        col1, col2 = st.columns(2)
        with col1:
            local = st.text_input("Equipo Local")
        with col2:
            visitante = st.text_input("Equipo Visitante")
        
        fase = st.selectbox("Fase", FASES_ELIMINATORIAS)
        fecha = st.date_input("Fecha")
        sede = st.text_input("Sede/Ciudad")
        
        if st.form_submit_button("Agregar Partido"):
            if local and visitante and local != visitante:
                add_partido(local, visitante, fase, fecha, sede)
                st.success(f"✅ Partido agregado: {local} vs {visitante}")
                st.rerun()
            else:
                st.error("Completa todos los campos correctamente")
