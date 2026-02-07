import os
import json
import requests
import pandas as pd
import googleapiclient.discovery

# CONFIGURACIÓN DINÁMICA
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_JSON = os.path.join(BASE_DIR, "API_KEYS.json")
CARPETA_SALIDA = os.path.join(BASE_DIR, "resultados_excel")

if not os.path.exists(CARPETA_SALIDA): os.makedirs(CARPETA_SALIDA)

def gestionar_api_key():
    if not os.path.exists(RUTA_JSON):
        print(f"\n[CONFIG] Creando API_KEYS.json en {BASE_DIR}")
        key = input("Introduce tu YouTube API Key: ").strip()
        with open(RUTA_JSON, 'w') as f: json.dump({"youtube_api": key}, f, indent=4)
        return key
    with open(RUTA_JSON, 'r') as f: return json.load(f).get("youtube_api")

def es_short_real(video_id):
    url = f"https://www.youtube.com/shorts/{video_id}"
    try:
        res = requests.head(url, allow_redirects=True, timeout=5)
        return "/shorts/" in res.url
    except: return False

def obtener_info_canal(youtube, url):
    print(f"[PROCESO] Identificando canal...")
    handle = url.split("@")[1].split("/")[0] if "@" in url else url.split("/")[-1]
    search = youtube.search().list(q=handle, type="channel", part="snippet", maxResults=1).execute()
    if not search['items']: raise Exception("Canal no encontrado.")
    return search['items'][0]['id']['channelId'], search['items'][0]['snippet']['title']

def main():
    api_key = gestionar_api_key()
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
    
    canal_url = input("\nIntroduce el link del canal: ").strip()
    
    try:
        ch_id, ch_name = obtener_info_canal(youtube, canal_url)
        print(f"[INFO] Canal detectado: {ch_name}")
        
        # --- NUEVO VALIDADOR DE CANTIDAD ---
        limite_input = input("¿Cuántos videos recientes quieres analizar? (Escribe un número o 'todos'): ").strip().lower()
        limite = 999999 if limite_input == 'todos' else int(limite_input)

        ch_res = youtube.channels().list(part="contentDetails", id=ch_id).execute()
        uploads_id = ch_res['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        v_ids = []
        next_p = None
        print(f"[PROCESO] Obteniendo lista de videos (máximo {limite})...")
        
        while len(v_ids) < limite:
            # Pedimos máximo 50 por página (límite de la API)
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

        print(f"[INFO] Analizando {len(v_ids)} videos para filtrar Shorts y extraer descripciones...")
        data = []
        for i in range(0, len(v_ids), 50):
            batch = v_ids[i:i+50]
            v_res = youtube.videos().list(part="snippet,statistics", id=",".join(batch)).execute()
            for v in v_res['items']:
                print(f"  > Validando: {v['snippet']['title'][:40]}...", end="\r")
                if es_short_real(v['id']):
                    data.append({
                        "Titulo": v['snippet']['title'],
                        "Vistas": int(v['statistics'].get('viewCount', 0)),
                        "Link": f"https://www.youtube.com/shorts/{v['id']}",
                        "Descripción": v['snippet'].get('description', 'Sin descripción'),
                        "Validador": "Pendiente"
                    })

        if data:
            # Ordenar por visitas de más a menos
            df = pd.DataFrame(data).sort_values(by='Vistas', ascending=False)
            nombre_limpio = "".join(c for c in ch_name if c.isalnum() or c in ' -_').strip() + ".xlsx"
            ruta_final = os.path.join(CARPETA_SALIDA, nombre_limpio)
            df.to_excel(ruta_final, index=False)
            print(f"\n\n[ÉXITO] Archivo '{nombre_limpio}' creado con {len(data)} Shorts.")
            print(f"[RUTA] {ruta_final}")
        else:
            print("\n[AVISO] No se encontraron Shorts en la muestra analizada.")

    except Exception as e:
        print(f"\n[ERROR] {e}")

if __name__ == "__main__":
    main()
