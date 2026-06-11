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
    .partido-card { background: linear-gradient(135deg, #1a472a 0%, #2d5a27 50%, #1a3a5c 100%); border-radius: 12px; padding: 16px; margin: 8px 0; color: white; }
    .grupo-header { background: linear-gradient(90deg, #c8a951 0%, #e8c96b 100%); border-radius: 8px; padding: 8px 16px; color: #1a1a1a; font-weight: bold; font-size: 1.1em; margin: 12px 0 6px 0; }
</style>
""", unsafe_allow_html=True)

# ─── DATOS ───────────────────────────────────────────────────────────
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
    # ... (Nota: Mantén tu lista completa de partidos aquí)
]

FASES_ELIMINATORIAS = ["16avos de Final", "Octavos de Final", "Cuartos de Final", "Semifinal", "Tercer lugar", "Final"]

# ─── Funciones de Base de Datos ───────────────────────────────────────────────
@st.cache_resource
def get_db_pool():
    import psycopg2.pool
    return psycopg2.pool.SimpleConnectionPool(1, 5, os.environ["DATABASE_URL"])

def get_connection():
    return get_db_pool().getconn()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jugadores (
            id SERIAL PRIMARY KEY, nombre VARCHAR(50) UNIQUE NOT NULL, email VARCHAR(100) UNIQUE NOT NULL, 
            password_hash VARCHAR(64) NOT NULL, es_admin BOOLEAN DEFAULT FALSE, registrado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS partidos (
            id SERIAL PRIMARY KEY, equipo_local VARCHAR(60) NOT NULL, equipo_visitante VARCHAR(60) NOT NULL, 
            goles_local INTEGER DEFAULT NULL, goles_visitante INTEGER DEFAULT NULL, fase VARCHAR(30) NOT NULL, 
            fecha DATE NOT NULL, sede VARCHAR(50), precargado BOOLEAN DEFAULT FALSE
        );
        CREATE TABLE IF NOT EXISTS predicciones (
            id SERIAL PRIMARY KEY, jugador_id INTEGER REFERENCES jugadores(id), partido_id INTEGER REFERENCES partidos(id), 
            pred_local INTEGER NOT NULL, pred_visitante INTEGER NOT NULL, puntos INTEGER DEFAULT 0, UNIQUE(jugador_id, partido_id)
        );
    """)
    conn.commit()
    cur.close()
    get_db_pool().putconn(conn)

# ─── Inicialización ──────────────────────────────────────────────────────────
try:
    init_db()
except Exception as e:
    st.error(f"❌ Error de base de datos: {e}")
    st.stop()

# ─── Lógica de Navegación ────────────────────────────────────────────────────
if "usuario" not in st.session_state:
    st.session_state.usuario = None

# (Aquí va el resto de la interfaz, los menús y funciones de tu archivo original)
st.title("Quiniela Mundial 2026")
st.write("Bienvenido, por favor usa el menú lateral para navegar.")
