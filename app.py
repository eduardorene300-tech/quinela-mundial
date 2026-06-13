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

CALENDARIO_GRUPOS = [
    # GRUPO A: Mexico, Sudafrica, Corea del Sur, Republica Checa
    ("Mexico", "Sudafrica", "Grupo A", "2026-06-11", "13:00"),
    ("Corea del Sur", "Republica Checa", "Grupo A", "2026-06-11", "20:00"),
    ("Republica Checa", "Sudafrica", "Grupo A", "2026-06-18", "12:00"),
    ("Mexico", "Corea del Sur", "Grupo A", "2026-06-18", "19:00"),
    ("Republica Checa", "Mexico", "Grupo A", "2026-06-24", "19:00"),
    ("Sudafrica", "Corea del Sur", "Grupo A", "2026-06-24", "19:00"),

    # GRUPO B: Canada, Bosnia y Herzegovina, Qatar, Suiza
    ("Canada", "Bosnia y Herzegovina", "Grupo B", "2026-06-12", "15:00"),
    ("Qatar", "Suiza", "Grupo B", "2026-06-13", "12:00"),
    ("Canada", "Qatar", "Grupo B", "2026-06-18", "22:00"),
    ("Bosnia y Herzegovina", "Suiza", "Grupo B", "2026-06-18", "19:00"),
    ("Suiza", "Canada", "Grupo B", "2026-06-24", "19:00"),
    ("Bosnia y Herzegovina", "Qatar", "Grupo B", "2026-06-24", "19:00"),

    # GRUPO C: Brasil, Marruecos, Haiti, Escocia
    ("Brasil", "Marruecos", "Grupo C", "2026-06-13", "18:00"),
    ("Haiti", "Escocia", "Grupo C", "2026-06-13", "21:00"),
    ("Escocia", "Marruecos", "Grupo C", "2026-06-19", "18:00"),
    ("Brasil", "Haiti", "Grupo C", "2026-06-19", "20:30"),
    ("Escocia", "Brasil", "Grupo C", "2026-06-24", "22:00"),
    ("Marruecos", "Haiti", "Grupo C", "2026-06-24", "22:00"),

    # GRUPO D: Estados Unidos, Paraguay, Australia, Turquia
    ("Estados Unidos", "Paraguay", "Grupo D", "2026-06-12", "18:00"),
    ("Australia", "Turquia", "Grupo D", "2026-06-13", "18:00"),
    ("Estados Unidos", "Australia", "Grupo D", "2026-06-19", "19:00"),
    ("Turquia", "Paraguay", "Grupo D", "2026-06-19", "21:00"),
    ("Turquia", "Estados Unidos", "Grupo D", "2026-06-25", "19:00"),
    ("Paraguay", "Australia", "Grupo D", "2026-06-25", "19:00"),

    # GRUPO E: Alemania, Curazao, Costa de Marfil, Ecuador
    ("Alemania", "Curazao", "Grupo E", "2026-06-14", "12:00"),
    ("Costa de Marfil", "Ecuador", "Grupo E", "2026-06-14", "19:00"),
    ("Alemania", "Costa de Marfil", "Grupo E", "2026-06-20", "16:00"),
    ("Ecuador", "Curazao", "Grupo E", "2026-06-20", "19:00"),
    ("Ecuador", "Alemania", "Grupo E", "2026-06-25", "20:00"),
    ("Curazao", "Costa de Marfil", "Grupo E", "2026-06-25", "20:00"),

    # GRUPO F: Paises Bajos, Japon, Suecia, Tunisia
    ("Paises Bajos", "Japon", "Grupo F", "2026-06-14", "15:00"),
    ("Suecia", "Tunisia", "Grupo F", "2026-06-14", "20:00"),
    ("Paises Bajos", "Suecia", "Grupo F", "2026-06-20", "12:00"),
    ("Tunisia", "Japon", "Grupo F", "2026-06-20", "22:00"),
    ("Japon", "Suecia", "Grupo F", "2026-06-25", "23:00"),
    ("Tunisia", "Paises Bajos", "Grupo F", "2026-06-25", "23:00"),

    # GRUPO G: Belgica, Egipto, Iran, Nueva Zelanda
    ("Belgica", "Egipto", "Grupo G", "2026-06-15", "19:00"),
    ("Iran", "Nueva Zelanda", "Grupo G", "2026-06-15", "19:00"),
    ("Belgica", "Iran", "Grupo G", "2026-06-21", "19:00"),
    ("Nueva Zelanda", "Egipto", "Grupo G", "2026-06-21", "19:00"),
    ("Belgica", "Nueva Zelanda", "Grupo G", "2026-06-27", "00:00"),
    ("Egipto", "Iran", "Grupo G", "2026-06-27", "00:00"),

    # GRUPO H: Espana, Cabo Verde, Arabia Saudi, Uruguay
    ("Espana", "Cabo Verde", "Grupo H", "2026-06-15", "12:00"),
    ("Arabia Saudi", "Uruguay", "Grupo H", "2026-06-15", "22:00"),
    ("Espana", "Arabia Saudi", "Grupo H", "2026-06-21", "12:00"),
    ("Uruguay", "Cabo Verde", "Grupo H", "2026-06-21", "22:00"),
    ("Uruguay", "Espana", "Grupo H", "2026-06-26", "00:00"),
    ("Cabo Verde", "Arabia Saudi", "Grupo H", "2026-06-26", "19:00"),

    # GRUPO I: Francia, Senegal, Irak, Noruega
    ("Francia", "Senegal", "Grupo I", "2026-06-16", "15:00"),
    ("Irak", "Noruega", "Grupo I", "2026-06-16", "18:00"),
    ("Francia", "Irak", "Grupo I", "2026-06-22", "17:00"),
    ("Noruega", "Senegal", "Grupo I", "2026-06-22", "20:00"),
    ("Noruega", "Francia", "Grupo I", "2026-06-26", "15:00"),
    ("Senegal", "Irak", "Grupo I", "2026-06-26", "15:00"),

    # GRUPO J: Argentina, Argelia, Austria, Jordan
    ("Argentina", "Argelia", "Grupo J", "2026-06-16", "20:00"),
    ("Austria", "Jordan", "Grupo J", "2026-06-16", "21:00"),
    ("Argentina", "Austria", "Grupo J", "2026-06-22", "12:00"),
    ("Jordan", "Argelia", "Grupo J", "2026-06-22", "21:00"),
    ("Jordan", "Argentina", "Grupo J", "2026-06-27", "00:00"),
    ("Argelia", "Austria", "Grupo J", "2026-06-27", "00:00"),

    # GRUPO K: Portugal, Congo DR, Uzbekistan, Colombia
    ("Portugal", "Congo DR", "Grupo K", "2026-06-17", "12:00"),
    ("Uzbekistan", "Colombia", "Grupo K", "2026-06-17", "20:00"),
    ("Portugal", "Uzbekistan", "Grupo K", "2026-06-23", "12:00"),
    ("Colombia", "Congo DR", "Grupo K", "2026-06-23", "20:00"),
    ("Colombia", "Portugal", "Grupo K", "2026-06-27", "00:00"),
    ("Congo DR", "Uzbekistan", "Grupo K", "2026-06-27", "00:00"),

    # GRUPO L: Inglaterra, Croacia, Ghana, Panama
    ("Inglaterra", "Croacia", "Grupo L", "2026-06-17", "15:00"),
    ("Ghana", "Panama", "Grupo L", "2026-06-17", "19:00"),
    ("Inglaterra", "Ghana", "Grupo L", "2026-06-23", "16:00"),
    ("Panama", "Croacia", "Grupo L", "2026-06-23", "19:00"),
    ("Panama", "Inglaterra", "Grupo L", "2026-06-28", "13:00"),
    ("Croacia", "Ghana", "Grupo L", "2026-06-28", "16:00"),
]

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

