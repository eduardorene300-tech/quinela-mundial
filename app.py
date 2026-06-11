import streamlit as st
import psycopg2
import os
import hashlib
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

# ─── Configuración de página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="⚽ Quiniela Mundial 2026",
    page_icon="⚽",
    layout="wide"
)

# ─── ZONA HORARIA DE VENEZUELA ─────────────────────────────────────────────────
VENEZUELA_TZ = ZoneInfo('America/Caracas')

def ahora_venezuela():
    return datetime.now(VENEZUELA_TZ)

# ─── CSS minimalista ───────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stButton button { width: 100%; }
    div[data-testid="column"] { padding: 0 4px; }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
# DATOS COMPLETOS DEL MUNDIAL 2026
# ════════════════════════════════════════════════════════════════════════════════

# ─── FASE DE GRUPOS (72 partidos) ──────────────────────────────────────────────
CALENDARIO_GRUPOS = [
    # GRUPO A (6 partidos)
    ("Mexico", "Sudafrica", "Grupo A", "2026-06-11", "15:00"),
    ("Corea del Sur", "Republica Checa", "Grupo A", "2026-06-11", "18:00"),
    ("Mexico", "Corea del Sur", "Grupo A", "2026-06-18", "20:00"),
    ("Sudafrica", "Republica Checa", "Grupo A", "2026-06-18", "14:00"),
    ("Mexico", "Republica Checa", "Grupo A", "2026-06-24", "16:00"),
    ("Sudafrica", "Corea del Sur", "Grupo A", "2026-06-24", "19:00"),
    
    # GRUPO B (6 partidos)
    ("Canada", "Bosnia y Herzegovina", "Grupo B", "2026-06-12", "13:00"),
    ("Qatar", "Suiza", "Grupo B", "2026-06-12", "16:00"),
    ("Canada", "Qatar", "Grupo B", "2026-06-18", "20:00"),
    ("Bosnia y Herzegovina", "Suiza", "Grupo B", "2026-06-18", "18:00"),
    ("Canada", "Suiza", "Grupo B", "2026-06-24", "14:00"),
    ("Bosnia y Herzegovina", "Qatar", "Grupo B", "2026-06-24", "17:00"),
    
    # GRUPO C (6 partidos)
    ("Brasil", "Haiti", "Grupo C", "2026-06-12", "12:00"),
    ("Marruecos", "Escocia", "Grupo C", "2026-06-12", "15:00"),
    ("Brasil", "Marruecos", "Grupo C", "2026-06-19", "14:00"),
    ("Escocia", "Haiti", "Grupo C", "2026-06-19", "17:00"),
    ("Brasil", "Escocia", "Grupo C", "2026-06-25", "13:00"),
    ("Haiti", "Marruecos", "Grupo C", "2026-06-25", "16:00"),
    
    # GRUPO D (6 partidos)
    ("Estados Unidos", "Paraguay", "Grupo D", "2026-06-13", "15:00"),
    ("Australia", "Turquia", "Grupo D", "2026-06-13", "18:00"),
    ("Estados Unidos", "Australia", "Grupo D", "2026-06-19", "14:00"),
    ("Paraguay", "Turquia", "Grupo D", "2026-06-19", "20:00"),
    ("Estados Unidos", "Turquia", "Grupo D", "2026-06-25", "16:00"),
    ("Australia", "Paraguay", "Grupo D", "2026-06-25", "19:00"),
    
    # GRUPO E (6 partidos)
    ("Alemania", "Costa de Marfil", "Grupo E", "2026-06-13", "13:00"),
    ("Ecuador", "Curazao", "Grupo E", "2026-06-13", "16:00"),
    ("Alemania", "Ecuador", "Grupo E", "2026-06-20", "15:00"),
    ("Costa de Marfil", "Curazao", "Grupo E", "2026-06-20", "18:00"),
    ("Alemania", "Curazao", "Grupo E", "2026-06-26", "14:00"),
    ("Ecuador", "Costa de Marfil", "Grupo E", "2026-06-26", "17:00"),
    
    # GRUPO F (6 partidos)
    ("Japon", "Peru", "Grupo F", "2026-06-14", "12:00"),
    ("Arabia Saudi", "Rumania", "Grupo F", "2026-06-14", "15:00"),
    ("Japon", "Arabia Saudi", "Grupo F", "2026-06-20", "14:00"),
    ("Peru", "Rumania", "Grupo F", "2026-06-20", "17:00"),
    ("Japon", "Rumania", "Grupo F", "2026-06-26", "13:00"),
    ("Peru", "Arabia Saudi", "Grupo F", "2026-06-26", "16:00"),
    
    # GRUPO G (6 partidos)
    ("Belgica", "Nueva Zelanda", "Grupo G", "2026-06-14", "13:00"),
    ("Iran", "Egipto", "Grupo G", "2026-06-14", "16:00"),
    ("Belgica", "Iran", "Grupo G", "2026-06-21", "15:00"),
    ("Egipto", "Nueva Zelanda", "Grupo G", "2026-06-21", "18:00"),
    ("Belgica", "Egipto", "Grupo G", "2026-06-27", "14:00"),
    ("Iran", "Nueva Zelanda", "Grupo G", "2026-06-27", "17:00"),
    
    # GRUPO H (6 partidos)
    ("Espana", "Cabo Verde", "Grupo H", "2026-06-15", "12:00"),
    ("Uruguay", "Arabia Saudi", "Grupo H", "2026-06-15", "15:00"),
    ("Espana", "Uruguay", "Grupo H", "2026-06-21", "14:00"),
    ("Cabo Verde", "Arabia Saudi", "Grupo H", "2026-06-21", "17:00"),
    ("Espana", "Arabia Saudi", "Grupo H", "2026-06-27", "13:00"),
    ("Uruguay", "Cabo Verde", "Grupo H", "2026-06-27", "16:00"),
    
    # GRUPO I (6 partidos)
    ("Francia", "Irak", "Grupo I", "2026-06-15", "13:00"),
    ("Senegal", "Noruega", "Grupo I", "2026-06-15", "16:00"),
    ("Francia", "Senegal", "Grupo I", "2026-06-22", "15:00"),
    ("Noruega", "Irak", "Grupo I", "2026-06-22", "18:00"),
    ("Francia", "Noruega", "Grupo I", "2026-06-27", "14:00"),
    ("Irak", "Senegal", "Grupo I", "2026-06-27", "17:00"),
    
    # GRUPO J (6 partidos)
    ("Argentina", "Argelia", "Grupo J", "2026-06-16", "15:00"),
    ("Austria", "Chile", "Grupo J", "2026-06-16", "18:00"),
    ("Argentina", "Austria", "Grupo J", "2026-06-22", "14:00"),
    ("Chile", "Argelia", "Grupo J", "2026-06-22", "17:00"),
    ("Argentina", "Chile", "Grupo J", "2026-06-28", "16:00"),
    ("Argelia", "Austria", "Grupo J", "2026-06-28", "19:00"),
    
    # GRUPO K (6 partidos)
    ("Portugal", "Jamaica", "Grupo K", "2026-06-16", "13:00"),
    ("Colombia", "Uzbekistan", "Grupo K", "2026-06-16", "16:00"),
    ("Portugal", "Colombia", "Grupo K", "2026-06-23", "15:00"),
    ("Jamaica", "Uzbekistan", "Grupo K", "2026-06-23", "18:00"),
    ("Portugal", "Uzbekistan", "Grupo K", "2026-06-28", "14:00"),
    ("Colombia", "Jamaica", "Grupo K", "2026-06-28", "17:00"),
    
    # GRUPO L (6 partidos)
    ("Inglaterra", "Ghana", "Grupo L", "2026-06-17", "15:00"),
    ("Croacia", "Panama", "Grupo L", "2026-06-17", "18:00"),
    ("Inglaterra", "Croacia", "Grupo L", "2026-06-23", "14:00"),
    ("Panama", "Ghana", "Grupo L", "2026-06-23", "17:00"),
    ("Inglaterra", "Panama", "Grupo L", "2026-06-28", "13:00"),
    ("Ghana", "Croacia", "Grupo L", "2026-06-28", "16:00"),
]

