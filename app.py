import os
import re
import json
import pandas as pd
import streamlit as st
import whisper
import torch
import googleapiclient.discovery
import googleapiclient.errors
from yt_dlp import YoutubeDL

# --- CONFIGURACIÓN DE RUTAS Y CONSTANTES ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CARPETA_EXCEL = os.path.join(BASE_DIR, "resultados_excel")
CARPETA_TXT = os.path.join(BASE_DIR, "transcripciones_completas")
RUTA_JSON = os.path.join(BASE_DIR, "API_KEYS.json")

# Crear carpetas si no existen
for c in [CARPETA_EXCEL, CARPETA_TXT]:
    if not os.path.exists(c): os.makedirs(c)

# --- FUNCIONES DE UTILIDAD (Importadas de tus scripts) ---
def limpiar_nombre(texto):
    return re.sub(r'[\\/*?:"<>|]', "", str(texto))[:80]

def es_short_real(video_id):
    url = f"https://www.youtube.com/shorts/{video_id}"
    try:
        import requests
        res = requests.head(url, allow_redirects=True, timeout=5)
        return "/shorts/" in res.url
    except: 
        return False

def obtener_api_key():
    if not os.path.exists(RUTA_JSON):
        return None
    with open(RUTA_JSON, 'r') as f:
        return json.load(f).get("youtube_api")

def guardar_api_key(key):
    with open(RUTA_JSON, 'w') as f:
        json.dump({"youtube_api": key}, f, indent=4)

# --- LÓGICA DEL SCRAPER (Script 1) ---
def ejecutar_scraper(url_canal, limite, youtube):
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("Identificando canal...")
        handle = url_canal.split("@")[1].split("/")[0] if "@" in url_canal else url_canal.split("/")[-1]
        search = youtube.search().list(q=handle, type="channel", part="snippet", maxResults=1).execute()
        
        if not search['items']:
            st.error("Canal no encontrado.")
            return None
            
        ch_id = search['items'][0]['id']['channelId']
        ch_name = search['items'][0]['snippet']['title']
        
        ch_res = youtube.channels().list(part="contentDetails", id=ch_id).execute()
        uploads_id = ch_res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        v_ids = []
        next_p = None
        
        status_text.text(f"Obteniendo lista de videos (máximo {limite})...")
        
        while len(v_ids) < limite:
            max_a_pedir = min(50, limite - len(v_ids))
            res = youtube.playlistItems().list(
                part="contentDetails", 
                playlistId=uploads_id, 
                maxResults=max_a_pedir, 
                pageToken=next_p
            ).execute()
            
            v_ids.extend([item['contentDetails']['videoId'] for item in res['items']])
            next_p = res.get('nextPageToken')
            if not next_p: break

        data = []
        total = len(v_ids)
        
        status_text.text(f"Analizando {total} videos...")
        
        for i in range(0, total, 50):
            batch = v_ids[i:i+50]
            v_res = youtube.videos().list(part="snippet,statistics", id=",".join(batch)).execute()
            for v in v_res['items']:
                if es_short_real(v['id']):
                    data.append({
                        "Titulo": v['snippet']['title'],
                        "Vistas": int(v['statistics'].get('viewCount', 0)),
                        "Link": f"https://www.youtube.com/shorts/{v['id']}",
                        "Descripción": v['snippet'].get('description', 'Sin descripción'),
                        "Validador": "Pendiente"
                    })
            
            # Actualizar barra de progreso
            progress = min((i + 50) / total, 1.0)
            progress_bar.progress(progress)

        if data:
            df = pd.DataFrame(data).sort_values(by='Vistas', ascending=False)
            nombre_limpio = "".join(c for c in ch_name if c.isalnum() or c in ' -_').strip() + ".xlsx"
            ruta_final = os.path.join(CARPETA_EXCEL, nombre_limpio)
            df.to_excel(ruta_final, index=False)
            return df, ruta_final
        else:
            return None, None
            
    except Exception as e:
        st.error(f"Error en scraper: {e}")
        return None, None

# --- LÓGICA IA (Script 2) ---
@st.cache_resource
def cargar_modelo_whisper():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return whisper.load_model("base", device=device)

def transcribir_video(titulo, link, descripcion, modelo):
    nombre_audio = "temp_audio.m4a"
    try:
        ydl_opts = {'format': 'm4a/bestaudio/best', 'outtmpl': 'temp_audio.%(ext)s', 'quiet': True}
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
        
        res = modelo.transcribe(nombre_audio, fp16=(torch.cuda.is_available()))
        guion = res['text'].strip()

        nombre_fichero = limpiar_nombre(titulo) + ".txt"
        ruta_txt = os.path.join(CARPETA_TXT, nombre_fichero)
        with open(ruta_txt, "w", encoding="utf-8") as f:
            f.write(f"TITULO: {titulo}\n\nGUIÓN: {guion}\n\nDESCRIPCIÓN: {descripcion}")
        
        return guion, ruta_txt
    except Exception as e:
        return None, str(e)
    finally:
        if os.path.exists(nombre_audio): os.remove(nombre_audio)

# --- INTERFAZ DE USUARIO (STREAMLIT) ---
st.set_page_config(page_title="Shorts IA Tool", layout="wide")
st.title("🤖 YouTube Shorts IA Transcriber")

# Barra lateral para configuración
with st.sidebar:
    st.header("Configuración")
    api_key_input = st.text_input("YouTube API Key", type="password", value=obtener_api_key() or "")
    if st.button("Guardar API Key"):
        guardar_api_key(api_key_input)
        st.success("Clave guardada localmente.")

    st.info("Asegúrate de guardar la API Key antes de empezar.")

