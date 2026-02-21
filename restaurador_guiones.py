import os
import ollama
import re

# --- CONFIGURACIÓN DE RUTAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CARPETA_ENTRADA = os.path.join(BASE_DIR, "transcripciones_completas")
CARPETA_SALIDA = os.path.join(BASE_DIR, "guiones_refinados")

if not os.path.exists(CARPETA_SALIDA):
    os.makedirs(CARPETA_SALIDA)

def leer_guion_bruto(ruta):
    """Extrae el bloque de GUIÓN del archivo original."""
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            contenido = f.read()
        if "GUIÓN:" in contenido:
            guion = contenido.split("GUIÓN:")[1].split("DESCRIPCIÓN:")[0]
            return guion.strip()
        return contenido.strip()
    except Exception as e:
        print(f"   [!] Error al leer: {e}")
        return None

def limpiar_basura_ia(texto):
    """Filtro final para asegurar que no haya comentarios de la IA."""
    lineas = texto.split('\n')
    # Palabras prohibidas que la IA usa a menudo para explicar lo que ha hecho
    basura = ('aquí', 'este', 'guion', 'corregido', 'título', 'revisado', 'contexto', 'transcripción', 'output')
    lineas_limpias = [l.strip() for l in lineas if l.strip() and not l.lower().startswith(basura)]
    return "\n\n".join(lineas_limpias).strip()

def restaurar_guion_con_ia(guion_bruto):
    """
    Estrategia: Few-Shot Prompting. 
    Le damos ejemplos de lo que SÍ queremos para que entienda el patrón
    sin inventar ni hablar de más.
    """
    # Definimos ejemplos de cómo debe comportarse
    ejemplos = """
EJEMPLO 1:
ENTRADA: "oye tio, no se si sabes pero la ia va a cambair el mundo porqe es muy fuerte"
SALIDA: "Oye tío, no sé si sabes, pero la IA va a cambiar el mundo porque es muy fuerte."

EJEMPLO 2:
ENTRADA: "el otro dia vi un video en yutub que decia que los cohes vuelan"
SALIDA: "El otro día vi un video en YouTube que decía que los coches vuelan."

EJEMPLO 3:
ENTRADA: "hola gente como estan bienvenidos a otro video hoy vamos a ver esto"
SALIDA: "Hola gente, ¿cómo están? Bienvenidos a otro video, hoy vamos a ver esto."
"""

    prompt_sistema = (
        "Eres un corrector ortográfico y de puntuación automático.\n"
        "TU ÚNICA FUNCIÓN: Corregir errores de transcripción (fonéticos) y añadir puntuación.\n"
        "REGLAS:\n"
        "1. NO añades introducciones ni explicaciones.\n"
        "2. NO cambias el sentido ni las palabras, solo corriges ortografía.\n"
        "3. RESPETAS el tono informal si lo hay.\n"
        "4. OUTPUT SOLO EL TEXTO CORREGIDO.\n\n"
        f"{ejemplos}"
    )

    prompt_usuario = f"ENTRADA:\n{guion_bruto}\n\nSALIDA:"

    print(f"   -> La IA está limpiando los errores de audio...")
    
    try:
        response = ollama.chat(model='llama3', messages=[
            {'role': 'system', 'content': prompt_sistema},
            {'role': 'user', 'content': prompt_usuario},
        ], options={"temperature": 0.0, "stop": ["ENTRADA:", "EJEMPLO"]}) # Temperature 0 para creatividad cero
        
        return limpiar_basura_ia(response['message']['content'])
    except Exception as e:
        return f"Error: {e}"

def main():
    print("\n" + "="*50)
    print(" PASO 3: RESTAURADOR DE GUIONES (FIDELIDAD TOTAL) ")
    print("="*50)

    archivos = [f for f in os.listdir(CARPETA_ENTRADA) if f.endswith('.txt')]
    if not archivos:
        print("[ERROR] No hay archivos en 'transcripciones_completas'."); return

    print("Guiones disponibles para restaurar:")
    for i, f in enumerate(archivos, 1):
        print(f"[{i}] {f}")

    try:
        entrada = input("\nSelecciona el número de los archivos a procesar (ej: 1 o 1,3,5 o 'todos'): ").strip().lower()
        indices_a_procesar = []

        if entrada == 'todos':
            indices_a_procesar = range(len(archivos))
        else:
            numeros_seleccionados = [int(num.strip()) - 1 for num in entrada.split(',')]
            for num in numeros_seleccionados:
                if 0 <= num < len(archivos):
                    indices_a_procesar.append(num)
                else:
                    print(f"[AVISO] El número {num+1} está fuera de rango y será ignorado.")

    except ValueError:
        print("[ERROR] Entrada no válida. Usa números, comas o la palabra 'todos'.")
        return

    if not indices_a_procesar:
        print("[INFO] No se seleccionaron archivos para procesar.")
        return

    for idx in indices_a_procesar:
        nombre_in = archivos[idx]
        print(f"\n[TRABAJANDO] {nombre_in}...")
        
        bruto = leer_guion_bruto(os.path.join(CARPETA_ENTRADA, nombre_in))
        
        if bruto:
            guion_limpio = restaurar_guion_con_ia(bruto)
            
            nombre_out = f"GUION_LIMPIO_{nombre_in}"
            with open(os.path.join(CARPETA_SALIDA, nombre_out), "w", encoding="utf-8") as f:
                f.write(guion_limpio)
            
            print(f"   [OK] Restauración completada.")
            print(f"\n--- GUION RESTAURADO ---")
            print(guion_limpio[:200] + "...")
            print("="*50)

if __name__ == "__main__":
    main()
    