# ─── FASE ELIMINATORIA COMPLETA ────────────────────────────────────────────────
# 16avos de Final (16 partidos) - 32 equipos
CALENDARIO_16AVOS = [
    ("1A", "2B", "16avos de Final", "2026-06-29", "12:00"),
    ("1C", "2D", "16avos de Final", "2026-06-29", "15:00"),
    ("1E", "2F", "16avos de Final", "2026-06-30", "12:00"),
    ("1G", "2H", "16avos de Final", "2026-06-30", "15:00"),
    ("1I", "2J", "16avos de Final", "2026-07-01", "12:00"),
    ("1K", "2L", "16avos de Final", "2026-07-01", "15:00"),
    ("2A", "1B", "16avos de Final", "2026-07-02", "12:00"),
    ("2C", "1D", "16avos de Final", "2026-07-02", "15:00"),
    ("2E", "1F", "16avos de Final", "2026-07-03", "12:00"),
    ("2G", "1H", "16avos de Final", "2026-07-03", "15:00"),
    ("2I", "1J", "16avos de Final", "2026-07-04", "12:00"),
    ("2K", "1L", "16avos de Final", "2026-07-04", "15:00"),
    ("3A", "3B", "16avos de Final", "2026-07-05", "12:00"),
    ("3C", "3D", "16avos de Final", "2026-07-05", "15:00"),
    ("3E", "3F", "16avos de Final", "2026-07-06", "12:00"),
    ("3G", "3H", "16avos de Final", "2026-07-06", "15:00"),
]

