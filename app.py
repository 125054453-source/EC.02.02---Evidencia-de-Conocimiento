"""
Dashboard de videojuegos con datos de la API de IGDB (Twitch).
Herramientas de Visualización · Unidad II.

Correr:  streamlit run app.py
"""
import os
from pathlib import Path

import streamlit as st

import igdb_utils as iu

RUTA_DATOS = Path(__file__).parent / "data" / "respuesta.json"

st.set_page_config(page_title="Videojuegos en IGDB", page_icon="🎮", layout="wide")


# ─── Carga de datos (con caché: no se vuelve a leer en cada interacción) ───
@st.cache_data(show_spinner=False)
def cargar():
    return iu.preparar(iu.cargar_json(RUTA_DATOS))


def credenciales():
    """Client ID y Secret desde secrets de Streamlit o variables de entorno.
    Nunca van escritos en el código ni se suben a GitHub."""
    try:
        return st.secrets["IGDB_CLIENT_ID"], st.secrets["IGDB_CLIENT_SECRET"]
    except Exception:
        return os.environ.get("IGDB_CLIENT_ID", ""), os.environ.get("IGDB_CLIENT_SECRET", "")


st.title("🎮 Videojuegos mejor calificados en IGDB")
st.caption("Fuente: API de IGDB (Internet Game Database, vía Twitch). Los 240 juegos "
           "con más votos que tienen calificación de la comunidad y fecha de lanzamiento.")

# ─── Barra lateral: actualizar datos y filtros ──────────────────────────────
st.sidebar.header("Datos")
cid, csec = credenciales()
if cid and csec:
    if st.sidebar.button("Actualizar desde la API de IGDB"):
        try:
            with st.spinner("Consultando IGDB..."):
                iu.guardar_json(iu.descargar_api(cid, csec), RUTA_DATOS)
            cargar.clear()
            st.sidebar.success("Datos actualizados.")
        except Exception as e:
            st.sidebar.error(str(e))
else:
    st.sidebar.caption("Mostrando datos guardados de IGDB. Para actualizar desde la API "
                       "configura IGDB_CLIENT_ID e IGDB_CLIENT_SECRET (ver README).")

df = cargar()

st.sidebar.header("Filtros")
a_min, a_max = int(df["anio"].min()), int(df["anio"].max())
anios = st.sidebar.slider("Año de lanzamiento", a_min, a_max, (a_min, a_max))
generos_todos = sorted(df["genero"].unique())
generos = st.sidebar.multiselect("Género principal", generos_todos, default=generos_todos)
rating_min = st.sidebar.slider("Calificación mínima de la comunidad", 0, 100, 0)

f = df[(df["anio"].between(*anios)) & (df["genero"].isin(generos)) &
       (df["rating"] >= rating_min)]

if f.empty:
    st.warning("Ningún juego cumple los filtros. Amplía el rango de años, los géneros o "
               "baja la calificación mínima.")
    st.stop()

# ─── Indicadores ────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Juegos", len(f))
c2.metric("Calificación comunidad (media)", f"{f['rating'].mean():.1f}")
crit = f["critica"].mean()
c3.metric("Calificación crítica (media)", f"{crit:.1f}" if crit == crit else "sin datos")
c4.metric("Periodo", f"{int(f['anio'].min())} – {int(f['anio'].max())}")


def mostrar(resultado, vacio):
    if resultado is None:
        st.info(vacio)
        return
    fig, lectura = resultado
    st.pyplot(fig)
    if lectura:
        st.caption(lectura)


# ─── Las cuatro gráficas ────────────────────────────────────────────────────
t1, t2, t3, t4, t5 = st.tabs(["Distribución", "Géneros", "Crítica vs comunidad",
                              "Evolución", "Datos"])
with t1:
    st.subheader("¿Cómo se reparten las calificaciones?")
    mostrar(iu.fig_distribucion(f), "Se necesitan al menos 2 juegos.")
with t2:
    st.subheader("¿Qué género tiene mejor calificación promedio?")
    mostrar(iu.fig_generos(f), "No hay datos con estos filtros.")
with t3:
    st.subheader("¿La crítica y la comunidad califican parecido?")
    mostrar(iu.fig_relacion(f), "Se necesitan al menos 3 juegos con calificación de la crítica.")
with t4:
    st.subheader("¿Cómo cambió la calificación con los años?")
    minimo = st.slider("Mínimo de juegos por año", 1, 10, 5,
                       help="Un promedio de 1 o 2 juegos es ruido; sube el mínimo para "
                            "ver solo años con más datos.")
    mostrar(iu.fig_evolucion(f, minimo), "Con estos filtros hay menos de 2 años que cumplan "
                                         "el mínimo. Baja el mínimo o amplía el rango.")
with t5:
    st.subheader("Juegos filtrados")
    tabla = f.sort_values("votos", ascending=False)
    st.dataframe(tabla, hide_index=True, use_container_width=True)
    st.download_button("Descargar CSV", tabla.to_csv(index=False).encode("utf-8"),
                       file_name="juegos_igdb.csv", mime="text/csv")

st.caption("Nota: el género es el primero que entrega IGDB para cada juego, y la muestra son "
           "los juegos más votados, no una muestra al azar.")
