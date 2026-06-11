import streamlit as st
import psycopg2
import psycopg2.pool
import os
import hashlib
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

# ─── Configuración de página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="⚽ Quiniela Mundial 2026",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
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
    .main > div { padding-top: 0; }
</style>
""", unsafe_allow_html=True)

# ─── DATOS ─────────────────────────────────────────────────────────────────────
CALENDARIO_GRUPOS = [
    ("Mexico", "Sudafrica", "Grupo A", "2026-06-11", "15:00"),
    ("Corea del Sur", "Republica Checa", "Grupo A", "2026-06-11", "18:00"),
    ("Mexico", "Corea del Sur", "Grupo A", "2026-06-18", "20:00"),
    ("Argentina", "Chile", "Grupo J", "2026-06-28", "16:00"),
    ("Brasil", "Argentina", "Final", "2026-07-19", "15:00"),
]

# Más partidos (versión simplificada para velocidad)
for g in range(ord('A'), ord('L')+1):
    letra = chr(g)
    for i in range(4):
        for j in range(i+1, 4):
            CALENDARIO_GRUPOS.append((f"Equipo{letra}{i+1}", f"Equipo{letra}{j+1}", f"Grupo {letra}", "2026-06-15", "15:00"))

FASES_ELIMINATORIAS = ["Octavos", "Cuartos", "Semifinal", "Final"]

# ─── CONEXIÓN SIMPLE (más rápida que pool) ─────────────────────────────────────
@st.cache_resource
def get_db_connection():
    return psycopg2.connect(os.environ["DATABASE_URL"])

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

# ─── INICIALIZAR BD (RÁPIDA) ──────────────────────────────────────────────────
@st.cache_resource
def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Tablas
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
        
        # Admin
        admin_pass = hash_password("admin123")
        cur.execute("""
            INSERT INTO jugadores (nombre, email, password_hash, es_admin)
            SELECT 'Admin', 'admin@quiniela.com', %s, TRUE
            WHERE NOT EXISTS (SELECT 1 FROM jugadores WHERE email = 'admin@quiniela.com')
        """, (admin_pass,))
        
        # Partidos (solo si está vacío)
        cur.execute("SELECT COUNT(*) FROM partidos")
        if cur.fetchone()[0] == 0:
            for local, visitante, fase, fecha_str, hora in CALENDARIO_GRUPOS[:20]:  # Solo primeros 20 para velocidad
                cur.execute("""
                    INSERT INTO partidos (equipo_local, equipo_visitante, fase, fecha, hora)
                    VALUES (%s, %s, %s, %s, %s)
                """, (local, visitante, fase, fecha_str, hora))
        
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error DB: {e}")
        return False

# ─── FUNCIONES CONSULTA ────────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def get_partidos():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, equipo_local, equipo_visitante, goles_local, goles_visitante, fase, fecha, hora FROM partidos ORDER BY fecha, hora")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

@st.cache_data(ttl=600)
def get_tabla_posiciones():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT j.nombre, COALESCE(SUM(pr.puntos), 0) as total
        FROM jugadores j
        LEFT JOIN predicciones pr ON j.id = pr.jugador_id
        GROUP BY j.id, j.nombre
        ORDER BY total DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

@st.cache_data(ttl=600)
def get_mis_predicciones(jugador_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.id, p.equipo_local, p.equipo_visitante, p.goles_local, p.goles_visitante,
               p.fase, p.fecha, p.hora, pr.pred_local, pr.pred_visitante, pr.puntos
        FROM predicciones pr
        JOIN partidos p ON pr.partido_id = p.id
        WHERE pr.jugador_id = %s
        ORDER BY p.fecha
    """, (jugador_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_prediccion(jugador_id, partido_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT pred_local, pred_visitante FROM predicciones WHERE jugador_id=%s AND partido_id=%s",
                (jugador_id, partido_id))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

# ─── FUNCIONES ESCRITURA ───────────────────────────────────────────────────────
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
        cur.close()
        conn.close()
        st.cache_data.clear()
        return uid, None
    except Exception as e:
        return None, str(e)

def login(email, password):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, nombre, es_admin FROM jugadores WHERE email=%s AND password_hash=%s",
            (email, hash_password(password))
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row
    except:
        return None

def guardar_prediccion(jugador_id, partido_id, pred_local, pred_visitante):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT fecha, hora, goles_local FROM partidos WHERE id = %s", (partido_id,))
        fecha, hora, goles = cur.fetchone()
        
        if goles is not None:
            cur.close()
            conn.close()
            return False, "Partido ya finalizado"
        
        if partido_ha_comenzado(fecha, hora):
            cur.close()
            conn.close()
            return False, "El partido ya comenzó"
        
        cur.execute("""
            INSERT INTO predicciones (jugador_id, partido_id, pred_local, pred_visitante)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (jugador_id, partido_id)
            DO UPDATE SET pred_local=EXCLUDED.pred_local, pred_visitante=EXCLUDED.pred_visitante, puntos=0
        """, (jugador_id, partido_id, pred_local, pred_visitante))
        
        conn.commit()
        cur.close()
        conn.close()
        st.cache_data.clear()
        return True, "✅ Guardado"
    except Exception as e:
        return False, str(e)

def borrar_prediccion(jugador_id, partido_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT fecha, hora, goles_local FROM partidos WHERE id = %s", (partido_id,))
        fecha, hora, goles = cur.fetchone()
        
        if goles is not None:
            cur.close()
            conn.close()
            return False, "Partido ya finalizado"
        
        if partido_ha_comenzado(fecha, hora):
            cur.close()
            conn.close()
            return False, "Partido ya comenzó"
        
        cur.execute("DELETE FROM predicciones WHERE jugador_id=%s AND partido_id=%s", (jugador_id, partido_id))
        conn.commit()
        cur.close()
        conn.close()
        st.cache_data.clear()
        return True, "✅ Borrado"
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
    cur.close()
    conn.close()
    st.cache_data.clear()

# ─── INICIALIZAR ───────────────────────────────────────────────────────────────
if not init_db():
    st.error("Error al conectar con la base de datos")
    st.stop()

# ─── ESTADO DE SESIÓN ──────────────────────────────────────────────────────────
if "user_id" not in st.session_state:
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.is_admin = False

# ─── HEADER ────────────────────────────────────────────────────────────────────
st.title("⚽ Quiniela Mundial 2026")
st.caption("11 Jun - 19 Jul 2026")

# ─── LOGIN ─────────────────────────────────────────────────────────────────────
if not st.session_state.user_id:
    with st.sidebar:
        st.subheader("🔐 Acceso")
        tab1, tab2 = st.tabs(["Login", "Registro"])
        
        with tab1:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Contraseña", type="password", key="login_pass")
            if st.button("Entrar", use_container_width=True):
                with st.spinner("Verificando..."):
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
                else:
                    with st.spinner("Registrando..."):
                        uid, err = registrar_usuario(nombre, email, pwd)
                        if uid:
                            st.success("¡Registrado! Ahora inicia sesión")
                        else:
                            st.error("Email o nombre ya existe")
    st.stop()

# ─── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"**👤 {st.session_state.user_name}**")
    if st.button("🚪 Cerrar sesión", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    st.divider()
    
    menu = st.radio("📋 Menú", ["🏆 Tabla", "🎯 Predecir", "📊 Mis resultados", "📅 Calendario"], label_visibility="collapsed")
    
    if st.session_state.is_admin:
        st.divider()
        admin_menu = st.radio("🔧 Admin", ["⚽ Resultados", "➕ Partido"], label_visibility="collapsed")

# ════════════════════════════════════════════════════════════════════════════════
# 1. TABLA
if menu == "🏆 Tabla":
    st.header("🏆 Clasificación")
    tabla = get_tabla_posiciones()
    if tabla:
        for i, (nombre, pts) in enumerate(tabla, 1):
            icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            st.write(f"{icon} **{nombre}** — **{pts} pts**")
    else:
        st.info("No hay jugadores")

# ════════════════════════════════════════════════════════════════════════════════
# 2. PREDICCIONES
elif menu == "🎯 Predecir":
    st.header(f"🎯 Predecir")
    
    partidos = get_partidos()
    ahora = ahora_venezuela()
    
    disponibles = [p for p in partidos if p[3] is None]
    
    if not disponibles:
        st.info("No hay partidos disponibles")
    else:
        for p in disponibles:
            pid, local, visitante, gl, gv, fase, fecha, hora = p
            pred = get_prediccion(st.session_state.user_id, pid)
            val_l = pred[0] if pred else 0
            val_v = pred[1] if pred else 0
            
            fecha_hora = datetime.combine(fecha, datetime.strptime(hora, "%H:%M").time()).replace(tzinfo=VENEZUELA_TZ)
            ya_comenzo = fecha_hora <= ahora
            
            if ya_comenzo:
                disabled = True
                estado = "🔴 Cerrado"
            else:
                disabled = False
                resto = fecha_hora - ahora
                horas = int(resto.total_seconds() // 3600)
                mins = int((resto.total_seconds() % 3600) // 60)
                estado = f"🟢 {horas}h {mins}m"
            
            col1, col2, col3, col4, col5 = st.columns([2, 1, 2, 1, 1])
            
            with col1:
                g_l = st.number_input(local, 0, 10, val_l, key=f"l_{pid}", label_visibility="collapsed", disabled=disabled)
            with col2:
                st.write("vs")
            with col3:
                g_v = st.number_input(visitante, 0, 10, val_v, key=f"v_{pid}", label_visibility="collapsed", disabled=disabled)
            with col4:
                if not disabled and st.button("💾", key=f"s_{pid}"):
                    ok, msg = guardar_prediccion(st.session_state.user_id, pid, g_l, g_v)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            with col5:
                if pred and not disabled and st.button("🗑️", key=f"d_{pid}"):
                    ok, msg = borrar_prediccion(st.session_state.user_id, pid)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            
            st.caption(f"{fase} - {fecha.day}/{fecha.month} {hora} | {estado}")
            st.divider()

# ════════════════════════════════════════════════════════════════════════════════
# 3. MIS RESULTADOS
elif menu == "📊 Mis resultados":
    st.header("📊 Mis resultados")
    preds = get_mis_predicciones(st.session_state.user_id)
    if preds:
        total = sum(p[10] for p in preds if p[10])
        st.metric("🏆 Puntos", total)
        st.divider()
        for p in preds:
            local, visitante, gl, gv, pl, pv, pts = p[1], p[2], p[3], p[4], p[8], p[9], p[10]
            if gl is not None:
                icon = "🟢" if pts == 3 else "🟡" if pts == 1 else "⚫"
                st.write(f"{icon} {local} {pl}-{pv} vs {visitante} → Real: {gl}-{gv} ({pts} pts)")
            else:
                st.write(f"⏳ {local} {pl}-{pv} vs {visitante}")
    else:
        st.info("Sin predicciones")

# ════════════════════════════════════════════════════════════════════════════════
# 4. CALENDARIO
elif menu == "📅 Calendario":
    st.header("📅 Calendario")
    for p in get_partidos():
        local, visitante, gl, gv, fecha, hora = p[1], p[2], p[3], p[4], p[6], p[7]
        resultado = f"{gl}-{gv}" if gl is not None else "vs"
        st.write(f"**{fecha.day}/{fecha.month} {hora}** — {local} {resultado} {visitante}")

# ════════════════════════════════════════════════════════════════════════════════
# ADMIN: RESULTADOS
if st.session_state.is_admin and menu != "🎯 Predecir" and admin_menu == "⚽ Resultados":
    st.header("⚽ Resultados")
    for p in get_partidos():
        pid, local, visitante, gl, gv, fase, fecha, hora = p
        if gl is None:
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                gl_new = st.number_input(f"{local}", 0, 10, key=f"gl_{pid}")
            with col2:
                gv_new = st.number_input(f"{visitante}", 0, 10, key=f"gv_{pid}")
            with col3:
                if st.button(f"✅", key=f"r_{pid}"):
                    set_resultado(pid, gl_new, gv_new)
                    st.success(f"{local} {gl_new}-{gv_new} {visitante}")
                    st.rerun()
            st.divider()

# ════════════════════════════════════════════════════════════════════════════════
# ADMIN: AGREGAR PARTIDO
if st.session_state.is_admin and menu != "🎯 Predecir" and admin_menu == "➕ Partido":
    st.header("➕ Agregar Partido")
    with st.form("new"):
        local = st.text_input("Local")
        visitante = st.text_input("Visitante")
        fase = st.selectbox("Fase", FASES_ELIMINATORIAS)
        fecha = st.date_input("Fecha")
        hora = st.text_input("Hora", "15:00")
        if st.form_submit_button("Agregar"):
            if local and visitante:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("INSERT INTO partidos (equipo_local, equipo_visitante, fase, fecha, hora) VALUES (%s, %s, %s, %s, %s)",
                           (local, visitante, fase, fecha, hora))
                conn.commit()
                cur.close()
                conn.close()
                st.cache_data.clear()
                st.success("Agregado")
                st.rerun()