# Octavos de Final (8 partidos) - 16 equipos
CALENDARIO_OCTAVOS = [
    ("Ganador 16avos 1", "Ganador 16avos 2", "Octavos de Final", "2026-07-07", "12:00"),
    ("Ganador 16avos 3", "Ganador 16avos 4", "Octavos de Final", "2026-07-07", "15:00"),
    ("Ganador 16avos 5", "Ganador 16avos 6", "Octavos de Final", "2026-07-08", "12:00"),
    ("Ganador 16avos 7", "Ganador 16avos 8", "Octavos de Final", "2026-07-08", "15:00"),
    ("Ganador 16avos 9", "Ganador 16avos 10", "Octavos de Final", "2026-07-09", "12:00"),
    ("Ganador 16avos 11", "Ganador 16avos 12", "Octavos de Final", "2026-07-09", "15:00"),
    ("Ganador 16avos 13", "Ganador 16avos 14", "Octavos de Final", "2026-07-10", "12:00"),
    ("Ganador 16avos 15", "Ganador 16avos 16", "Octavos de Final", "2026-07-10", "15:00"),
]

# Cuartos de Final (4 partidos) - 8 equipos
CALENDARIO_CUARTOS = [
    ("Ganador Octavos 1", "Ganador Octavos 2", "Cuartos de Final", "2026-07-11", "12:00"),
    ("Ganador Octavos 3", "Ganador Octavos 4", "Cuartos de Final", "2026-07-11", "15:00"),
    ("Ganador Octavos 5", "Ganador Octavos 6", "Cuartos de Final", "2026-07-12", "12:00"),
    ("Ganador Octavos 7", "Ganador Octavos 8", "Cuartos de Final", "2026-07-12", "15:00"),
]

# Semifinales (2 partidos) - 4 equipos
CALENDARIO_SEMIFINALES = [
    ("Ganador Cuartos 1", "Ganador Cuartos 2", "Semifinal", "2026-07-14", "15:00"),
    ("Ganador Cuartos 3", "Ganador Cuartos 4", "Semifinal", "2026-07-15", "15:00"),
]

# Tercer Lugar (1 partido)
CALENDARIO_TERCER_LUGAR = [
    ("Perdedor Semifinal 1", "Perdedor Semifinal 2", "Tercer Lugar", "2026-07-18", "15:00"),
]

# Final (1 partido)
CALENDARIO_FINAL = [
    ("Ganador Semifinal 1", "Ganador Semifinal 2", "Final", "2026-07-19", "15:00"),
]

# Unir todas las fases eliminatorias
CALENDARIO_ELIMINACION = (
    CALENDARIO_16AVOS + 
    CALENDARIO_OCTAVOS + 
    CALENDARIO_CUARTOS + 
    CALENDARIO_SEMIFINALES + 
    CALENDARIO_TERCER_LUGAR + 
    CALENDARIO_FINAL
)

# Total de partidos eliminatorios: 16 + 8 + 4 + 2 + 1 + 1 = 32 partidos
# Total general: 72 (grupos) + 32 (eliminatorias) = 104 partidos

FASES_ELIMINATORIAS = ["16avos de Final", "Octavos de Final", "Cuartos de Final", "Semifinal", "Tercer Lugar", "Final"]

# ─── VARIABLE GLOBAL DE CONEXIÓN ───────────────────────────────────────────────
_conn = None

def get_db_connection():
    global _conn
    if _conn is None or _conn.closed:
        _conn = psycopg2.connect(os.environ["DATABASE_URL"])
    return _conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ─── FUNCIÓN PARTIDO COMENZADO ─────────────────────────────────────────────────
