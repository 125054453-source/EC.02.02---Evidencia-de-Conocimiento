"""
igdb_utils.py
Funciones de datos y gráficas del dashboard (no dependen de Streamlit, así se
pueden probar por separado). Fuente: API de IGDB (Internet Game Database, Twitch).
"""
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from matplotlib.figure import Figure

# Paleta del curso
GRIS = "#B9C3D1"
AZUL = "#1C4C9A"
ROJO = "#B2182B"

URL_TOKEN_TWITCH = "https://id.twitch.tv/oauth2/token"
URL_GAMES = "https://api.igdb.com/v4/games"


# ─── Datos ────────────────────────────────────────────────────────────────
def cargar_json(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


def preparar(juegos):
    """Lista de juegos (JSON de IGDB) -> tabla limpia lista para graficar."""
    df = pd.DataFrame(juegos)
    df["genero"] = df["genres"].apply(
        lambda l: l[0]["name"] if isinstance(l, list) and l else np.nan)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df["critica"] = pd.to_numeric(df.get("aggregated_rating"), errors="coerce")
    df["votos"] = pd.to_numeric(df["total_rating_count"], errors="coerce")
    df["anio"] = pd.to_datetime(df["first_release_date"], unit="s",
                                errors="coerce").dt.year
    df = df.dropna(subset=["rating", "genero", "anio"])
    df["anio"] = df["anio"].astype(int)
    return df[["name", "anio", "genero", "rating", "critica", "votos"]] \
        .rename(columns={"name": "juego"}).reset_index(drop=True)


def descargar_api(client_id, client_secret, objetivo=240, tam_pagina=120):
    """Pide un access_token a Twitch y descarga juegos de IGDB (paginado)."""
    r = requests.post(URL_TOKEN_TWITCH, timeout=20, params={
        "client_id": client_id, "client_secret": client_secret,
        "grant_type": "client_credentials"})
    if r.status_code != 200:
        raise RuntimeError(f"Twitch respondió {r.status_code} al pedir el token. "
                           "Revisa el Client ID y el Client Secret.")
    token = r.json()["access_token"]
    encabezados = {"Client-ID": client_id, "Authorization": f"Bearer {token}",
                   "Content-Type": "text/plain"}
    juegos, offset = [], 0
    while len(juegos) < objetivo:
        cuerpo = ("fields name,first_release_date,rating,aggregated_rating,"
                  "total_rating_count,genres.name;\n"
                  "where rating != null & first_release_date != null;\n"
                  "sort total_rating_count desc;\n"
                  f"limit {tam_pagina};\noffset {offset};")
        resp = requests.post(URL_GAMES, headers=encabezados, data=cuerpo, timeout=20)
        if resp.status_code != 200:
            raise RuntimeError(f"IGDB respondió {resp.status_code}: {resp.text[:200]}")
        if "json" not in (resp.headers.get("Content-Type") or ""):
            raise RuntimeError("IGDB no respondió en JSON.")
        pagina = resp.json()
        if not pagina:
            break
        juegos.extend(pagina)
        offset += tam_pagina
        time.sleep(0.3)  # límite: 4 peticiones por segundo
    return juegos


def guardar_json(juegos, ruta):
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(juegos, f, ensure_ascii=False, indent=2)


# ─── Gráficas (cada una devuelve (figura, lectura) o None si no hay datos) ─
def _fig(w=8, h=4.5):
    fig = Figure(figsize=(w, h))
    return fig, fig.subplots()


def fig_distribucion(df):
    if len(df) < 2:
        return None
    r = df["rating"]
    media, q1, q3 = r.mean(), r.quantile(0.25), r.quantile(0.75)
    fig, ax = _fig()
    ax.hist(r, bins=20, color=GRIS, edgecolor="white")
    ax.axvline(media, color=AZUL, linewidth=2)
    ax.text(media + 0.3, ax.get_ylim()[1] * 0.97, f"Media: {media:.1f}",
            color=AZUL, va="top", fontsize=10)
    ax.set_title(f"La mitad de los juegos se califica entre {q1:.0f} y {q3:.0f} "
                 f"(máximo {r.max():.0f})", fontsize=11)
    ax.set_xlabel("Calificación de la comunidad (0 a 100 puntos)")
    ax.set_ylabel("Número de juegos")
    fig.tight_layout()
    return fig, (f"Con {len(df)} juegos, la media es {media:.1f} y la mitad central "
                 f"va de {q1:.0f} a {q3:.0f} puntos.")


def fig_generos(df, top=8):
    if df.empty:
        return None
    top_g = df["genero"].value_counts().head(top).index
    sub = df[df["genero"].isin(top_g)]
    prom = sub.groupby("genero")["rating"].mean().sort_values(ascending=False)
    cuenta = sub["genero"].value_counts()
    fig, ax = _fig(9, 4.8)
    colores = [AZUL if i == 0 else GRIS for i in range(len(prom))]
    ax.bar(range(len(prom)), prom.values, color=colores)
    ax.set_xticks(range(len(prom)))
    ax.set_xticklabels([f"{g}\n(n = {cuenta[g]})" for g in prom.index],
                       rotation=30, ha="right", fontsize=8)
    bajo = max(0, np.floor(prom.min() / 5) * 5 - 5)
    ax.set_ylim(bajo, min(100, prom.max() + 3))
    if len(prom) > 1:
        titulo = (f"{prom.index[0]} lidera y {prom.index[-1]} queda "
                  f"{prom.iloc[0] - prom.iloc[-1]:.0f} puntos abajo")
    else:
        titulo = f"Solo hay un género con datos: {prom.index[0]}"
    ax.set_title(titulo, fontsize=11)
    ax.set_xlabel("Género principal (n = número de juegos)")
    ax.set_ylabel(f"Calificación promedio (0 a 100; eje desde {bajo:.0f})")
    fig.tight_layout()
    chicos = [g for g in prom.index if cuenta[g] < 5]
    nota = ("Los géneros con menos de 5 juegos (" + ", ".join(chicos) +
            ") pesan poco." if chicos else "")
    return fig, nota


def fig_relacion(df):
    d = df.dropna(subset=["critica"])
    if len(d) < 3:
        return None
    r = d["critica"].corr(d["rating"])
    fuerza = "fuerte" if abs(r) >= 0.7 else "moderada" if abs(r) >= 0.4 else "débil"
    sentido = "positiva" if r >= 0 else "negativa"
    fig, ax = _fig()
    ax.scatter(d["critica"], d["rating"], color=AZUL, alpha=0.5)
    ax.set_title(f"Crítica y comunidad: relación {fuerza} y {sentido} (r = {r:.2f})",
                 fontsize=11)
    ax.set_xlabel("Calificación de la crítica (0 a 100 puntos)")
    ax.set_ylabel("Calificación de la comunidad (0 a 100 puntos)")
    fig.tight_layout()
    return fig, f"Calculado con {len(d)} juegos que tienen ambas calificaciones."


def fig_evolucion(df, min_juegos=5):
    g = df.groupby("anio")["rating"].agg(["mean", "count"])
    g = g[g["count"] >= min_juegos]
    if len(g) < 2:
        return None
    a_min, a_max = g["mean"].idxmin(), g["mean"].idxmax()
    fig, ax = _fig(9, 4.5)
    ax.plot(g.index, g["mean"], color=GRIS, linewidth=1.5)
    ax.plot(g.index, g["mean"], "o", color=GRIS)
    ax.plot(a_min, g.loc[a_min, "mean"], "o", color=AZUL, markersize=9)
    ax.plot(a_max, g.loc[a_max, "mean"], "o", color=ROJO, markersize=9)
    ax.xaxis.set_major_locator(__import__("matplotlib").ticker.MaxNLocator(integer=True))
    ax.set_title(f"Promedio más alto en {a_max} ({g.loc[a_max, 'mean']:.0f}) y más "
                 f"bajo en {a_min} ({g.loc[a_min, 'mean']:.0f})", fontsize=11)
    ax.set_xlabel(f"Año de lanzamiento (solo años con {min_juegos} o más juegos)")
    ax.set_ylabel("Calificación promedio (0 a 100 puntos)")
    fig.tight_layout()
    return fig, f"Se grafican {len(g)} años; los demás tienen muy pocos juegos."