CALENDARIO_CUARTOS = [
    ("Ganador Octavos 1", "Ganador Octavos 2", "Cuartos de Final", "2026-07-11", "12:00"),
    ("Ganador Octavos 3", "Ganador Octavos 4", "Cuartos de Final", "2026-07-11", "15:00"),
    ("Ganador Octavos 5", "Ganador Octavos 6", "Cuartos de Final", "2026-07-12", "12:00"),
    ("Ganador Octavos 7", "Ganador Octavos 8", "Cuartos de Final", "2026-07-12", "15:00"),
]

CALENDARIO_SEMIFINALES = [
    ("Ganador Cuartos 1", "Ganador Cuartos 2", "Semifinal", "2026-07-14", "15:00"),
    ("Ganador Cuartos 3", "Ganador Cuartos 4", "Semifinal", "2026-07-15", "15:00"),
]

CALENDARIO_TERCER_LUGAR = [
    ("Perdedor Semifinal 1", "Perdedor Semifinal 2", "Tercer Lugar", "2026-07-18", "15:00"),
]

CALENDARIO_FINAL = [
    ("Ganador Semifinal 1", "Ganador Semifinal 2", "Final", "2026-07-19", "15:00"),
]

CALENDARIO_ELIMINACION = (
    CALENDARIO_16AVOS + CALENDARIO_OCTAVOS + CALENDARIO_CUARTOS +
    CALENDARIO_SEMIFINALES + CALENDARIO_TERCER_LUGAR + CALENDARIO_FINAL
)