def partido_ha_comenzado(fecha_partido, hora_partido):
    try:
        ahora = ahora_venezuela()
        if isinstance(fecha_partido, str):
            fecha_hora = datetime.strptime(f"{fecha_partido} {hora_partido}", "%Y-%m-%d %H:%M")
        else:
            fecha_hora = datetime.combine(fecha_partido, datetime.strptime(hora_partido, "%H:%M").time())
        fecha_hora = fecha_hora.replace(tzinfo=VENEZUELA_TZ)
        return fecha_hora <= ahora
    except:
        return False

# ─── INICIALIZAR BD ────────────────────────────────────────────────────────────
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Crear tablas
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
    
    # Admin por defecto
    admin_pass = hash_password("admin123")
    cur.execute("""
        INSERT INTO jugadores (nombre, email, password_hash, es_admin)
        SELECT 'Admin', 'admin@quiniela.com', %s, TRUE
        WHERE NOT EXISTS (SELECT 1 FROM jugadores WHERE email = 'admin@quiniela.com')
    """, (admin_pass,))
    
    # Limpiar y cargar TODOS los partidos
    cur.execute("DELETE FROM partidos")
    
    # Cargar fase de grupos (72 partidos)
    for local, visitante, fase, fecha_str, hora in CALENDARIO_GRUPOS:
        cur.execute("""
            INSERT INTO partidos (equipo_local, equipo_visitante, fase, fecha, hora)
            VALUES (%s, %s, %s, %s, %s)
        """, (local, visitante, fase, fecha_str, hora))
    
    # Cargar todas las eliminatorias (32 partidos)
    for local, visitante, fase, fecha_str, hora in CALENDARIO_ELIMINACION:
        cur.execute("""
            INSERT INTO partidos (equipo_local, equipo_visitante, fase, fecha, hora)
            VALUES (%s, %s, %s, %s, %s)
        """, (local, visitante, fase, fecha_str, hora))
    
    conn.commit()

# ─── FUNCIONES DE CONSULTA ─────────────────────────────────────────────────────
def ejecutar_consulta(sql, params=None):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        return cur.fetchall()
    except Exception as e:
        global _conn
        _conn = None
        conn = get_db_connection()
        cur = conn.cursor()
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        return cur.fetchall()

def ejecutar_comando(sql, params=None):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        conn.commit()
        st.cache_data.clear()
        return True, None
    except Exception as e:
        global _conn
        _conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            if params:
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            conn.commit()
            st.cache_data.clear()
            return True, None
        except Exception as e2:
            return False, str(e2)

# ─── FUNCIONES DE NEGOCIO ──────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def get_partidos():
    return ejecutar_consulta("SELECT id, equipo_local, equipo_visitante, goles_local, goles_visitante, fase, fecha, hora FROM partidos ORDER BY fecha, hora")

@st.cache_data(ttl=600)
def get_tabla_posiciones():
    return ejecutar_consulta("""
        SELECT j.nombre, COALESCE(SUM(pr.puntos), 0) as total,
               COUNT(CASE WHEN pr.puntos = 3 THEN 1 END) as exactos,
               COUNT(CASE WHEN pr.puntos = 1 THEN 1 END) as ganadores
        FROM jugadores j
        LEFT JOIN predicciones pr ON j.id = pr.jugador_id
        GROUP BY j.id, j.nombre
        ORDER BY total DESC, exactos DESC
    """)

@st.cache_data(ttl=600)
def get_mis_predicciones(jugador_id):
    return ejecutar_consulta("""
        SELECT p.id, p.equipo_local, p.equipo_visitante, p.goles_local, p.goles_visitante,
               p.fase, p.fecha, p.hora, pr.pred_local, pr.pred_visitante, pr.puntos
        FROM predicciones pr
        JOIN partidos p ON pr.partido_id = p.id
        WHERE pr.jugador_id = %s
        ORDER BY p.fecha, p.hora
    """, (jugador_id,))

def get_prediccion(jugador_id, partido_id):
    rows = ejecutar_consulta("SELECT pred_local, pred_visitante FROM predicciones WHERE jugador_id=%s AND partido_id=%s",
                             (jugador_id, partido_id))
    return rows[0] if rows else None

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
    rows = ejecutar_consulta(
        "SELECT id, nombre, es_admin FROM jugadores WHERE email=%s AND password_hash=%s",
        (email, hash_password(password))
    )
    return rows[0] if rows else None

