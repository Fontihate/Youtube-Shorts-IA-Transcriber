import os
import pandas as pd
import whisper
import torch
import re
import json
import googleapiclient.discovery
import tempfile
from yt_dlp import YoutubeDL

# --- CONFIGURACIÓN DE RUTAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CARPETA_EXCEL = os.path.join(BASE_DIR, "resultados_excel")
CARPETA_TXT = os.path.join(BASE_DIR, "transcripciones_completas")
RUTA_JSON = os.path.join(BASE_DIR, "API_KEYS.json")

for c in [CARPETA_EXCEL, CARPETA_TXT]:
    if not os.path.exists(c): os.makedirs(c)

def limpiar_nombre(texto):
    return re.sub(r'[\\/*?:"<>|]', "", str(texto))[:80]

def obtener_api_key():
    if not os.path.exists(RUTA_JSON):
        raise Exception(f"No se encontró API_KEYS.json. Ejecuta primero el Script 1.")
    with open(RUTA_JSON, 'r') as f:
        return json.load(f).get("youtube_api")

def extraer_video_id(url):
    """Extrae el ID del video de cualquier URL de YouTube usando Regex."""
    patrones = [
        r'(?:v=|\/shorts\/|youtu\.be\/)([a-zA-Z0-9_-]{11})' # Estándar, Shorts, Cortos
    ]
    for patron in patrones:
        match = re.search(patron, url)
        if match:
            return match.group(1)
    return None

def obtener_metadatos_manual(youtube, url):
    """Obtiene título y descripción de un link directo usando la API."""
    try:
        video_id = extraer_video_id(url)
        if not video_id: raise ValueError("No se pudo extraer el ID del video")
        
        res = youtube.videos().list(part="snippet", id=video_id).execute()
        if res['items']:
            snippet = res['items'][0]['snippet']
            return snippet.get('title'), snippet.get('description', 'Sin descripción')
    except Exception as e:
        print(f"Error metadatos: {e}")
    return "Video Manual", "Descripción no disponible"

def seleccionar_archivo():
    archivos = [f for f in os.listdir(CARPETA_EXCEL) if f.endswith('.xlsx')]
    if not archivos:
        print(f"[ERROR] No hay archivos Excel en {CARPETA_EXCEL}")
        return None
    print("\n--- EXCEL DISPONIBLES ---")
    for i, f in enumerate(archivos, 1): print(f"[{i}] {f}")
    try:
        idx = int(input("\nSelecciona el número del archivo: ")) - 1
        return os.path.join(CARPETA_EXCEL, archivos[idx])
    except: return None

def transcribir_y_guardar(titulo, link, descripcion, modelo, device):
    """Lógica central de descarga, transcripción y guardado en TXT."""
    print(f"\n[PROCESANDO] {titulo[:50]}...")
    
    # Usamos un archivo temporal real para evitar conflictos
    temp_audio_file = None
    
    try:
        # Descarga a archivo temporal
        with tempfile.NamedTemporaryFile(suffix=".m4a", delete=False) as tmp:
            temp_audio_path = tmp.name
            temp_audio_file = temp_audio_path # Guardamos la ruta para borrarlo luego

        ydl_opts = {
            'format': 'm4a/bestaudio/best', 
            'outtmpl': temp_audio_path.replace('.m4a', ''), # yt-dlp añade la extensión
            'quiet': True, 
            'no_warnings': True
        }
        
        # yt-dlp descarga, hay que controlar que el archivo exista
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
        
        # A veces yt-dlp descarga con otro nombre, buscamos el archivo
        # Si usamos outtmpl sin extensión, yt-dlp pone la que quiere.
        # Simplificación: usamos el path temporal directo.
        
        if not os.path.exists(temp_audio_path):
             # Pequeño fix si yt-dlp cambió la extensión (poco común en m4a forzado)
             # Buscamos cualquier archivo que empiece por el nombre temporal en el dir actual
             base_temp = temp_audio_path.replace('.m4a', '')
             encontrado = [f for f in os.listdir(os.path.dirname(base_temp) or '.') if f.startswith(os.path.basename(base_temp))]
             if encontrado:
                 temp_audio_path = os.path.join(os.path.dirname(base_temp) or '.', encontrado[0])

        # Transcripción
        print("   -> Transcribiendo audio con IA...")
        res = modelo.transcribe(temp_audio_path, fp16=(device=="cuda"))
        guion = res['text'].strip()

        # Guardar TXT
        nombre_fichero = limpiar_nombre(titulo) + ".txt"
        ruta_txt = os.path.join(CARPETA_TXT, nombre_fichero)
        with open(ruta_txt, "w", encoding="utf-8") as f:
            f.write(f"TITULO: {titulo}\n\nGUIÓN: {guion}\n\nDESCRIPCIÓN: {descripcion}")
        
        print(f"   [OK] Archivo generado en /transcripciones_completas/")
        return True
    except Exception as e:
        print(f"   [ERROR] {e}")
        return False
    finally:
        # Limpieza estricta
        if temp_audio_file and os.path.exists(temp_audio_file):
            try: os.remove(temp_audio_file)
            except: pass

def main():
    print("--- PROCESADOR DE SHORTS IA ---")
    print("[1] Procesar desde archivo Excel (Modo Explorador)")
    print("[2] Procesar link directo de Short (Modo Francotirador)")
    
    modo = input("\nSelecciona una opción: ").strip()

    # Cargar Modelo IA
    print("\n[IA] Preparando Whisper...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    modelo = whisper.load_model("base", device=device)

    if modo == "1":
        ruta_excel = seleccionar_archivo()
        if not ruta_excel: return
        df = pd.read_excel(ruta_excel)
        
        df = df.rename(columns={'nº de vistas': 'Vistas', 'Titulo del short': 'Titulo', 'link del video': 'Link'})
        pendientes = df[df['Validador'] == 'Pendiente'].sort_values(by='Vistas', ascending=False).head(5)
        
        if pendientes.empty:
            print("[INFO] No hay videos pendientes."); return

        print("\n--- TOP 5 SHORTS PENDIENTES ---")
        for i, (idx, row) in enumerate(pendientes.iterrows(), 1):
            print(f"[{i}] {int(row['Vistas']):,}: {row['Titulo'][:60]}")

        eleccion = input("\nVideos a procesar (1,3 o 'todos'): ").strip().lower()
        indices = pendientes.index.tolist() if eleccion == 'todos' else [pendientes.index[int(x)-1] for x in eleccion.split(',')]

        for idx in indices:
            row = df.loc[idx]
            exito = transcribir_y_guardar(row['Titulo'], row['Link'], row.get('Descripción', 'Sin descripción'), modelo, device)
            if exito: df.at[idx, 'Validador'] = 'Completado'
        
        df.to_excel(ruta_excel, index=False)
        print("\n[FIN] Excel actualizado.")

    elif modo == "2":
        url = input("\nPega el link del YouTube Short: ").strip()
        api_key = obtener_api_key()
        youtube_api = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
        
        titulo, descripcion = obtener_metadatos_manual(youtube_api, url)
        transcribir_y_guardar(titulo, url, descripcion, modelo, device)
        print("\n[FIN] Proceso manual terminado.")

if __name__ == "__main__":
    main()
