import streamlit as st
import psycopg2
import psycopg2.pool
import os
import hashlib
from datetime import datetime, date, timedelta

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
    .partido-activo { background-color: #e8f5e9; border-radius: 10px; padding: 10px; margin: 5px 0; border-left: 5px solid #4caf50; }
    .partido-bloqueado { opacity: 0.6; background-color: #ffebee; border-radius: 10px; padding: 10px; margin: 5px 0; border-left: 5px solid #f44336; }
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
    ("Mexico", "Sudafrica", "Grupo A", "2026-06-11", "Ciudad de México", "15:00"),
    ("Corea del Sur", "Republica Checa", "Grupo A", "2026-06-11", "Guadalajara", "18:00"),
    ("Sudafrica", "Republica Checa", "Grupo A", "2026-06-18", "Atlanta", "14:00"),
    ("Mexico", "Corea del Sur", "Grupo A", "2026-06-18", "Guadalajara", "20:00"),
    ("Mexico", "Republica Checa", "Grupo A", "2026-06-24", "Ciudad de México", "16:00"),
    ("Sudafrica", "Corea del Sur", "Grupo A", "2026-06-24", "Dallas", "19:00"),
    ("Canada", "Bosnia y Herzegovina", "Grupo B", "2026-06-12", "Toronto", "13:00"),
    ("Qatar", "Suiza", "Grupo B", "2026-06-12", "Vancouver", "16:00"),
    ("Bosnia y Herzegovina", "Suiza", "Grupo B", "2026-06-18", "Houston", "18:00"),
    ("Canada", "Qatar", "Grupo B", "2026-06-18", "Toronto", "20:00"),
    ("Canada", "Suiza", "Grupo B", "2026-06-24", "Vancouver", "14:00"),
    ("Bosnia y Herzegovina", "Qatar", "Grupo B", "2026-06-24", "Kansas City", "17:00"),
    ("Brasil", "Haiti", "Grupo C", "2026-06-12", "Los Angeles", "12:00"),
    ("Marruecos", "Escocia", "Grupo C", "2026-06-12", "Nueva York", "15:00"),
    ("Brasil", "Marruecos", "Grupo C", "2026-06-19", "Los Angeles", "14:00"),
    ("Escocia", "Haiti", "Grupo C", "2026-06-19", "Philadelphia", "17:00"),
    ("Brasil", "Escocia", "Grupo C", "2026-06-25", "San Francisco", "13:00"),
    ("Haiti", "Marruecos", "Grupo C", "2026-06-25", "Miami", "16:00"),
    ("Estados Unidos", "Paraguay", "Grupo D", "2026-06-13", "Dallas", "15:00"),
    ("Australia", "Turquia", "Grupo D", "2026-06-13", "Kansas City", "18:00"),
    ("Estados Unidos", "Australia", "Grupo D", "2026-06-19", "New York", "14:00"),
    ("Paraguay", "Turquia", "Grupo D", "2026-06-19", "Houston", "20:00"),
    ("Estados Unidos", "Turquia", "Grupo D", "2026-06-25", "Miami", "16:00"),
    ("Australia", "Paraguay", "Grupo D", "2026-06-25", "Seattle", "19:00"),
    ("Alemania", "Costa de Marfil", "Grupo E", "2026-06-13", "Philadelphia", "13:00"),
    ("Ecuador", "Curazao", "Grupo E", "2026-06-13", "Boston", "16:00"),
    ("Alemania", "Ecuador", "Grupo E", "2026-06-20", "Atlanta", "15:00"),
    ("Costa de Marfil", "Curazao", "Grupo E", "2026-06-20", "Dallas", "18:00"),
    ("Alemania", "Curazao", "Grupo E", "2026-06-26", "Nueva York", "14:00"),
    ("Ecuador", "Costa de Marfil", "Grupo E", "2026-06-26", "Houston", "17:00"),
    ("Japon", "Peru", "Grupo F", "2026-06-14", "Seattle", "12:00"),
    ("Arabia Saudi", "Rumania", "Grupo F", "2026-06-14", "Miami", "15:00"),
    ("Japon", "Arabia Saudi", "Grupo F", "2026-06-20", "Los Angeles", "14:00"),
    ("Peru", "Rumania", "Grupo F", "2026-06-20", "San Francisco", "17:00"),
    ("Japon", "Rumania", "Grupo F", "2026-06-26", "Boston", "13:00"),
    ("Peru", "Arabia Saudi", "Grupo F", "2026-06-26", "Kansas City", "16:00"),
    ("Belgica", "Nueva Zelanda", "Grupo G", "2026-06-14", "Atlanta", "13:00"),
    ("Iran", "Egipto", "Grupo G", "2026-06-14", "Dallas", "16:00"),
    ("Belgica", "Iran", "Grupo G", "2026-06-21", "Nueva York", "15:00"),
    ("Egipto", "Nueva Zelanda", "Grupo G", "2026-06-21", "Miami", "18:00"),
    ("Belgica", "Egipto", "Grupo G", "2026-06-27", "Philadelphia", "14:00"),
    ("Iran", "Nueva Zelanda", "Grupo G", "2026-06-27", "Boston", "17:00"),
    ("Espana", "Cabo Verde", "Grupo H", "2026-06-15", "San Francisco", "12:00"),
    ("Uruguay", "Arabia Saudi", "Grupo H", "2026-06-15", "Seattle", "15:00"),
    ("Espana", "Uruguay", "Grupo H", "2026-06-21", "Los Angeles", "14:00"),
    ("Cabo Verde", "Arabia Saudi", "Grupo H", "2026-06-21", "Guadalajara", "17:00"),
    ("Espana", "Arabia Saudi", "Grupo H", "2026-06-27", "Dallas", "13:00"),
    ("Uruguay", "Cabo Verde", "Grupo H", "2026-06-27", "Montreal", "16:00"),
    ("Francia", "Irak", "Grupo I", "2026-06-15", "Houston", "13:00"),
    ("Senegal", "Noruega", "Grupo I", "2026-06-15", "Kansas City", "16:00"),
    ("Francia", "Senegal", "Grupo I", "2026-06-22", "Miami", "15:00"),
    ("Noruega", "Irak", "Grupo I", "2026-06-22", "Philadelphia", "18:00"),
    ("Francia", "Noruega", "Grupo I", "2026-06-27", "Atlanta", "14:00"),
    ("Irak", "Senegal", "Grupo I", "2026-06-27", "Los Angeles", "17:00"),
    ("Argentina", "Argelia", "Grupo J", "2026-06-16", "Dallas", "15:00"),
    ("Austria", "Chile", "Grupo J", "2026-06-16", "Nueva York", "18:00"),
    ("Argentina", "Austria", "Grupo J", "2026-06-22", "Miami", "14:00"),
    ("Chile", "Argelia", "Grupo J", "2026-06-22", "Boston", "17:00"),
    ("Argentina", "Chile", "Grupo J", "2026-06-28", "Los Angeles", "16:00"),
    ("Argelia", "Austria", "Grupo J", "2026-06-28", "Seattle", "19:00"),
    ("Portugal", "Jamaica", "Grupo K", "2026-06-16", "Boston", "13:00"),
    ("Colombia", "Uzbekistan", "Grupo K", "2026-06-16", "Houston", "16:00"),
    ("Portugal", "Colombia", "Grupo K", "2026-06-23", "Kansas City", "15:00"),
    ("Jamaica", "Uzbekistan", "Grupo K", "2026-06-23", "Atlanta", "18:00"),
    ("Portugal", "Uzbekistan", "Grupo K", "2026-06-28", "Philadelphia", "14:00"),
    ("Colombia", "Jamaica", "Grupo K", "2026-06-28", "Dallas", "17:00"),
    ("Inglaterra", "Ghana", "Grupo L", "2026-06-17", "Nueva York", "15:00"),
    ("Croacia", "Panama", "Grupo L", "2026-06-17", "San Francisco", "18:00"),
    ("Inglaterra", "Croacia", "Grupo L", "2026-06-23", "Philadelphia", "14:00"),
    ("Panama", "Ghana", "Grupo L", "2026-06-23", "Houston", "17:00"),
    ("Inglaterra", "Panama", "Grupo L", "2026-06-28", "Boston", "13:00"),
    ("Ghana", "Croacia", "Grupo L", "2026-06-28", "Kansas City", "16:00"),
]

FASES_ELIMINATORIAS = ["16avos de Final", "Octavos de Final", "Cuartos de Final", "Semifinal", "Tercer lugar", "Final"]

# ─── Pool de conexiones a Neon ─────────────────────────────────────────────────
@st.cache_resource
def get_db_pool():
    """Crea un pool de conexiones reutilizable"""
    return psycopg2.pool.SimpleConnectionPool(1, 10, os.environ["DATABASE_URL"])

def get_connection():
    """Obtiene una conexión del pool"""
    return get_db_pool().getconn()

def return_connection(conn):
    """Devuelve la conexión al pool"""
    if conn:
        get_db_pool().putconn(conn)

# Context manager para manejar conexiones automáticamente
class DBConnection:
    def __enter__(self):
        self.conn = get_connection()
        return self.conn
    def __exit__(self, exc_type, exc_val, exc_tb):
        return_connection(self.conn)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ─── Función para verificar si el partido ya comenzó ───────────────────────────
def partido_ha_comenzado(fecha_partido, hora_partido):
    """Verifica si el partido YA COMENZÓ (no se puede predecir)"""
    try:
        ahora = datetime.now()
        
        if isinstance(fecha_partido, str):
            fecha_hora_partido = datetime.strptime(f"{fecha_partido} {hora_partido}", "%Y-%m-%d %H:%M")
        else:
            fecha_hora_partido = datetime.combine(fecha_partido, datetime.strptime(hora_partido, "%H:%M").time())
        
        return fecha_hora_partido <= ahora
    except Exception as e:
        print(f"Error en partido_ha_comenzado: {e}")
        return True

# ─── Crear tablas ───────────────────────────────────────────────────────────────
def init_db():
    with DBConnection() as conn:
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
                hora VARCHAR(10) DEFAULT '15:00',
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
                creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(jugador_id, partido_id)
            );
        """)
        
        # Migraciones
        cur.execute("ALTER TABLE partidos ADD COLUMN IF NOT EXISTS precargado BOOLEAN DEFAULT FALSE;")
        cur.execute("ALTER TABLE partidos ADD COLUMN IF NOT EXISTS sede VARCHAR(50);")
        cur.execute("ALTER TABLE partidos ADD COLUMN IF NOT EXISTS hora VARCHAR(10) DEFAULT '15:00';")
        cur.execute("ALTER TABLE predicciones ADD COLUMN IF NOT EXISTS creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")
        cur.execute("ALTER TABLE predicciones ADD COLUMN IF NOT EXISTS puntos INTEGER DEFAULT 0;")
        
        # Precargar calendario
        cur.execute("SELECT COUNT(*) FROM partidos WHERE precargado = TRUE")
        count = cur.fetchone()[0]
        if count == 0:
            for local, visitante, fase, fecha_str, sede, hora in CALENDARIO_GRUPOS:
                cur.execute("""
                    INSERT INTO partidos (equipo_local, equipo_visitante, fase, fecha, hora, sede, precargado)
                    VALUES (%s, %s, %s, %s, %s, %s, TRUE)
                    ON CONFLICT DO NOTHING
                """, (local, visitante, fase, fecha_str, hora, sede))
        
        conn.commit()
        cur.close()

# ─── Funciones de consulta ─────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_todos_jugadores():
    with DBConnection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, nombre, email, registrado_en FROM jugadores ORDER BY registrado_en DESC")
        rows = cur.fetchall()
        cur.close()
        return rows

@st.cache_data(ttl=300)
def get_partidos():
    with DBConnection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, equipo_local, equipo_visitante, goles_local, goles_visitante, fase, fecha, hora, sede FROM partidos ORDER BY fecha, hora, id")
        rows = cur.fetchall()
        cur.close()
        return rows

@st.cache_data(ttl=300)
def get_tabla_posiciones():
    with DBConnection() as conn:
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
    with DBConnection() as conn:
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
        cur.close()
        return rows

def get_prediccion_existente(jugador_id, partido_id):
    with DBConnection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT pred_local, pred_visitante FROM predicciones WHERE jugador_id=%s AND partido_id=%s",
                    (jugador_id, partido_id))
        row = cur.fetchone()
        cur.close()
        return row

# ─── Funciones de escritura ────────────────────────────────────────────────────
def registrar_jugador(nombre, email, password):
    try:
        with DBConnection() as conn:
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
    with DBConnection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, nombre, es_admin FROM jugadores WHERE email=%s AND password_hash=%s",
            (email, hash_password(password))
        )
        row = cur.fetchone()
        cur.close()
        return row

def save_prediccion(jugador_id, partido_id, pred_local, pred_visitante):
    try:
        with DBConnection() as conn:
            cur = conn.cursor()
            
            cur.execute("SELECT fecha, hora, goles_local FROM partidos WHERE id = %s", (partido_id,))
            resultado = cur.fetchone()
            
            if not resultado:
                cur.close()
                return False, "Partido no encontrado"
            
            fecha, hora, goles = resultado
            
            if goles is not None:
                cur.close()
                return False, "❌ El partido ya tiene resultado ingresado"
            
            if partido_ha_comenzado(fecha, hora):
                cur.close()
                return False, "⛔ NO se puede predecir: el partido YA COMENZÓ"
            
            cur.execute("""
                INSERT INTO predicciones (jugador_id, partido_id, pred_local, pred_visitante, creado_en)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (jugador_id, partido_id)
                DO UPDATE SET pred_local=EXCLUDED.pred_local, pred_visitante=EXCLUDED.pred_visitante, 
                              puntos=0, creado_en=CURRENT_TIMESTAMP
            """, (jugador_id, partido_id, pred_local, pred_visitante))
            
            conn.commit()
            cur.close()
            st.cache_data.clear()
            return True, "✅ Predicción guardada correctamente"
            
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

def set_resultado(partido_id, goles_local, goles_visitante):
    with DBConnection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE partidos SET goles_local=%s, goles_visitante=%s WHERE id=%s",
                    (goles_local, goles_visitante, partido_id))
        
        cur.execute("SELECT jugador_id, pred_local, pred_visitante FROM predicciones WHERE partido_id=%s", (partido_id,))
        for jugador_id, pl, pv in cur.fetchall():
            puntos = 3 if (pl == goles_local and pv == goles_visitante) else (1 if ((pl > pv and goles_local > goles_visitante) or (pl < pv and goles_local < goles_visitante) or (pl == pv and goles_local == goles_visitante)) else 0)
            cur.execute("UPDATE predicciones SET puntos=%s WHERE partido_id=%s AND jugador_id=%s", 
                       (puntos, partido_id, jugador_id))
        
        conn.commit()
        cur.close()
        st.cache_data.clear()

def add_partido(local, visitante, fase, fecha, hora, sede=""):
    with DBConnection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO partidos (equipo_local, equipo_visitante, fase, fecha, hora, sede) VALUES (%s, %s, %s, %s, %s, %s)",
            (local, visitante, fase, fecha, hora, sede)
        )
        conn.commit()
        cur.close()
        st.cache_data.clear()

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
# 1. TABLA DE POSICIONES
if menu == "🏆 Tabla de Posiciones":
    st.header("🏆 Tabla de Posiciones")
    
    tabla = get_tabla_posiciones()
    
    if not tabla:
        st.info("Aún no hay jugadores registrados.")
    else:
        for i, (jid, nombre, total, exactos, ganadores, total_preds) in enumerate(tabla, 1):
            icono = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
            st.markdown(f"{icono} **{nombre}** — **{total} pts** (🟢{exactos} exactos / 🟡{ganadores} ganador)")
        
        st.caption("🟢 3 puntos = Marcador exacto | 🟡 1 punto = Acertó ganador o empate")

# ════════════════════════════════════════════════════════════════════════════════
# 2. CALENDARIO
elif menu == "📅 Calendario":
    st.header("📅 Calendario del Mundial 2026")
    
    partidos = get_partidos()
    
    for pid, local, visitante, gl, gv, fase, fecha, hora, sede in partidos:
        resultado = f"{gl}-{gv}" if gl is not None else "vs"
        
        if gl is not None:
            estado = "✅ Finalizado"
        elif partido_ha_comenzado(fecha, hora):
            estado = "🔴 En curso"
        else:
            estado = "⏳ Próximo"
        
        st.write(f"{estado} — **{fecha} {hora}** — {local} **{resultado}** {visitante} — *{fase}*")

# ════════════════════════════════════════════════════════════════════════════════
# 3. PREDICCIONES
elif menu == "🎯 Predicciones":
    st.header(f"🎯 Tus Predicciones - {st.session_state.usuario}")
    st.warning("⚠️ Solo puedes predecir ANTES de que el partido comience.")
    
    partidos = get_partidos()
    ahora = datetime.now()
    
    partidos_disponibles = []
    partidos_cerrados = []
    
    for p in partidos:
        pid, local, visitante, gl, gv, fase, fecha, hora, sede = p
        if gl is None:
            if partido_ha_comenzado(fecha, hora):
                partidos_cerrados.append(p)
            else:
                partidos_disponibles.append(p)
    
    if partidos_disponibles:
        st.subheader(f"📝 Partidos disponibles ({len(partidos_disponibles)})")
        
        for partido in partidos_disponibles:
            pid, local, visitante, gl, gv, fase, fecha, hora, sede = partido
            pred = get_prediccion_existente(st.session_state.usuario_id, pid)
            val_l = pred[0] if pred else 0
            val_v = pred[1] if pred else 0
            
            fecha_hora_partido = datetime.combine(fecha, datetime.strptime(hora, "%H:%M").time())
            tiempo_restante = fecha_hora_partido - ahora
            horas_rest = int(tiempo_restante.total_seconds() // 3600)
            mins_rest = int((tiempo_restante.total_seconds() % 3600) // 60)
            
            with st.container():
                st.markdown(f'<div class="partido-activo">', unsafe_allow_html=True)
                col1, col2, col3, col4 = st.columns([2, 1, 2, 2])
                with col1:
                    st.write(f"**{local}**")
                    new_l = st.number_input("", 0, 10, val_l, key=f"l_{pid}", label_visibility="collapsed")
                with col2:
                    st.write("vs")
                with col3:
                    st.write(f"**{visitante}**")
                    new_v = st.number_input("", 0, 10, val_v, key=f"v_{pid}", label_visibility="collapsed")
                with col4:
                    if st.button(f"💾 Guardar", key=f"save_{pid}"):
                        success, msg = save_prediccion(st.session_state.usuario_id, pid, new_l, new_v)
                        if success:
                            st.success(f"{msg}: {local} {new_l}-{new_v} {visitante}")
                            st.rerun()
                        else:
                            st.error(msg)
                
                st.caption(f"📅 {fecha} {hora} - 📍{sede}")
                st.caption(f"⏰ Tiempo restante: {horas_rest}h {mins_rest}m")
                st.markdown('</div>', unsafe_allow_html=True)
                st.divider()
    else:
        st.info("No hay partidos disponibles para predecir.")
    
    if partidos_cerrados:
        st.subheader(f"🔒 Partidos cerrados ({len(partidos_cerrados)})")
        for partido in partidos_cerrados:
            pid, local, visitante, gl, gv, fase, fecha, hora, sede = partido
            pred = get_prediccion_existente(st.session_state.usuario_id, pid)
            if pred:
                val_l, val_v = pred
                st.markdown(f'<div class="partido-bloqueado">🔒 {local} {val_l}-{val_v} vs {visitante}<br>⛔ Partido ya comenzó</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="partido-bloqueado">❌ {local} vs {visitante}<br>⛔ No realizaste predicción a tiempo</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
# 4. MIS RESULTADOS
elif menu == "📊 Mis resultados":
    st.header(f"📊 Tus Resultados - {st.session_state.usuario}")
    
    preds = get_predicciones_jugador(st.session_state.usuario_id)
    
    if not preds:
        st.info("Aún no tienes predicciones.")
    else:
        total_pts = sum(p[9] for p in preds)
        exactos = sum(1 for p in preds if p[9] == 3)
        ganadores = sum(1 for p in preds if p[9] == 1)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("🏆 Puntos", total_pts)
        col2.metric("🟢 Exactos", exactos)
        col3.metric("🟡 Ganadores", ganadores)
        
        st.divider()
        
        for p in preds:
            pid, local, visitante, gl, gv, fase, fecha, hora, pl, pv, pts = p
            if gl is not None:
                icon = "🟢" if pts == 3 else "🟡" if pts == 1 else "⚫"
                st.write(f"{icon} **{local}** {pl}-{pv} vs **{visitante}** → Real: {gl}-{gv} → **{pts} pts**")
            else:
                st.write(f"⏳ **{local}** {pl}-{pv} vs **{visitante}** ({fecha} {hora})")

# ════════════════════════════════════════════════════════════════════════════════
# 5. JUGADORES
elif menu == "👥 Jugadores":
    st.header("👥 Todos los Jugadores")
    
    tabla = get_tabla_posiciones()
    tabla_dict = {nombre: (total, exactos, ganadores) for _, nombre, total, exactos, ganadores, _ in tabla}
    
    for jid, nombre, email, reg in get_todos_jugadores():
        total, exactos, ganadores = tabla_dict.get(nombre, (0, 0, 0))
        st.write(f"👤 **{nombre}** — {total} pts (🟢{exactos} exactos / 🟡{ganadores} ganador)")

# ════════════════════════════════════════════════════════════════════════════════
# ADMIN: RESULTADOS
elif menu == "⚽ Resultados" and st.session_state.es_admin:
    st.header("⚽ Ingresar Resultados")
    
    partidos = get_partidos()
    pendientes = [p for p in partidos if p[3] is None]
    
    if not pendientes:
        st.success("✅ Todos los partidos ya tienen resultado")
    else:
        for pid, local, visitante, gl, gv, fase, fecha, hora, sede in pendientes:
            st.markdown(f"**{fase}** - {fecha} {hora} - {sede}")
            col1, col2 = st.columns(2)
            with col1:
                gl_new = st.number_input(f"Goles {local}", 0, 20, 0, key=f"gl_{pid}")
            with col2:
                gv_new = st.number_input(f"Goles {visitante}", 0, 20, 0, key=f"gv_{pid}")
            if st.button(f"✅ Guardar resultado", key=f"res_{pid}"):
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
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            fecha = st.date_input("Fecha")
        with col_f2:
            hora = st.text_input("Hora (HH:MM)", "15:00")
        sede = st.text_input("Sede/Ciudad")
        
        if st.form_submit_button("Agregar Partido"):
            if local and visitante and local != visitante:
                add_partido(local, visitante, fase, fecha, hora, sede)
                st.success(f"✅ Partido agregado: {local} vs {visitante}")
                st.rerun()
            else:
                st.error("Completa todos los campos correctamente")