TODOS_LOS_PARTIDOS = CALENDARIO_GRUPOS + CALENDARIO_ELIMINACION

FASES_ELIMINATORIAS = [
    "16avos de Final", "Octavos de Final", "Cuartos de Final",
    "Semifinal", "Tercer Lugar", "Final"
]

ORDEN_FASES = [
    "Grupo A", "Grupo B", "Grupo C", "Grupo D", "Grupo E", "Grupo F",
    "Grupo G", "Grupo H", "Grupo I", "Grupo J", "Grupo K", "Grupo L",
    "16avos de Final", "Octavos de Final", "Cuartos de Final",
    "Semifinal", "Tercer Lugar", "Final"
]

# ════════════════════════════════════════════════════════════════════════════════
# CONEXIÓN A LA BASE DE DATOS — reconexión automática ante caídas SSL
# ════════════════════════════════════════════════════════════════════════════════

def _nueva_conexion():
    return psycopg2.connect(os.environ["DATABASE_URL"])

def _conn_valida(conn):
    """Comprueba si la conexión sigue viva sin lanzar excepción al usuario."""
    try:
        if conn is None or conn.closed:
            return False
        conn.cursor().execute("SELECT 1")
        return True
    except Exception:
        return False

# Conexión única reutilizable por sesión de Streamlit
if "db_conn" not in st.session_state:
    st.session_state.db_conn = _nueva_conexion()

def get_conn():
    """Devuelve una conexión válida, reconectando si SSL la cerró."""
    conn = st.session_state.db_conn
    if not _conn_valida(conn):
        try:
            conn.close()
        except Exception:
            pass
        conn = _nueva_conexion()
        st.session_state.db_conn = conn
    return conn

def ejecutar_consulta(sql, params=None):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    except Exception:
        # Reconectar y reintentar una vez
        conn = _nueva_conexion()
        st.session_state.db_conn = conn
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

def ejecutar_comando(sql, params=None):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()
        return True, None
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        # Reconectar y reintentar una vez
        try:
            conn = _nueva_conexion()
            st.session_state.db_conn = conn
            with conn.cursor() as cur:
                cur.execute(sql, params)
            conn.commit()
            return True, None
        except Exception as e2:
            return False, str(e2)

