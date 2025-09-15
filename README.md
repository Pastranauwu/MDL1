# README - Proyecto de Scraping para Información de la UAM

## Descripción General

Este proyecto implementa un sistema de scraping específico diseñado para extraer información de páginas web. El script busca respuestas a un conjunto de preguntas organizadas por categorías temáticas.

## Funcionalidades Principales

- **Scraping Dirigido**: Extrae información específica de URLs predefinidas
- **Búsqueda Contextual**: Localiza respuestas a preguntas organizadas por categorías
- **Procesamiento de Datos**: Limpia y estructura la información obtenida
- **Exportación de Resultados**: Guarda los datos en formato JSON para su posterior uso

## Estructura del Proyecto

### Archivos Principales

- `mapeo.py`: Script principal que contiene la lógica de scraping
- `servicio.json`: Archivo de salida con los resultados del scraping (generado automáticamente)

### Dependencias

El proyecto requiere las siguientes bibliotecas de Python:

- `requests`: Para realizar solicitudes HTTP
- `bs4` (BeautifulSoup): Para analizar y extraer información de HTML
- `json`: Para manejar datos en formato JSON
- `re`: Para operaciones con expresiones regulares
- `urllib.parse`: Para manipulación de URLs
- `time`: Para gestionar pausas entre solicitudes

### Instalación de Dependencias

```bash
pip install requests beautifulsoup4
```

## Configuración y Uso

### URLs Objetivo

El script está configurado para scrapear dos URLs específicas:
1. Página principal de UAM Iztapalapa: `http://www.iztapalapa.uam.mx/`
2. Página de preguntas frecuentes: `https://cse.izt.uam.mx/index.php/home/preguntas`

### Categorías y Preguntas

El cuestionario está organizado en 11 categorías con preguntas específicas:

1. **Becas**: Información sobre tipos de becas y convocatorias
2. **Proyecto Terminal**: Procesos y requisitos para proyectos terminales
3. **Quinta oportunidad**: Información sobre cursos intertrimestrales
4. **Actividades culturales**: Grupos y actividades culturales disponibles
5. **COSIB**: Información sobre el Centro de Operación de Servicios Institucionales y Bibliotecas
6. **Representante estudiantil**: Datos sobre representación estudiantil
7. **Laboratorios de la UAM**: Laboratorios de investigación disponibles
8. **Supercómputo**: Información sobre recursos de supercomputación
9. **Derechos de autor**: Aspectos legales sobre proyectos y servicios sociales
10. **Eventos UAMI**: Eventos y oportunidades de participación
11. **Tutores**: Información sobre el sistema de tutorías

### Ejecución del Script

```bash
python mapeo.py
```

### Salida Esperada

El script generará:
- Mensajes de progreso en la consola
- Un archivo `servicio.json` con las respuestas encontradas
- Un resumen estadístico del proceso

## Estructura de los Resultados

El archivo JSON resultante tiene la siguiente estructura:

```json
{
  "Categoría": {
    "Pregunta": {
      "respuestas_directas": [],
      "informacion_relacionada": [],
      "enlaces_relevantes": [],
      "fuentes": []
    }
  }
}
```

## Consideraciones Técnicas

### Política de Scraping

- El script incluye un User-Agent para simular un navegador real
- Implementa pausas entre solicitudes (1 segundo) para evitar sobrecargar los servidores
- Maneja excepciones para conexiones fallidas o errores HTTP
