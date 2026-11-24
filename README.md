# Dashboard de videojuegos con la API de IGDB

Dashboard hecho con **Streamlit** a partir de la API de **IGDB** (Internet Game Database, de Twitch).
Herramientas de Visualización · Unidad II · Universidad Politécnica de Querétaro.

**Autor:** _tu nombre aquí_

## Qué muestra

Los 240 juegos con más votos que tienen calificación de la comunidad y fecha de lanzamiento.

| Pestaña | Pregunta que responde |
|---|---|
| Distribución | ¿Cómo se reparten las calificaciones de la comunidad? |
| Géneros | ¿Qué género tiene mejor calificación promedio? |
| Crítica vs comunidad | ¿La crítica y la comunidad califican parecido? |
| Evolución | ¿Cómo cambió la calificación promedio con los años? |
| Datos | Tabla filtrada y descarga en CSV |

Filtros en la barra lateral: años de lanzamiento, género principal y calificación mínima.
Los títulos de las gráficas se calculan con los datos filtrados, así que siempre dicen lo que se ve.

## Cómo correrlo

```bash
pip install -r requirements.txt
streamlit run app.py
```

Funciona sin credenciales: usa los datos guardados en `data/respuesta.json`.

## Actualizar los datos desde la API (opcional)

1. Crea una app gratis en https://dev.twitch.tv/console/apps y genera un Client ID y un Client Secret.
2. Copia `.streamlit/secrets.toml.example` como `.streamlit/secrets.toml` y escribe tus credenciales
   (o define las variables de entorno `IGDB_CLIENT_ID` e `IGDB_CLIENT_SECRET`).
3. Aparece el botón **Actualizar desde la API de IGDB** en la barra lateral.

Las credenciales **nunca** se suben a GitHub: `.gitignore` excluye `token*.txt` y `secrets.toml`.

## Cómo funciona la integración con la API

1. Se pide un `access_token` a Twitch con el Client ID y el Client Secret (`client_credentials`).
2. Se consulta `POST https://api.igdb.com/v4/games` con los encabezados `Client-ID` y `Authorization: Bearer ...`
   y una consulta Apicalypse (campos, filtro, orden, límite y offset), en 2 páginas de 120 juegos.
3. Se revisa el código de estado y que la respuesta sea JSON; se guarda en `data/respuesta.json` y se reutiliza.
4. `preparar()` convierte tipos, saca el año del timestamp y el género principal.

## Archivos

- `app.py`: interfaz de Streamlit (filtros, indicadores, pestañas).
- `igdb_utils.py`: descarga de la API, limpieza y gráficas.
- `data/respuesta.json`: respuesta guardada de la API.

## Limitaciones

- La muestra son los juegos más votados, no una muestra al azar.
- El género es el primero que entrega IGDB para cada juego.
- Con filtros muy estrechos algunas gráficas muestran un aviso en lugar de graficar.
