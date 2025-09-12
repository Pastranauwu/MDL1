import os
import time
import json
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

# Configuración del logging
logging.basicConfig(level=logging.INFO)


# --- Configuración ---
# Rutas de las carpetas (dentro del contenedor)
INPUT_DIR = "/app/input_data"
OUTPUT_DIR = "/app/output_data"

# Configuración de Ollama (desde variables de entorno)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:270m")
SYSTEM_PROMPT_QUESTION = os.getenv("SYSTEM_PROMPT_QUESTION", "¿El texto contiene información relevante?")

# --- Lógica del Procesador ETL ---

def query_ollama(text_content, question):
    """
    Envía el contenido del texto y una pregunta a la API de Ollama y obtiene una respuesta.
    """
    full_prompt = f"""
    Contexto:
    ---
    {text_content}
    ---
    Pregunta:
    {question} Responde únicamente con "Sí" o "No".
    """
    
    try:
        logging.info(f"Consultando a Ollama con el modelo '{OLLAMA_MODEL}'...")
        response = requests.post(
            f"{OLLAMA_HOST}",
            json={
                "model": OLLAMA_MODEL,
                "prompt": full_prompt,
                "stream": False, # Esperamos la respuesta completa
                "options": {
                    "temperature": 0.0 # Para respuestas deterministas (Sí/No)
                }
            },
            timeout=120 # Timeout de 60 segundos
        )
        response.raise_for_status()
        
        # Extrae la respuesta y la limpia
        result = response.json()
        answer = result.get("response", "").strip()
        
        # Asegurarnos de que la respuesta sea solo "Sí" o "No"
        if "sí" in answer.lower():
            return "Sí"
        elif "no" in answer.lower():
            return "No"
        else:
            logging.warning(f"Respuesta no esperada del modelo: '{answer}'")
            return "Indeterminado"

    except requests.exceptions.RequestException as e:
        logging.error(f"Error al conectar con Ollama: {e}")
        return None

def process_file(filepath):
    """
    Procesa un único archivo de texto: lo lee, consulta a Ollama y guarda el resultado.
    """
    filename = os.path.basename(filepath)
    logging.info(f"Nuevo archivo detectado: {filename}")

    # 1. Leer el contenido del archivo
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logging.error(f"Error al leer el archivo {filepath}: {e}")
        return

    # 2. Consultar al modelo de lenguaje
    answer = query_ollama(content, SYSTEM_PROMPT_QUESTION)

    if answer is None:
        logging.warning("No se pudo obtener respuesta de Ollama. Reintentando más tarde.")
        return

    # 3. Guardar el resultado en un archivo JSON
    output_data = {
        "source_file": filename,
        "question": SYSTEM_PROMPT_QUESTION,
        "is_relevant": answer,
        "original_content": content
    }
    
    output_filename = f"{os.path.splitext(filename)[0]}.json"
    output_filepath = os.path.join(OUTPUT_DIR, output_filename)
    
    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)
        print(f"Resultado guardado en: {output_filepath}")
    except Exception as e:
        print(f"Error al guardar el archivo JSON: {e}")

    # 4. (Opcional) Eliminar el archivo de entrada una vez procesado
    # os.remove(filepath)
    # print(f"Archivo de entrada eliminado: {filename}")


# --- Monitor de Archivos ---

class TxtFileHandler(FileSystemEventHandler):
    """

    Manejador de eventos que reacciona a la creación de archivos .txt.
    """
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.txt'):
            # Esperar un poco para asegurar que el archivo se haya escrito completamente
            time.sleep(1)
            process_file(event.src_path)

if __name__ == "__main__":
    # Asegurarse de que los directorios de entrada y salida existan
    logging.info("Verificando directorios...")
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    logging.info("Iniciando servicio de ETL...")
    logging.info(f"Monitoreando la carpeta: {INPUT_DIR}")
    logging.info(f"Los resultados se guardarán en: {OUTPUT_DIR}")
    logging.info(f"Usando el host de Ollama: {OLLAMA_HOST}")

    # Configurar y empezar el observador
    event_handler = TxtFileHandler()
    observer = Observer()
    observer.schedule(event_handler, INPUT_DIR, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