def guardar_prediccion(jugador_id, partido_id, pred_local, pred_visitante):
    try:
        partido = ejecutar_consulta("SELECT fecha, hora, goles_local FROM partidos WHERE id = %s", (partido_id,))
        if not partido:
            return False, "Partido no encontrado"
        
        fecha, hora, goles = partido[0]
        
        if goles is not None:
            return False, "Partido ya finalizado"
        
        if partido_ha_comenzado(fecha, hora):
            return False, "El partido ya comenzó"
        
        ok, err = ejecutar_comando("""
            INSERT INTO predicciones (jugador_id, partido_id, pred_local, pred_visitante)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (jugador_id, partido_id)
            DO UPDATE SET pred_local=EXCLUDED.pred_local, pred_visitante=EXCLUDED.pred_visitante, puntos=0
        """, (jugador_id, partido_id, pred_local, pred_visitante))
        
        if ok:
            st.cache_data.clear()
            return True, "Predicción guardada"
        return False, err
    except Exception as e:
        return False, str(e)

def borrar_prediccion(jugador_id, partido_id):
    try:
        partido = ejecutar_consulta("SELECT fecha, hora, goles_local FROM partidos WHERE id = %s", (partido_id,))
        if not partido:
            return False, "Partido no encontrado"
        
        fecha, hora, goles = partido[0]
        
        if goles is not None:
            return False, "No se puede borrar: el partido ya finalizó"
        
        if partido_ha_comenzado(fecha, hora):
            return False, "No se puede borrar: el partido ya comenzó"
        
        ok, err = ejecutar_comando("DELETE FROM predicciones WHERE jugador_id=%s AND partido_id=%s", (jugador_id, partido_id))
        
        if ok:
            st.cache_data.clear()
            return True, "Predicción borrada"
        return False, err
    except Exception as e:
        return False, str(e)

def limpiar_todas_predicciones_usuario(jugador_id):
    ok, err = ejecutar_comando("DELETE FROM predicciones WHERE jugador_id=%s", (jugador_id,))
    if ok:
        st.cache_data.clear()
        return True, "Todas tus predicciones fueron eliminadas"
    return False, err

def set_resultado(partido_id, goles_local, goles_visitante):
    ok, err = ejecutar_comando("UPDATE partidos SET goles_local=%s, goles_visitante=%s WHERE id=%s",
                               (goles_local, goles_visitante, partido_id))
    if not ok:
        return
    
    predicciones = ejecutar_consulta("SELECT jugador_id, pred_local, pred_visitante FROM predicciones WHERE partido_id=%s", (partido_id,))
    for jugador_id, pl, pv in predicciones:
        if pl == goles_local and pv == goles_visitante:
            puntos = 3
        elif (pl > pv and goles_local > goles_visitante) or (pl < pv and goles_local < goles_visitante) or (pl == pv and goles_local == goles_visitante):
            puntos = 1
        else:
            puntos = 0
        ejecutar_comando("UPDATE predicciones SET puntos=%s WHERE partido_id=%s AND jugador_id=%s", 
                        (puntos, partido_id, jugador_id))
    
    st.cache_data.clear()

def add_partido(local, visitante, fase, fecha, hora):
    ejecutar_comando("""
        INSERT INTO partidos (equipo_local, equipo_visitante, fase, fecha, hora)
        VALUES (%s, %s, %s, %s, %s)
    """, (local, visitante, fase, fecha, hora))

# ─── INICIALIZAR ───────────────────────────────────────────────────────────────
try:
    init_db()
except Exception as e:
    st.error(f"Error: {e}")
    st.stop()

# ─── ESTADO DE SESIÓN ──────────────────────────────────────────────────────────
if "user_id" not in st.session_state:
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.is_admin = False