# Validar API Key
API_KEY = obtener_api_key()
if not API_KEY:
    st.warning("Por favor, introduce tu YouTube API Key en la barra lateral.")
    st.stop()

try:
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=API_KEY)
except Exception as e:
    st.error(f"Error iniciando API de YouTube: {e}")
    st.stop()

# Pestañas principales
tab1, tab2 = st.tabs(["🕷️ Scraper de Canal", "📝 Transcriptor IA"])

# --- TAB 1: SCRAPER ---
with tab1:
    st.subheader("Extraer Shorts de un Canal")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        url_canal = st.text_input("URL del Canal", placeholder="https://www.youtube.com/@NombreCanal")
    
    with col2:
        limite = st.number_input("Límite de videos", min_value=10, max_value=500, value=50)

    if st.button("Iniciar Scraping", key="btn_scraper"):
        if url_canal:
            with st.spinner("Procesando... esto puede tardar unos segundos."):
                df_resultado, ruta_archivo = ejecutar_scraper(url_canal, limite, youtube)
            
            if df_resultado is not None:
                st.success(f"¡Éxito! Se encontraron {len(df_resultado)} Shorts.")
                st.dataframe(df_resultado)
                
                with open(ruta_archivo, "rb") as f:
                    st.download_button(
                        label="📥 Descargar Excel",
                        data=f,
                        file_name=os.path.basename(ruta_archivo),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        else:
            st.error("Introduce una URL válida.")

# --- TAB 2: TRANSCRIPTOR ---
with tab2:
    st.subheader("Procesar y Transcribir")
    
    # Cargar modelo una sola vez
    modelo = cargar_modelo_whisper()
    
    opcion = st.radio("Modo de operación:", ["Procesar Excel generado", "Link Directo (Modo Francotirador)"], horizontal=True)

    if opcion == "Procesar Excel generado":
        archivos = [f for f in os.listdir(CARPETA_EXCEL) if f.endswith('.xlsx')]
        if not archivos:
            st.info("No hay archivos Excel. Ve a la pestaña 'Scraper' para generar uno.")
        else:
            archivo_sel = st.selectbox("Selecciona archivo Excel:", archivos)
            
            if archivo_sel:
                ruta_excel = os.path.join(CARPETA_EXCEL, archivo_sel)
                df = pd.read_excel(ruta_excel)
                
                # Normalizar columnas por si acaso
                df = df.rename(columns={'nº de vistas': 'Vistas', 'Titulo del short': 'Titulo', 'link del video': 'Link'})
                
                # Filtro pendientes
                pendientes = df[df['Validador'] == 'Pendiente'].sort_values(by='Vistas', ascending=False)
                
                st.write(f"Pendientes: {len(pendientes)} videos.")
                
                # Mostrar top 5 para seleccionar
                if not pendientes.empty:
                    st.dataframe(pendientes.head(5)[['Titulo', 'Vistas', 'Link']])
                    
                    procesar = st.button("Transcribir Top 5 Pendientes")
                    if procesar:
                        items_a_procesar = pendientes.head(5)
                        progress_bar = st.progress(0)
                        
                        for i, (idx, row) in enumerate(items_a_procesar.iterrows()):
                            st.markdown(f"**Procesando: {row['Titulo'][:40]}...**")
                            
                            guion, ruta_txt = transcribir_video(
                                row['Titulo'], 
                                row['Link'], 
                                row.get('Descripción', ''), 
                                modelo
                            )
                            
                            if guion:
                                df.at[idx, 'Validador'] = 'Completado'
                                st.success(f"Transcripción completada: {os.path.basename(ruta_txt)}")
                                with open(ruta_txt, "r", encoding="utf-8") as f:
                                    st.download_button(
                                        label=f"Descargar TXT {i+1}",
                                        data=f.read(),
                                        file_name=os.path.basename(ruta_txt),
                                        key=f"dl_{i}"
                                    )
                            else:
                                st.error(f"Error en video {row['Titulo']}: {ruta_txt}")
                            
                            progress_bar.progress((i + 1) / len(items_a_procesar))
                        
                        # Guardar cambios en Excel
                        df.to_excel(ruta_excel, index=False)
                        st.rerun() # Recargar para actualizar estados
                else:
                    st.success("¡No hay videos pendientes en este Excel!")

    elif opcion == "Link Directo (Modo Francotirador)":
        url_directa = st.text_input("Pega el link del Short:")
        
        if st.button("Transcribir Link"):
            if url_directa:
                with st.spinner("Descargando y transcribiendo..."):
                    # Obtener metadatos
                    try:
                        video_id = url_directa.split("/shorts/")[1].split("?")[0] if "/shorts/" in url_directa else url_directa.split("v=")[-1]
                        res = youtube.videos().list(part="snippet", id=video_id).execute()
                        snippet = res['items'][0]['snippet']
                        titulo = snippet.get('title')
                        descripcion = snippet.get('description', 'Sin descripción')
                        
                        guion, ruta = transcribir_video(titulo, url_directa, descripcion, modelo)
                        
                        if guion:
                            st.subheader("📄 Resultado")
                            st.text_area("Transcripción", guion, height=300)
                            with open(ruta, "r", encoding="utf-8") as f:
                                st.download_button(
                                    label="📥 Descargar Transcripción TXT",
                                    data=f.read(),
                                    file_name=os.path.basename(ruta),
                                    mime="text/plain"
                                )
                        else:
                            st.error(f"Error: {ruta}")
                            
                    except Exception as e:
                        st.error(f"No se pudo obtener info del video: {e}")
            else:
                st.warning("Introduce un link.")