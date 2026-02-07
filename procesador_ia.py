import os
import pandas as pd
import whisper
import torch
import re
from yt_dlp import YoutubeDL

# Directorios dinámicos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CARPETA_EXCEL = os.path.join(BASE_DIR, "resultados_excel")
CARPETA_TXT = os.path.join(BASE_DIR, "transcripciones_completas")

# Crear carpetas si no existen
for c in [CARPETA_EXCEL, CARPETA_TXT]:
    if not os.path.exists(c): os.makedirs(c)

def limpiar_nombre(texto):
    """Limpia el título para que sea un nombre de archivo válido."""
    return re.sub(r'[\\/*?:"<>|]', "", str(texto))[:80]

def seleccionar_archivo():
    archivos = [f for f in os.listdir(CARPETA_EXCEL) if f.endswith('.xlsx')]
    if not archivos:
        print(f"[ERROR] No se encontraron archivos Excel en {CARPETA_EXCEL}")
        return None
    print("\n--- ARCHIVOS EXCEL DISPONIBLES ---")
    for i, f in enumerate(archivos, 1):
        print(f"[{i}] {f}")
    try:
        idx = int(input("\nSelecciona el número del archivo: ")) - 1
        return os.path.join(CARPETA_EXCEL, archivos[idx])
    except:
        return None

def main():
    ruta_excel = seleccionar_archivo()
    if not ruta_excel: return
    
    df = pd.read_excel(ruta_excel)

    # --- CORRECCIÓN DE COLUMNAS (Para compatibilidad) ---
    # Si el Excel es viejo, renombramos las columnas al formato nuevo
    mapeo_columnas = {
        'nº de vistas': 'Vistas',
        'Titulo del short': 'Titulo',
        'link del video': 'Link',
        'Descripción': 'Descripción'
    }
    df = df.rename(columns=mapeo_columnas)

    # Verificamos que las columnas críticas existan
    if 'Vistas' not in df.columns or 'Validador' not in df.columns:
        print("[ERROR] El Excel no tiene el formato esperado. Columnas encontradas:", df.columns.tolist())
        return

    # Filtrar Pendientes y ordenar por viralidad
    pendientes = df[df['Validador'] == 'Pendiente'].sort_values(by='Vistas', ascending=False).head(5)
    
    if pendientes.empty:
        print("[INFO] No hay videos pendientes de procesar en este archivo.")
        return

    print("\n--- TOP 5 SHORTS PENDIENTES ---")
    for i, (idx, row) in enumerate(pendientes.iterrows(), 1):
        vistas = f"{int(row['Vistas']):,}".replace(",", ".")
        print(f"[{i}] {vistas} vistas | {row['Titulo'][:60]}")

    eleccion = input("\nVideos a procesar (ej: 1,3 o 'todos'): ").strip().lower()
    indices_finales = []
    
    if eleccion == 'todos':
        indices_finales = pendientes.index.tolist()
    else:
        try:
            for s in eleccion.split(','):
                num = int(s.strip()) - 1
                indices_finales.append(pendientes.index[num])
        except:
            print("[ERROR] Selección no válida."); return

    # Cargar IA
    print("\n[IA] Cargando Whisper...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[MODO] Ejecutando en: {device.upper()}")
    modelo = whisper.load_model("base", device=device)

    for idx in indices_finales:
        row = df.loc[idx]
        titulo = str(row['Titulo'])
        print(f"\n[PROCESANDO] {titulo[:50]}...")
        
        try:
            # Descarga de Audio
            ydl_opts = {'format': 'm4a/bestaudio/best', 'outtmpl': 'temp_audio.%(ext)s', 'quiet': True}
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([row['Link']])
            
            # Transcripción
            print("   -> Transcribiendo audio...")
            res = modelo.transcribe("temp_audio.m4a", fp16=(device=="cuda"))
            guion = res['text'].strip()

            # Guardar TXT con la estructura solicitada
            nombre_fichero = limpiar_nombre(titulo) + ".txt"
            ruta_txt = os.path.join(CARPETA_TXT, nombre_fichero)
            
            # Manejo de descripción si no existe en archivos viejos
            descripcion = row.get('Descripción', 'No disponible en este archivo.')

            with open(ruta_txt, "w", encoding="utf-8") as f:
                f.write(f"TITULO: {titulo}\n\n")
                f.write(f"GUIÓN: {guion}\n\n")
                f.write(f"DESCRIPCIÓN: {descripcion}\n")

            df.at[idx, 'Validador'] = 'Completado'
            print(f"   [OK] TXT generado en /transcripciones_completas/")

        except Exception as e:
            print(f"   [ERROR] No se pudo procesar: {e}")
            df.at[idx, 'Validador'] = 'Error'
        
        if os.path.exists("temp_audio.m4a"):
            os.remove("temp_audio.m4a")

    # Guardar cambios
    df.to_excel(ruta_excel, index=False)
    print(f"\n[FIN] Excel actualizado. Revisa la carpeta 'transcripciones_completas'.")

if __name__ == "__main__":
    main()