# ─── HEADER ────────────────────────────────────────────────────────────────────
st.title("⚽ Quiniela Mundial 2026")
st.caption("11 Jun - 19 Jul 2026 | USA · México · Canadá")
st.info(f"📅 Hora Venezuela: {ahora_venezuela().strftime('%d/%m/%Y %H:%M:%S')}")

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
    
    # Mostrar cantidad de partidos
    partidos = get_partidos()
    st.caption(f"📊 {len(partidos)} partidos cargados")

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
    
    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn2:
        if st.button("🗑️ Limpiar todas", use_container_width=True):
            ok, msg = limpiar_todas_predicciones_usuario(st.session_state.user_id)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
    
    st.divider()
    
    partidos = get_partidos()
    ahora = ahora_venezuela()
    
    disponibles = [p for p in partidos if p[3] is None]
    
    if not disponibles:
        st.info("No hay partidos disponibles para predecir")
    else:
        for p in disponibles:
            pid, local, visitante, gl, gv, fase, fecha, hora = p
            pred = get_prediccion(st.session_state.user_id, pid)
            tiene_pred = pred is not None
            val_l = pred[0] if pred else 0
            val_v = pred[1] if pred else 0
            
            fecha_hora = datetime.combine(fecha, datetime.strptime(hora, "%H:%M").time()).replace(tzinfo=VENEZUELA_TZ)
            ya_comenzo = fecha_hora <= ahora
            
            if ya_comenzo:
                tiempo_text = "🔴 Cerrado"
                disabled = True
            else:
                resto = fecha_hora - ahora
                horas = int(resto.total_seconds() // 3600)
                mins = int((resto.total_seconds() % 3600) // 60)
                tiempo_text = f"🟢 {horas}h {mins}m"
                disabled = False
            
            if tiene_pred:
                st.markdown(f"📝 **{local} vs {visitante}** - Actual: {val_l}-{val_v}")
            else:
                st.markdown(f"⚪ **{local} vs {visitante}** - Sin predicción")
            
            col1, col2, col3, col4, col5 = st.columns([2, 1, 2, 1, 1])
            
            with col1:
                g_l = st.number_input(f"{local}", 0, 10, val_l, key=f"l_{pid}", label_visibility="collapsed", disabled=disabled)
            with col2:
                st.write("vs")
            with col3:
                g_v = st.number_input(f"{visitante}", 0, 10, val_v, key=f"v_{pid}", label_visibility="collapsed", disabled=disabled)
            with col4:
                if not disabled:
                    if st.button("💾", key=f"s_{pid}", use_container_width=True):
                        ok, msg = guardar_prediccion(st.session_state.user_id, pid, g_l, g_v)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
            with col5:
                if tiene_pred and not disabled:
                    if st.button("🗑️", key=f"d_{pid}", use_container_width=True):
                        ok, msg = borrar_prediccion(st.session_state.user_id, pid)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
            
            st.caption(f"📅 {fecha.day}/{fecha.month} {hora} | {tiempo_text} | {fase}")
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
                fecha_hora = datetime.combine(fecha, datetime.strptime(hora, "%H:%M").time()).replace(tzinfo=VENEZUELA_TZ)
                ahora = ahora_venezuela()
                if fecha_hora > ahora:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"⏳ {local} {pl}-{pv} vs {visitante} ({fecha.day}/{fecha.month} {hora})")
                    with col2:
                        if st.button(f"🗑️", key=f"del_{pid}"):
                            ok, msg = borrar_prediccion(st.session_state.user_id, pid)
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                else:
                    st.write(f"🔒 {local} {pl}-{pv} vs {visitante} ({fecha.day}/{fecha.month} {hora})")

# ════════════════════════════════════════════════════════════════════════════════
# 4. CALENDARIO
elif menu == "📅 Calendario":
    st.header("📅 Calendario")
    
    partidos = get_partidos()
    ahora = ahora_venezuela()
    
    # Agrupar por fase en orden
    orden_fases = ["Grupo A", "Grupo B", "Grupo C", "Grupo D", "Grupo E", "Grupo F", 
                   "Grupo G", "Grupo H", "Grupo I", "Grupo J", "Grupo K", "Grupo L",
                   "16avos de Final", "Octavos de Final", "Cuartos de Final", "Semifinal", "Tercer Lugar", "Final"]
    
    for fase in orden_fases:
        partidos_fase = [p for p in partidos if p[5] == fase]
        if partidos_fase:
            st.subheader(fase)
            for p in partidos_fase:
                pid, local, visitante, gl, gv, fase, fecha, hora = p
                
                if gl is not None:
                    resultado = f"{gl}-{gv}"
                    icon = "✅"
                else:
                    resultado = "vs"
                    fecha_hora = datetime.combine(fecha, datetime.strptime(hora, "%H:%M").time()).replace(tzinfo=VENEZUELA_TZ)
                    icon = "🔴" if fecha_hora <= ahora else "⏳"
                
                st.write(f"{icon} **{fecha.day}/{fecha.month} {hora}** — {local} {resultado} {visitante}")
            st.divider()

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
                if st.button(f"✅", key=f"r_{pid}"):
                    set_resultado(pid, gl_new, gv_new)
                    st.success(f"{local} {gl_new}-{gv_new} {visitante}")
                    st.rerun()
            st.caption(f"{fecha.day}/{fecha.month} {hora} - {fase}")
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
