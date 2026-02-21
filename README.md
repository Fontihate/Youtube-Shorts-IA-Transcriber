# 🚀 YouTube Shorts IA: Scraper & Transcriber

![Python](https://img.shields.io/badge/python-3.10+-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![YouTube](https://img.shields.io/badge/YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI%20Whisper-412991?style=for-the-badge&logo=openai&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Local_AI-black?style=for-the-badge&logo=ollama&logoColor=white)

Kit de herramientas modular para la extracción de métricas de YouTube Shorts y generación de guiones automáticos mediante Inteligencia Artificial (OpenAI Whisper). Incluye corrección gramatical avanzada con LLMs locales (Ollama).

---

## ✨ Características Principales

*   🖥️ **Interfaz Web Unificada**: Panel de control visual con Streamlit para gestionar scraping, transcripción y corrección en un solo lugar.
*   🔍 **Scraping Inteligente y Rápido**: Obtiene títulos, vistas y enlaces mediante la API de YouTube. Usa **Multithreading** para validar Shorts a gran velocidad.
*   🧠 **Transcripción con IA**: Utiliza el motor **Whisper de OpenAI** para convertir audio en texto.
*   ✨ **Restauración Inteligente**: Corrige errores de transcripción (puntuación, ortografía) usando Ollama y técnicas de **Few-Shot Prompting** para evitar alucinaciones.
*   ⚡ **Aceleración por GPU**: Detección automática de tarjetas NVIDIA (CUDA).
*   📂 **Gestión Organizada**: Genera archivos Excel y archivos `.txt` refinados listos para producción.

---

## 🛠️ Instalación y Requisitos

### 1. Requisitos Previos
*   **Python 3.10+**
*   **FFmpeg**: Imprescindible para procesar audio.
    *   *Windows*: Descárgalo y añade la carpeta `bin` al PATH.
    *   *Mac*: `brew install ffmpeg`
*   **Ollama**: Necesario para la función de restauración de guiones.
    *   Instálalo desde [ollama.com](https://ollama.com).
    *   Descarga el modelo usado por la app: `ollama pull llama3`

### 2. Clonar e Instalar

1.  `git clone https://github.com/Fontihate/Youtube-Shorts-IA-Transcriber.git`
2.  `cd Youtube-Shorts-IA-Transcriber`
3.  `pip install -r requirements.txt`

---

## 🚀 Guía de Uso

### Opción A: Interfaz Web (Recomendado) 🌟

Ejecuta la aplicación con:
`streamlit run app.py`

El navegador se abrirá con tres pestañas principales:

1.  **🕷️ Scraper**: Introduce la URL de un canal y extrae los Shorts más vistos a un Excel.
2.  **📝 Transcriptor**: Carga el Excel o pega un link directo. Descarga el audio y transcribe con Whisper.
3.  **✨ Restaurar**: Selecciona una transcripción bruta y usa IA local (Llama3) para corregir puntuación y ortografía automáticamente.

### Opción B: Modo Terminal (Scripts Clásicos)

#### Paso 1: Scraping
`python scraper_shorts.py`

#### Paso 2: Transcripción
`python procesador_ia.py`

#### Paso 3: Restauración (Corrección IA)
`python restaurador_guiones.py`
*   *Nota*: Este paso corrige los errores típicos de los audios a texto y genera archivos limpios en `/guiones_refinados`.

---

## 📁 Estructura del Proyecto

    ├── app.py                    # 🌟 Interfaz Web Streamlit
    ├── scraper_shorts.py         # Módulo de scraping (CLI)
    ├── procesador_ia.py          # Módulo de transcripción (CLI)
    ├── restaurador_guiones.py    # Módulo de corrección IA (CLI)
    ├── requirements.txt          # Dependencias
    ├── API_KEYS.json             # Credenciales (Local - ¡No subir!)
    ├── resultados_excel/         # Datos crudos (XLSX)
    ├── transcripciones_completas/# Transcripciones brutas
    └── guiones_refinados/        # 📝 Guiones corregidos por IA

---

## ⚙️ Detalles Técnicos

*   **Few-Shot Prompting**: El restaurador de guiones usa ejemplos dentro del prompt para guiar a la IA y evitar que invente información.
*   **Multithreading**: El scraper valida cientos de videos en segundos consultando las URLs en paralelo.
*   **Robustez**: El procesador de IA usa `tempfile` para no dejar archivos de audio residuales.

---

## ⚠️ Seguridad
**NUNCA SUBAS `API_KEYS.json` A GITHUB.** El archivo `.gitignore` está configurado para bloquearlo.

---

## 👨‍💻 Autor
Hecho con ❤️ por [Fontihate](https://github.com/Fontihate)

---
¡Si te sirve, dale una ⭐!

Nota sobre el desarrollo: Este proyecto ha sido diseñado, estructurado y supervisado por [Fontihate](https://github.com/Fontihate), utilizando herramientas de IA como asistente de código para la generación de sintaxis y optimización de scripts.
