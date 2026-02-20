# 🚀 YouTube Shorts IA: Scraper & Transcriber

![Python](https://img.shields.io/badge/Python-3.10%2B-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![YouTube](https://img.shields.io/badge/YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white)
![OpenAI Whisper](https://img.shields.io/badge/OpenAI%20Whisper-412991?style=for-the-badge&logo=openai&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![NVIDIA CUDA](https://img.shields.io/badge/NVIDIA%20CUDA-76B900?style=for-the-badge&logo=nvidia&logoColor=white)

Kit de herramientas modular para la extracción de métricas de YouTube Shorts y generación de guiones automáticos mediante Inteligencia Artificial (OpenAI Whisper). Diseñado para ser portátil, eficiente y con una interfaz web moderna incluida.

---

## ✨ Características Principales

*   🖥️ **Interfaz Web Incluida**: Panel de control visual con Streamlit para gestionar el proceso sin tocar la terminal.
*   🔍 **Scraping Inteligente y Rápido**: Obtiene títulos, vistas y enlaces mediante la API de YouTube. Usa **Multithreading** para validar Shorts a gran velocidad.
*   📏 **Validación Real**: Filtra Shorts auténticos comprobando la estructura de la URL, detectando incluso los nuevos Shorts de hasta 3 minutos.
*   🧠 **Transcripción con IA**: Utiliza el motor **Whisper de OpenAI** para convertir audio en texto con alta precisión.
*   ⚡ **Aceleración por GPU**: Detección automática de tarjetas NVIDIA (CUDA) para transcripciones ultra rápidas.
*   📂 **Gestión Organizada**: Genera archivos Excel para análisis de datos y archivos `.txt` individuales con estructura profesional.

---

## 🛠️ Instalación y Requisitos

### 1. Requisitos Previos
*   **Python 3.10+**: Versión recomendada para compatibilidad con librerías de IA.
*   **FFmpeg**: **Imprescindible** para el procesamiento de audio.
    *   *Windows*: Descárgalo de la web oficial y añade la carpeta `bin` a tu PATH.
    *   *Mac*: `brew install ffmpeg`
    *   *Linux*: `sudo apt install ffmpeg`

### 2. Clonar e Instalar
Clona el repositorio e instala las dependencias:

1.  `git clone https://github.com/Fontihate/Youtube-Shorts-IA-Transcriber.git`
2.  `cd Youtube-Shorts-IA-Transcriber`
3.  `pip install -r requirements.txt`

---

## 🚀 Guía de Uso

Puedes utilizar esta herramienta de dos formas: mediante la **Interfaz Web** (recomendado) o mediante **Terminal** (scripts individuales).

### Opción A: Interfaz Web (Streamlit) 🌟
La forma más visual y sencilla de usar la herramienta.

1.  Ejecuta el comando: `streamlit run app.py`
2.  Se abrirá automáticamente una pestaña en tu navegador.
3.  Introduce tu **YouTube API Key** en la barra lateral (solo la primera vez).
4.  Navega entre las pestañas "Scraper" y "Transcriptor" para trabajar.

### Opción B: Modo Terminal (Scripts Clásicos)

#### Paso 1: Obtención de Datos (`scraper_shorts.py`)

1.  Ejecuta: `python scraper_shorts.py`
2.  Introduce el link del canal.
3.  Define cuántos videos analizar.
4.  El script validará en paralelo cuáles son Shorts reales y generará un Excel en `/resultados_excel`.

#### Paso 2: Generación de Guiones (`procesador_ia.py`)

1.  Ejecuta: `python procesador_ia.py`
2.  Selecciona el archivo Excel generado.
3.  Elige los videos a transcribir.
4.  La IA generará los archivos `.txt` en `/transcripciones_completas`.

---

## 📁 Estructura del Proyecto

    ├── app.py                    # 🌟 Interfaz Web Streamlit (NUEVO)
    ├── scraper_shorts.py         # Módulo de scraping (CLI)
    ├── procesador_ia.py          # Módulo de transcripción (CLI)
    ├── requirements.txt          # Dependencias del proyecto
    ├── API_KEYS.json             # Almacena tus credenciales (Local - Ignorado por Git)
    ├── resultados_excel/         # Base de datos generada (XLSX)
    └── transcripciones_completas/# Guiones finales generados (TXT)

---

## ⚙️ Detalles Técnicos y Optimización

*   **Multithreading**: El script de scraping utiliza `ThreadPoolExecutor` para validar cientos de videos en segundos, en lugar de hacer consultas una por una.
*   **Gestión de Temporales**: El procesador de IA utiliza `tempfile` para manejar los audios descargados, garantizando que no se dejen archivos residuales si el script falla.
*   **Compatibilidad**: Extrae IDs de video mediante Regex, soportando URLs de Shorts, URLs normales (`watch?v=`) y URLs cortas (`youtu.be`).

---

## ⚠️ Seguridad y Privacidad
Este proyecto genera un archivo local llamado `API_KEYS.json`. 
**NUNCA SUBAS ESTE ARCHIVO A GITHUB NI A NINGÚN REPOSITORIO PÚBLICO.** 

El proyecto incluye un archivo `.gitignore` configurado para ignorar automáticamente:
*   `API_KEYS.json`
*   Archivos temporales de audio (`*.m4a`, `*.mp3`)
*   Archivos de Python compilados (`__pycache__`)

---

## 👨‍💻 Autor
Hecho con ❤️ por [Fontihate](https://github.com/Fontihate)

---
¡Si este proyecto te ha ahorrado tiempo, dale una ⭐ en GitHub!
