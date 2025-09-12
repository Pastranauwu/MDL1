# Proyecto de Scraping y Fine-Tuning de LLM para Información de la UAM

## 1. Descripción General

Este repositorio tiene como objetivo principal la extracción, procesamiento y utilización de información pública de los sitios web de la Universidad Autónoma Metropolitana (UAM) para entrenar un Modelo de Lenguaje Grande (LLM). El propósito final es crear un asistente virtual especializado, capaz de responder preguntas sobre trámites, planes de estudio, eventos, y otros aspectos relevantes para la comunidad universitaria, utilizando técnicas de Supervised Fine-Tuning (SFT) con QLoRA.

## 2. Objetivo

Desarrollar un LLM especializado que sirva como una fuente de información centralizada y confiable para la comunidad de la UAM, reduciendo la dificultad de encontrar datos dispersos en múltiples sitios web oficiales.

## 3. Arquitectura del Proyecto

El proyecto se divide en tres fases principales, siguiendo un flujo de trabajo de Extracción, Transformación y Carga (ETL) para los datos, y finalmente, el entrenamiento del modelo.

1.  **Fase 1: Extracción (Scraping)**: Obtención del texto crudo desde las páginas web de la UAM.
2.  **Fase 2: Proceso de ETL (Transformación)**: Limpieza, filtrado y estructuración de los datos extraídos para crear un dataset de alta calidad.
3.  **Fase 3: Entrenamiento del Modelo (Carga y SFT)**: Fine-tuning de un modelo de lenguaje pre-entrenado con el dataset curado.

---

## 4. Fases del Proyecto a Detalle

### Fase 1: Extracción de Datos (Scraping)

El proceso de extracción se realiza mediante scripts de Python, contenidos en la carpeta `CONTENEDORES`. Estos scripts están diseñados para navegar los sitios de la UAM y volcar el contenido de texto en archivos `.txt`.

-   **Herramientas**: Python, BeautifulSoup, Scrapy (o similar).
-   **Ejecución**: Los scrapers están dockerizados para facilitar su ejecución y portabilidad. Se pueden iniciar con `docker-compose up`.
-   **Almacenamiento**: La información extraída se almacena en la carpeta `DATA/`, organizada en subdirectorios temáticos (ej. `Licenciaturas`, `Servicio_Social`, `Idiomas`).

### Fase 2: Proceso de ETL (Extracción, Transformación y Carga)

Esta es la fase más crítica, ya que la calidad del dataset final depende de ella. El objetivo es transformar el texto plano extraído en un formato de pregunta-respuesta (`prompt`-`completion`) o instructivo que sea útil para el fine-tuning.

La estrategia propuesta es utilizar un modelo de lenguaje auxiliar (ej. un modelo pre-entrenado de 4B de parámetros) para automatizar la clasificación y el filtrado de la información.

#### **Proceso de Filtrado y Correlación con Modelo Auxiliar:**

1.  **Definir Categorías de Interés**: Para cada directorio en `DATA/` (ej. `Servicio_Social`), se debe crear una lista de preguntas o temas clave que se espera encontrar.
    -   *Ejemplo para `Servicio_Social`*: "¿Cuáles son los requisitos para el servicio social?", "¿Dónde puedo ver los proyectos disponibles?", "¿Cómo se liberan las horas?".

2.  **Iterar sobre los Datos Crudos**: Se crea un script que recorra cada archivo `.txt` de los directorios de `DATA/`.

3.  **Consulta al Modelo Auxiliar**: Por cada archivo de texto, el script enviará su contenido al modelo de 4B parámetros junto con una pregunta (prompt) diseñada para validar la relevancia del texto.

    **Ejemplo de Prompt para el modelo auxiliar:**

    ```
    Contexto:
    ---
    {pegar aquí el contenido completo del archivo .txt}
    ---
    Pregunta:
    Basado únicamente en el contexto proporcionado, ¿encuentras información relevante sobre los requisitos para realizar el servicio social en la UAM? Responde solo con "Sí" o "No".
    ```

4.  **Clasificación y Almacenamiento**:
    -   Si el modelo auxiliar responde "Sí", el contenido de ese archivo `.txt` se considera relevante para la categoría y se guarda en una nueva estructura de datos curada.
    -   Si responde "No", el archivo se descarta para esa categoría específica.

5.  **Generación del Dataset Final**: Una vez filtrado el contenido, se puede usar el mismo modelo auxiliar (o uno más avanzado) para generar pares de pregunta-respuesta a partir de los textos relevantes, creando así el dataset final para el SFT.

    **Ejemplo de Prompt para generar pares Q&A:**

    ```
    Contexto:
    ---
    {pegar aquí el texto relevante y filtrado sobre el servicio social}
    ---
    Tarea:
    Basado en el contexto, genera 5 preguntas y sus respuestas directas en formato JSON. Las preguntas deben ser las que un estudiante haría.

    Ejemplo de formato:
    [
      {
        "pregunta": "¿Un alumno de la UAM puede iniciar su servicio social si debe materias?",
        "respuesta": "No, para iniciar el servicio social es requisito haber cubierto al menos el 70% de los créditos de la licenciatura y no deber ninguna materia."
      }
    ]
    ```

### Fase 3: Entrenamiento del Modelo (SFT con QLoRA)

Con el dataset de alta calidad en formato instructivo o Q&A, se procede al fine-tuning.

-   **Modelo Base**: Se recomienda un modelo open-source de tamaño mediano (ej. 7B a 13B de parámetros) que tenga un buen rendimiento en español.
-   **Técnica**: **QLoRA (Quantized Low-Rank Adaptation)**. Esta técnica permite realizar el fine-tuning de modelos grandes en hardware de consumo (como una GPU con 16-24 GB de VRAM) al cuantizar el modelo base y entrenar solo un pequeño número de parámetros adicionales (adaptadores).
-   **Proceso**:
    1.  Cargar el modelo base en 4 bits.
    2.  Añadir los adaptadores LoRA.
    3.  Entrenar los adaptadores con el dataset curado.
    4.  Una vez entrenado, fusionar los adaptadores con el modelo base o cargarlos dinámicamente para la inferencia.
-   **Resultado**: Un LLM especializado y eficiente, ajustado específicamente al dominio de la información de la UAM.

## 5. Cómo Contribuir

1.  **Mejorar los Scrapers**: Añadir nuevas fuentes de datos o mejorar la robustez de los existentes.
2.  **Optimizar el Proceso ETL**: Refinar los prompts para el modelo auxiliar o proponer métodos de filtrado más eficientes.
3.  **Experimentar con Modelos**: Probar diferentes modelos base o configuraciones de QLoRA para mejorar el rendimiento final.
4.  **Evaluar el Modelo**: Crear un conjunto de preguntas de evaluación para medir la precisión y utilidad del modelo entrenado.
