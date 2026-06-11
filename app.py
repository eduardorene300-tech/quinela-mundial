import streamlit as st
import psycopg2
import os
from datetime import datetime

# ─── Configuración de página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="⚽ Quiniela Mundial",
    page_icon="⚽",
    layout="wide"
)

# ─── Conexión a Neon (base de datos) ───────────────────────────────────────────
def get_connection():
    # Asegúrate de tener la variable DATABASE_URL configurada en los Secrets de Streamlit
    return psycopg2.connect(os.environ["DATABASE_URL"])

# ─── Crear tablas si no existen ────────────────────────────────────────────────
def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS partidos (
            id SERIAL PRIMARY KEY,
            equipo_local VARCHAR(50) NOT NULL,
            equipo_visitante VARCHAR(50) NOT NULL,
            goles_local INTEGER DEFAULT NULL,
            goles_visitante INTEGER DEFAULT NULL,
            fase VARCHAR(30) NOT NULL,
            fecha TIMESTAMP NOT NULL
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS predicciones (
            id SERIAL PRIMARY KEY,
            usuario VARCHAR(50) NOT NULL,
            partido_id INTEGER REFERENCES partidos(id),
            pred_local INTEGER NOT NULL,
            pred_visitante INTEGER NOT NULL,
            puntos INTEGER DEFAULT 0,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(usuario, partido_id)
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

# ─── Funciones de base de datos ────────────────────────────────────────────────
def get_partidos():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM partidos ORDER BY fecha")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def add_partido(local, visitante, fase, fecha):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO partidos (equipo_local, equipo_visitante, fase, fecha) VALUES (%s, %s, %s, %s)",
        (local, visitante, fase, fecha)
    )
    conn.commit()
    cur.close()
    conn.close()

def calcular_puntos(pred_l, pred_v, real_l, real_v):
    if pred_l == real_l and pred_v == real_v:
        return 3
    pred_ganador = "L" if pred_l > pred_v else ("V" if pred_v > pred_l else "E")
    real_ganador = "L" if real_l > real_v else ("V" if real_v > real_l else "E")
    if pred_ganador == real_ganador:
        return 1
    return 0

def set_resultado(partido_id, goles_local, goles_visitante):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE partidos SET goles_local=%s, goles_visitante=%s WHERE id=%s",
        (goles_local, goles_visitante, partido_id)
    )
    cur.execute("SELECT id, pred_local, pred_visitante FROM predicciones WHERE partido_id=%s", (partido_id,))
    preds = cur.fetchall()
    for pred_id, pl, pv in preds:
        puntos = calcular_puntos(pl, pv, goles_local, goles_visitante)
        cur.execute("UPDATE predicciones SET puntos=%s WHERE id=%s", (puntos, pred_id))
    conn.commit()
    cur.close()
    conn.close()

def save_prediccion(usuario, partido_id, pred_local, pred_visitante):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO predicciones (usuario, partido_id, pred_local, pred_visitante)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (usuario, partido_id)
        DO UPDATE SET pred_local=EXCLUDED.pred_local, pred_visitante=EXCLUDED.pred_visitante
    """, (usuario, partido_id, pred_local, pred_visitante))
    conn.commit()
    cur.close()
    conn.close()

def get_predicciones_usuario(usuario):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.equipo_local, p.equipo_visitante, p.goles_local, p.goles_visitante,
               pr.pred_local, pr.pred_visitante, pr.puntos
        FROM predicciones pr
        JOIN partidos p ON pr.partido_id = p.id
        WHERE pr.usuario = %s
        ORDER BY p.fecha
    """, (usuario,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_tabla_posiciones():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT usuario, SUM(puntos) as total
        FROM predicciones
        GROUP BY usuario
        ORDER BY total DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

# ─── Inicialización ────────────────────────────────────────────────────────────
try:
    init_db()
except Exception as e:
    st.error("Error conectando a la base de datos: " + str(e))
    st.stop()

# ─── Interfaz ──────────────────────────────────────────────────────────────────
st.title("⚽ Quiniela del Mundial")
menu = st.sidebar.selectbox("📋 Menú", [
    "🏆 Tabla de posiciones", "🎯 Hacer mis predicciones", 
    "📊 Ver mis resultados", "⚙️ Admin: Cargar partidos", 
    "✅ Admin: Ingresar resultados"
])

if menu == "🏆 Tabla de posiciones":
    st.header("🏆 Tabla de Posiciones")
    tabla = get_tabla_posiciones()
    if not tabla:
        st.info("Aún no hay predicciones registradas.")
    else:
        for i, (usuario, total) in enumerate(tabla):
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
            st.write(f"**{medal} {usuario}**: {total} pts")

elif menu == "🎯 Hacer mis predicciones":
    st.header("🎯 Hacer mis Predicciones")
    nombre = st.text_input("👤 Tu nombre")
    if nombre:
        partidos = get_partidos()
        # Corregido: comparar contra None en goles_local
        partidos_sin_resultado = [p for p in partidos if p[3] is None]
        if not partidos_sin_resultado:
            st.info("No hay partidos pendientes.")
        else:
            for p in partidos_sin_resultado:
                pid, local, visitante, _, _, fase, _ = p
                with st.expander(f"⚽ {local} vs {visitante} — {fase}"):
                    c1, c2 = st.columns(2)
                    pl = c1.number_input(f"Goles {local}", min_value=0, key=f"l_{pid}")
                    pv = c2.number_input(f"Goles {visitante}", min_value=0, key=f"v_{pid}")
                    if st.button("Guardar", key=f"btn_{pid}"):
                        save_prediccion(nombre, pid, pl, pv)
                        st.success("Guardado")

elif menu == "📊 Ver mis resultados":
    st.header("📊 Mis Resultados")
    nombre = st.text_input("👤 Tu nombre")
    if nombre:
        preds = get_predicciones_usuario(nombre)
        for local, visitante, gl, gv, pl, pv, ptos in preds:
            st.write(f"**{local} vs {visitante}**: Pred {pl}-{pv} | Real {gl}-{gv} | **{ptos} pts**")

elif menu == "⚙️ Admin: Cargar partidos":
    with st.form("add_partido"):
        local = st.text_input("Local")
        visitante = st.text_input("Visitante")
        fase = st.selectbox("Fase", ["Grupos", "Octavos", "Cuartos", "Semifinal", "Final"])
        fecha = st.date_input("Fecha")
        if st.form_submit_button("Agregar"):
            add_partido(local, visitante, fase, fecha)
            st.success("Agregado")

elif menu == "✅ Admin: Ingresar resultados":
    partidos = [p for p in get_partidos() if p[3] is None]
    for p in partidos:
        pid, local, visitante, _, _, _, _ = p
        with st.expander(f"{local} vs {visitante}"):
            gl = st.number_input(f"Goles {local}", key=f"rgl_{pid}")
            gv = st.number_input(f"Goles {visitante}", key=f"rgv_{pid}")
            if st.button("Guardar Resultado", key=f"btnres_{pid}"):
                set_resultado(pid, gl, gv)
                st.rerun()