def ejecutar_comandos_batch(sqls_params):
    """Ejecuta múltiples comandos en una sola transacción."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            for sql, params in sqls_params:
                cur.execute(sql, params)
        conn.commit()
        return True, None
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        # Reconectar y reintentar una vez
        try:
            conn = _nueva_conexion()
            st.session_state.db_conn = conn
            with conn.cursor() as cur:
                for sql, params in sqls_params:
                    cur.execute(sql, params)
            conn.commit()
            return True, None
        except Exception as e2:
            return False, str(e2)

# ════════════════════════════════════════════════════════════════════════════════
# UTILIDADES
# ════════════════════════════════════════════════════════════════════════════════

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def partido_ha_comenzado(fecha_partido, hora_partido):
    try:
        ahora = ahora_venezuela()
        if isinstance(fecha_partido, str):
            fecha_hora = datetime.strptime(f"{fecha_partido} {hora_partido}", "%Y-%m-%d %H:%M")
        else:
            fecha_hora = datetime.combine(fecha_partido, datetime.strptime(hora_partido, "%H:%M").time())
        return fecha_hora.replace(tzinfo=VENEZUELA_TZ) <= ahora
    except Exception:
        return False

def tiempo_restante(fecha_partido, hora_partido):
    """Devuelve (ya_comenzo, texto)."""
    try:
        ahora = ahora_venezuela()
        if isinstance(fecha_partido, str):
            fecha_hora = datetime.strptime(f"{fecha_partido} {hora_partido}", "%Y-%m-%d %H:%M")
        else:
            fecha_hora = datetime.combine(fecha_partido, datetime.strptime(hora_partido, "%H:%M").time())
        fecha_hora = fecha_hora.replace(tzinfo=VENEZUELA_TZ)
        if fecha_hora <= ahora:
            return True, "🔴 Cerrado"
        resto = fecha_hora - ahora
        horas = int(resto.total_seconds() // 3600)
        mins = int((resto.total_seconds() % 3600) // 60)
        return False, f"🟢 {horas}h {mins}m"
    except Exception:
        return False, "?"

# ════════════════════════════════════════════════════════════════════════════════
# INICIALIZACIÓN DE BD — solo una vez
# ════════════════════════════════════════════════════════════════════════════════

def init_db():
    conn = get_conn()
    with conn.cursor() as cur:
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

        # ── Sincronizar partidos del código con la BD ──────────────────────
        # 1 sola query para leer todo, luego inserts/updates solo si hay diferencia.
        cur.execute("""
            SELECT equipo_local, equipo_visitante, fase, fecha::text, hora, id
            FROM partidos WHERE fase NOT LIKE '%Final%' OR fase LIKE 'Grupo%'
                             OR fase IN ('16avos de Final','Octavos de Final',
                                         'Cuartos de Final','Semifinal',
                                         'Tercer Lugar','Final')
        """)
        bd = {(r[0], r[1], r[2]): (r[3], r[4], r[5]) for r in cur.fetchall()}

        for local, visitante, fase, fecha_str, hora in TODOS_LOS_PARTIDOS:
            key = (local, visitante, fase)
            if key not in bd:
                cur.execute("""
                    INSERT INTO partidos (equipo_local, equipo_visitante, fase, fecha, hora)
                    VALUES (%s, %s, %s, %s, %s)
                """, (local, visitante, fase, fecha_str, hora))
            else:
                fecha_bd, hora_bd, pid = bd[key]
                if fecha_bd != fecha_str or hora_bd != hora:
                    cur.execute(
                        "UPDATE partidos SET fecha = %s, hora = %s WHERE id = %s",
                        (fecha_str, hora, pid)
                    )

    conn.commit()

# ════════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE NEGOCIO — con caché granular
# ════════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def get_partidos():
    return ejecutar_consulta(
        "SELECT id, equipo_local, equipo_visitante, goles_local, goles_visitante, fase, fecha, hora "
        "FROM partidos ORDER BY fecha, hora"
    )

@st.cache_data(ttl=120)
def get_tabla_posiciones():
    return ejecutar_consulta("""
        SELECT j.nombre,
               COALESCE(SUM(pr.puntos), 0) AS total,
               COUNT(CASE WHEN pr.puntos = 3 THEN 1 END) AS exactos,
               COUNT(CASE WHEN pr.puntos = 1 THEN 1 END) AS ganadores
        FROM jugadores j
        LEFT JOIN predicciones pr ON j.id = pr.jugador_id
        GROUP BY j.id, j.nombre
        ORDER BY total DESC, exactos DESC
    """)

@st.cache_data(ttl=60)
def get_mis_predicciones(jugador_id):
    return ejecutar_consulta("""
        SELECT p.id, p.equipo_local, p.equipo_visitante, p.goles_local, p.goles_visitante,
               p.fase, p.fecha, p.hora, pr.pred_local, pr.pred_visitante, pr.puntos
        FROM predicciones pr
        JOIN partidos p ON pr.partido_id = p.id
        WHERE pr.jugador_id = %s
        ORDER BY p.fecha, p.hora
    """, (jugador_id,))

@st.cache_data(ttl=60)
def get_predicciones_usuario_dict(jugador_id):
    """Una sola query que devuelve todas las predicciones como dict {partido_id: (local, visitante)}."""
    rows = ejecutar_consulta(
        "SELECT partido_id, pred_local, pred_visitante FROM predicciones WHERE jugador_id = %s",
        (jugador_id,)
    )
    return {r[0]: (r[1], r[2]) for r in rows}

def _limpiar_cache_partidos():
    get_partidos.clear()
    get_tabla_posiciones.clear()

def _limpiar_cache_usuario(jugador_id):
    get_mis_predicciones.clear()
    get_predicciones_usuario_dict.clear()
    get_tabla_posiciones.clear()

# ════════════════════════════════════════════════════════════════════════════════
# AUTENTICACIÓN
# ════════════════════════════════════════════════════════════════════════════════

def registrar_usuario(nombre, email, password):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO jugadores (nombre, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                (nombre, email, hash_password(password))
            )
            uid = cur.fetchone()[0]
        conn.commit()
        return uid, None
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return None, str(e)

def login(email, password):
    rows = ejecutar_consulta(
        "SELECT id, nombre, es_admin FROM jugadores WHERE email=%s AND password_hash=%s",
        (email, hash_password(password))
    )
    return rows[0] if rows else None

# ════════════════════════════════════════════════════════════════════════════════
# PREDICCIONES
# ════════════════════════════════════════════════════════════════════════════════

def guardar_prediccion(jugador_id, partido_id, pred_local, pred_visitante):
    partido = ejecutar_consulta(
        "SELECT fecha, hora, goles_local FROM partidos WHERE id = %s", (partido_id,)
    )
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
        _limpiar_cache_usuario(jugador_id)
        return True, "Predicción guardada ✅"
    return False, err

def borrar_prediccion(jugador_id, partido_id):
    partido = ejecutar_consulta(
        "SELECT fecha, hora, goles_local FROM partidos WHERE id = %s", (partido_id,)
    )
    if not partido:
        return False, "Partido no encontrado"
    fecha, hora, goles = partido[0]
    if goles is not None:
        return False, "No se puede borrar: partido ya finalizado"
    if partido_ha_comenzado(fecha, hora):
        return False, "No se puede borrar: el partido ya comenzó"

    ok, err = ejecutar_comando(
        "DELETE FROM predicciones WHERE jugador_id=%s AND partido_id=%s", (jugador_id, partido_id)
    )
    if ok:
        _limpiar_cache_usuario(jugador_id)
        return True, "Predicción borrada"
    return False, err

def limpiar_todas_predicciones_usuario(jugador_id):
    ok, err = ejecutar_comando("DELETE FROM predicciones WHERE jugador_id=%s", (jugador_id,))
    if ok:
        _limpiar_cache_usuario(jugador_id)
        return True, "Todas tus predicciones fueron eliminadas"
    return False, err

# ════════════════════════════════════════════════════════════════════════════════
# ADMIN
# ════════════════════════════════════════════════════════════════════════════════

def set_resultado(partido_id, goles_local, goles_visitante):
    ok, err = ejecutar_comando(
        "UPDATE partidos SET goles_local=%s, goles_visitante=%s WHERE id=%s",
        (goles_local, goles_visitante, partido_id)
    )
    if not ok:
        return False, err

    predicciones = ejecutar_consulta(
        "SELECT jugador_id, pred_local, pred_visitante FROM predicciones WHERE partido_id=%s",
        (partido_id,)
    )

    if predicciones:
        updates = []
        for jugador_id, pl, pv in predicciones:
            if pl == goles_local and pv == goles_visitante:
                puntos = 3
            elif (
                (pl > pv and goles_local > goles_visitante) or
                (pl < pv and goles_local < goles_visitante) or
                (pl == pv and goles_local == goles_visitante)
            ):
                puntos = 1
            else:
                puntos = 0
            updates.append((
                "UPDATE predicciones SET puntos=%s WHERE partido_id=%s AND jugador_id=%s",
                (puntos, partido_id, jugador_id)
            ))
        ejecutar_comandos_batch(updates)

    _limpiar_cache_partidos()
    get_mis_predicciones.clear()
    get_predicciones_usuario_dict.clear()
    return True, None

def add_partido(local, visitante, fase, fecha, hora):
    ok, err = ejecutar_comando("""
        INSERT INTO partidos (equipo_local, equipo_visitante, fase, fecha, hora)
        VALUES (%s, %s, %s, %s, %s)
    """, (local, visitante, fase, fecha, hora))
    if ok:
        _limpiar_cache_partidos()
    return ok, err

# ════════════════════════════════════════════════════════════════════════════════
# INICIALIZAR
# ════════════════════════════════════════════════════════════════════════════════

try:
    init_db()
except Exception as e:
    st.error(f"Error de base de datos: {e}")
    st.stop()

# ─── ESTADO DE SESIÓN ──────────────────────────────────────────────────────────
if "user_id" not in st.session_state:
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.is_admin = False

# ─── HEADER ────────────────────────────────────────────────────────────────────
st.title("⚽ Quiniela Mundial 2026")
st.caption("11 Jun – 19 Jul 2026 | USA · México · Canadá")
st.info(f"📅 Hora Venezuela: {ahora_venezuela().strftime('%d/%m/%Y %H:%M:%S')}")

# ════════════════════════════════════════════════════════════════════════════════
# LOGIN / REGISTRO
# ════════════════════════════════════════════════════════════════════════════════

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
            email_r = st.text_input("Email", key="reg_email")
            pwd = st.text_input("Contraseña", type="password", key="reg_pass")
            pwd2 = st.text_input("Repetir", type="password", key="reg_pass2")
            if st.button("Registrarse", use_container_width=True):
                if not nombre or not email_r or not pwd:
                    st.error("Completa todos los campos")
                elif pwd != pwd2:
                    st.error("Las contraseñas no coinciden")
                elif len(pwd) < 4:
                    st.error("Mínimo 4 caracteres")
                else:
                    uid, err = registrar_usuario(nombre, email_r, pwd)
                    if uid:
                        st.success("¡Registrado! Ahora inicia sesión")
                    else:
                        st.error("Email o nombre ya existe" if "unique" in str(err).lower() else f"Error: {err}")
    st.stop()

# ════════════════════════════════════════════════════════════════════════════════
# SIDEBAR CON MENÚ
# ════════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown(f"**👤 {st.session_state.user_name}**")
    if st.button("🚪 Cerrar sesión", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    st.divider()

    menu = st.radio(
        "Menú",
        ["🏆 Tabla", "🎯 Predecir", "📊 Mis resultados", "📅 Calendario"],
        label_visibility="collapsed"
    )

    admin_menu = None
    if st.session_state.is_admin:
        st.divider()
        st.markdown("**🔧 Admin**")
        admin_menu = st.radio("", ["⚽ Resultados", "➕ Partido"], label_visibility="collapsed")

    partidos_count = len(get_partidos())
    st.caption(f"📊 {partidos_count} partidos cargados")

# ════════════════════════════════════════════════════════════════════════════════
# 1. TABLA DE POSICIONES
# ════════════════════════════════════════════════════════════════════════════════

if menu == "🏆 Tabla":
    st.header("🏆 Clasificación")
    tabla = get_tabla_posiciones()

    if not tabla:
        st.info("No hay jugadores registrados aún")
    else:
        for i, (nombre, pts, exactos, ganadores) in enumerate(tabla, 1):
            icon = ["🥇", "🥈", "🥉"][i - 1] if i <= 3 else f"{i}."
            st.markdown(f"{icon} **{nombre}** — **{pts} pts** (🟢 {exactos} exactos / 🟡 {ganadores} ganadores)")

# ════════════════════════════════════════════════════════════════════════════════
# 2. PREDICCIONES
# ════════════════════════════════════════════════════════════════════════════════

elif menu == "🎯 Predecir":
    st.header(f"🎯 Predecir — {st.session_state.user_name}")

    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn2:
        if st.button("🗑️ Limpiar todas", use_container_width=True):
            ok, msg = limpiar_todas_predicciones_usuario(st.session_state.user_id)
            st.success(msg) if ok else st.error(msg)
            if ok:
                st.rerun()

    st.divider()

    partidos = get_partidos()
    # Una sola query para todas las predicciones del usuario
    todas_preds = get_predicciones_usuario_dict(st.session_state.user_id)

    disponibles = [p for p in partidos if p[3] is None]

    if not disponibles:
        st.info("No hay partidos disponibles para predecir")
    else:
        for p in disponibles:
            pid, local, visitante, gl, gv, fase, fecha, hora = p
            pred = todas_preds.get(pid)
            tiene_pred = pred is not None
            val_l = pred[0] if pred else 0
            val_v = pred[1] if pred else 0

            ya_comenzo, tiempo_text = tiempo_restante(fecha, hora)
            disabled = ya_comenzo

            if tiene_pred:
                st.markdown(f"📝 **{local} vs {visitante}** — Actual: {val_l}-{val_v}")
            else:
                st.markdown(f"⚪ **{local} vs {visitante}** — Sin predicción")

            col1, col2, col3, col4, col5 = st.columns([2, 1, 2, 1, 1])
            with col1:
                g_l = st.number_input(local, 0, 10, val_l, key=f"l_{pid}",
                                      label_visibility="collapsed", disabled=disabled)
            with col2:
                st.write("vs")
            with col3:
                g_v = st.number_input(visitante, 0, 10, val_v, key=f"v_{pid}",
                                      label_visibility="collapsed", disabled=disabled)
            with col4:
                if not disabled:
                    if st.button("💾", key=f"s_{pid}", use_container_width=True):
                        ok, msg = guardar_prediccion(st.session_state.user_id, pid, g_l, g_v)
                        st.success(msg) if ok else st.error(msg)
                        if ok:
                            st.rerun()
            with col5:
                if tiene_pred and not disabled:
                    if st.button("🗑️", key=f"d_{pid}", use_container_width=True):
                        ok, msg = borrar_prediccion(st.session_state.user_id, pid)
                        st.success(msg) if ok else st.error(msg)
                        if ok:
                            st.rerun()

            if isinstance(fecha, str):
                d = datetime.strptime(fecha, "%Y-%m-%d").date()
            else:
                d = fecha
            st.caption(f"📅 {d.day}/{d.month} {hora} | {tiempo_text} | {fase}")
            st.divider()

# ════════════════════════════════════════════════════════════════════════════════
# 3. MIS RESULTADOS
# ════════════════════════════════════════════════════════════════════════════════

elif menu == "📊 Mis resultados":
    st.header(f"📊 Mis resultados — {st.session_state.user_name}")

    predicciones = get_mis_predicciones(st.session_state.user_id)

    if not predicciones:
        st.info("Aún no tienes predicciones")
    else:
        total = sum(p[10] for p in predicciones if p[10])
        st.metric("🏆 Puntos totales", total)
        st.divider()

        ahora = ahora_venezuela()
        for p in predicciones:
            pid, local, visitante, gl, gv, fase, fecha, hora, pl, pv, pts = p

            if gl is not None:
                icon = {3: "🟢", 1: "🟡"}.get(pts, "⚫")
                st.write(f"{icon} {local} {pl}-{pv} vs {visitante} → Real: {gl}-{gv} ({pts} pts)")
            else:
                if isinstance(fecha, str):
                    fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
                else:
                    fecha_dt = fecha
                fecha_hora = datetime.combine(fecha_dt, datetime.strptime(hora, "%H:%M").time()).replace(tzinfo=VENEZUELA_TZ)

                if fecha_hora > ahora:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"⏳ {local} {pl}-{pv} vs {visitante} ({fecha_dt.day}/{fecha_dt.month} {hora})")
                    with col2:
                        if st.button("🗑️", key=f"del_{pid}"):
                            ok, msg = borrar_prediccion(st.session_state.user_id, pid)
                            st.success(msg) if ok else st.error(msg)
                            if ok:
                                st.rerun()
                else:
                    st.write(f"🔒 {local} {pl}-{pv} vs {visitante} ({fecha_dt.day}/{fecha_dt.month} {hora})")

# ════════════════════════════════════════════════════════════════════════════════
# 4. CALENDARIO
# ════════════════════════════════════════════════════════════════════════════════

elif menu == "📅 Calendario":
    st.header("📅 Calendario")

    partidos = get_partidos()
    ahora = ahora_venezuela()

    for fase in ORDEN_FASES:
        partidos_fase = [p for p in partidos if p[5] == fase]
        if not partidos_fase:
            continue
        st.subheader(fase)
        for p in partidos_fase:
            pid, local, visitante, gl, gv, fase_p, fecha, hora = p
            if isinstance(fecha, str):
                fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
            else:
                fecha_dt = fecha

            if gl is not None:
                st.write(f"✅ **{fecha_dt.day}/{fecha_dt.month} {hora}** — {local} {gl}-{gv} {visitante}")
            else:
                fecha_hora = datetime.combine(fecha_dt, datetime.strptime(hora, "%H:%M").time()).replace(tzinfo=VENEZUELA_TZ)
                icon = "🔴" if fecha_hora <= ahora else "⏳"
                st.write(f"{icon} **{fecha_dt.day}/{fecha_dt.month} {hora}** — {local} vs {visitante}")
        st.divider()

# ════════════════════════════════════════════════════════════════════════════════
# ADMIN: RESULTADOS
# ════════════════════════════════════════════════════════════════════════════════

if st.session_state.is_admin and admin_menu == "⚽ Resultados":
    st.header("⚽ Ingresar resultados")

    partidos = get_partidos()
    pendientes = [p for p in partidos if p[3] is None]

    if not pendientes:
        st.success("Todos los partidos tienen resultado")
    else:
        for p in pendientes:
            pid, local, visitante, gl, gv, fase, fecha, hora = p
            if isinstance(fecha, str):
                fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
            else:
                fecha_dt = fecha

            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                gl_new = st.number_input(local, 0, 20, key=f"gl_{pid}")
            with col2:
                gv_new = st.number_input(visitante, 0, 20, key=f"gv_{pid}")
            with col3:
                if st.button("✅", key=f"r_{pid}"):
                    ok, err = set_resultado(pid, gl_new, gv_new)
                    if ok:
                        st.success(f"{local} {gl_new}-{gv_new} {visitante}")
                        st.rerun()
                    else:
                        st.error(err)
            st.caption(f"{fecha_dt.day}/{fecha_dt.month} {hora} — {fase}")
            st.divider()

# ════════════════════════════════════════════════════════════════════════════════
# ADMIN: AGREGAR PARTIDO
# ════════════════════════════════════════════════════════════════════════════════

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
                ok, err = add_partido(local, visitante, fase, fecha, hora)
                if ok:
                    st.success(f"Partido agregado: {local} vs {visitante}")
                    st.rerun()
                else:
                    st.error(f"Error: {err}")
            else:
                st.error("Completa todos los campos")
