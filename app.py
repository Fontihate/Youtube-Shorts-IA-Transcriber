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
import ollama # Importamos Ollama para la restauración

# --- CONFIGURACIÓN DE RUTAS Y CONSTANTES ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CARPETA_EXCEL = os.path.join(BASE_DIR, "resultados_excel")
CARPETA_TXT = os.path.join(BASE_DIR, "transcripciones_completas")
CARPETA_REFINADOS = os.path.join(BASE_DIR, "guiones_refinados")
RUTA_JSON = os.path.join(BASE_DIR, "API_KEYS.json")

# Crear carpetas si no existen
for c in [CARPETA_EXCEL, CARPETA_TXT, CARPETA_REFINADOS]:
    if not os.path.exists(c): os.makedirs(c)

# --- FUNCIONES DE UTILIDAD ---
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

# --- LÓGICA DEL SCRAPER ---
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

# --- LÓGICA IA (TRANSCRIPCIÓN) ---
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

# --- LÓGICA IA (RESTAURACIÓN) ---
def restaurar_guion_con_ia(guion_bruto):
    """Versión mejorada con Few-Shot Prompting para web."""
    ejemplos = """
EJEMPLO 1:
ENTRADA: "oye tio, no se si sabes pero la ia va a cambair el mundo"
SALIDA: "Oye tío, no sé si sabes, pero la IA va a cambiar el mundo."
"""
    prompt_sistema = (
        "Eres un corrector ortográfico automático.\n"
        "REGLAS: NO añadas intros. NO expliques. SOLO corrige ortografía y puntuación.\n"
        f"{ejemplos}"
    )
    prompt_usuario = f"ENTRADA:\n{guion_bruto}\n\nSALIDA:"

    try:
        response = ollama.chat(model='llama3', messages=[
            {'role': 'system', 'content': prompt_sistema},
            {'role': 'user', 'content': prompt_usuario},
        ], options={"temperature": 0.0, "stop": ["ENTRADA:", "EJEMPLO"]})
        return response['message']['content'].strip()
    except Exception as e:
        return f"Error de IA: {e}"

# --- INTERFAZ DE USUARIO (STREAMLIT) ---
st.set_page_config(page_title="Shorts IA Tool", layout="wide")
st.title("🤖 YouTube Shorts IA Transcriber")

# Barra lateral
with st.sidebar:
    st.header("Configuración")
    api_key_input = st.text_input("YouTube API Key", type="password", value=obtener_api_key() or "")
    if st.button("Guardar API Key"):
        guardar_api_key(api_key_input)
        st.success("Clave guardada localmente.")
    st.info("Asegúrate de tener Ollama corriendo para la restauración de guiones.")

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
tab1, tab2, tab3 = st.tabs(["🕷️ Scraper de Canal", "📝 Transcriptor IA", "✨ Restaurar Guiones"])

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
            with st.spinner("Procesando..."):
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
    modelo = cargar_modelo_whisper()
    
    opcion = st.radio("Modo de operación:", ["Procesar Excel generado", "Link Directo"], horizontal=True)

    if opcion == "Procesar Excel generado":
        archivos = [f for f in os.listdir(CARPETA_EXCEL) if f.endswith('.xlsx')]
        if not archivos:
            st.info("No hay archivos Excel. Ve a la pestaña 'Scraper' para generar uno.")
        else:
            archivo_sel = st.selectbox("Selecciona archivo Excel:", archivos)
            
            if archivo_sel:
                ruta_excel = os.path.join(CARPETA_EXCEL, archivo_sel)
                df = pd.read_excel(ruta_excel)
                df = df.rename(columns={'nº de vistas': 'Vistas', 'Titulo del short': 'Titulo', 'link del video': 'Link'})
                pendientes = df[df['Validador'] == 'Pendiente'].sort_values(by='Vistas', ascending=False)
                
                st.write(f"Pendientes: {len(pendientes)} videos.")
                
                if not pendientes.empty:
                    st.dataframe(pendientes.head(5)[['Titulo', 'Vistas', 'Link']])
                    
                    procesar = st.button("Transcribir Top 5 Pendientes")
                    if procesar:
                        items = pendientes.head(5)
                        progress = st.progress(0)
                        
                        for i, (idx, row) in enumerate(items.iterrows()):
                            st.markdown(f"**Procesando: {row['Titulo'][:40]}...**")
                            guion, ruta_txt = transcribir_video(row['Titulo'], row['Link'], row.get('Descripción', ''), modelo)
                            
                            if guion:
                                df.at[idx, 'Validador'] = 'Completado'
                                st.success(f"OK: {os.path.basename(ruta_txt)}")
                            else:
                                st.error(f"Error en video {row['Titulo']}")
                            
                            progress.progress((i + 1) / len(items))
                        
                        df.to_excel(ruta_excel, index=False)
                        st.rerun()

    elif opcion == "Link Directo":
        url_directa = st.text_input("Pega el link del Short:")
        if st.button("Transcribir Link"):
            if url_directa:
                with st.spinner("Procesando..."):
                    try:
                        video_id = url_directa.split("/shorts/")[1].split("?")[0]
                        res = youtube.videos().list(part="snippet", id=video_id).execute()
                        titulo = res['items'][0]['snippet']['title']
                        descripcion = res['items'][0]['snippet'].get('description', '')
                        
                        guion, ruta = transcribir_video(titulo, url_directa, descripcion, modelo)
                        if guion:
                            st.text_area("Resultado", guion, height=300)
                    except Exception as e:
                        st.error(f"Error: {e}")

# --- TAB 3: RESTAURAR GUIONES (NUEVO) ---
with tab3:
    st.subheader("Restaurar y Limpiar Guiones con IA")
    st.markdown("Utiliza **Ollama (Llama3)** para corregir la puntuación y ortografía de las transcripciones brutas.")
    
    archivos_txt = [f for f in os.listdir(CARPETA_TXT) if f.endswith('.txt')]
    
    if not archivos_txt:
        st.info("No hay transcripciones en la carpeta 'transcripciones_completas' para restaurar.")
    else:
        archivo_sel = st.selectbox("Selecciona la transcripción a restaurar:", archivos_txt)
        
        if st.button("Restaurar Guion"):
            ruta_in = os.path.join(CARPETA_TXT, archivo_sel)
            
            with open(ruta_in, "r", encoding="utf-8") as f:
                contenido_bruto = f.read()
                # Extraemos solo la parte del guion
                texto_bruto = contenido_bruto.split("GUIÓN:")[1].split("DESCRIPCIÓN:")[0] if "GUIÓN:" in contenido_bruto else contenido_bruto

            with st.spinner("La IA está corrigiendo el texto... (Esto puede tardar unos segundos)"):
                texto_corregido = restaurar_guion_con_ia(texto_bruto)
            
            st.markdown("#### Resultado Corregido:")
            st.success("¡Corrección completada!")
            st.text_area("Texto Final", texto_corregido, height=300)
            
            # Botón para guardar
            nombre_salida = f"GUION_LIMPIO_{archivo_sel}"
            ruta_out = os.path.join(CARPETA_REFINADOS, nombre_salida)
            
            st.download_button(
                label="💾 Descargar Guion Limpio",
                data=texto_corregido,
                file_name=nombre_salida,
                mime="text/plain"
            )