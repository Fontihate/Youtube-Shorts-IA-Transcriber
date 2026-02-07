# 🚀 YouTube Shorts IA: Scraper & Transcriber

![Python](https://img.shields.io/badge/python-3.12+-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![YouTube](https://img.shields.io/badge/YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI%20Whisper-412991?style=for-the-badge&logo=openai&logoColor=white)
![NVIDIA](https://img.shields.io/badge/NVIDIA%20CUDA-76B900?style=for-the-badge&logo=nvidia&logoColor=white)

Kit de herramientas modular para la extracción de métricas de YouTube Shorts y generación de guiones automáticos mediante Inteligencia Artificial (OpenAI Whisper). Diseñado para ser portátil, eficiente y fácil de compartir en GitHub.

---

## ✨ Características Principales

*   🔍 **Scraping Inteligente**: Obtiene títulos, vistas, enlaces y descripciones oficiales mediante la API de YouTube.
*   📏 **Validación Real**: Filtra Shorts auténticos comprobando la estructura de la URL, evitando errores por duración técnica.
*   🧠 **Transcripción con IA**: Utiliza el motor **Whisper de OpenAI** para convertir audio en texto con alta precisión.
*   ⚡ **Aceleración por GPU**: Detección automática de tarjetas NVIDIA (CUDA) para transcripciones ultra rápidas.
*   📂 **Gestión Organizada**: Genera archivos Excel para análisis de datos y archivos `.txt` individuales con estructura profesional.

---

## 🛠️ Instalación y Requisitos

### 1. Requisitos del Sistema
*   **Python 3.12+**: Versión recomendada para compatibilidad con librerías de IA.
*   **FFmpeg**: Imprescindible para el procesamiento de audio (debe estar en el PATH del sistema).
*   **Node.js**: Recomendado para asegurar la estabilidad de las descargas de contenido de YouTube.

### 2. Configuración del Entorno
Instala todas las librerías necesarias con el siguiente comando:
```bash
pip install -r requirements.txt
```

---

## 🚀 Guía de Uso

### Paso 1: Obtención de Datos (`scraper_shorts.py`)
Ejecuta el primer script para analizar un canal completo. 
- Te pedirá el link del canal (ej: `https://www.youtube.com/@nombrecanal`).
- Te pedirá tu **YouTube API Key** (se guardará localmente en `API_KEYS.json`).
- Podrás elegir cuántos videos recientes analizar o escribir "todos".
- Los resultados se guardarán en la carpeta `resultados_excel/`.

### Paso 2: Generación de Guiones con IA (`procesador_ia.py`)
Ejecuta el segundo script para procesar los datos obtenidos.
- Selecciona el archivo Excel generado en el paso anterior.
- El script mostrará el **Top 5 de Shorts más vistos** con estado "Pendiente".
- Selecciona cuáles procesar y la IA generará los archivos `.txt` en `transcripciones_completas/`.

**Estructura de los archivos de salida (.txt):**
- **TITULO**: Título completo del video.
- **GUIÓN**: Transcripción íntegra generada por la IA.
- **DESCRIPCIÓN**: Descripción original del video en YouTube.

---

## 📁 Estructura del Proyecto

```text
├── scraper_shorts.py         # Módulo de extracción y scraping
├── procesador_ia.py          # Módulo de transcripción con IA
├── API_KEYS.json             # Almacena tus llaves de forma segura (Local)
├── resultados_excel/         # Base de datos generada (XLSX)
├── transcripciones_completas/   # Guiones finales generados (TXT)
├── requirements.txt          # Dependencias del proyecto
└── .gitignore                # Filtros de seguridad para Git
```

---

## ⚠️ Seguridad y Privacidad
Este proyecto genera un archivo local llamado `API_KEYS.json`. 
**NUNCA SUBAS ESTE ARCHIVO A GITHUB NI A NINGÚN REPOSITORIO PÚBLICO.** El proyecto incluye un archivo `.gitignore` configurado para ignorar automáticamente tus credenciales y archivos temporales.

---

## 👨‍💻 Autor
Desarrollado por **Andrés Fontaneda**.

---
¡Si te gusta el proyecto, dale una ⭐ en GitHub!
```
