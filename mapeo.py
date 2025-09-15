import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin
import time

def scrape_uam_specific_pages():
    """
    Función principal para hacer scraping específico de las dos páginas proporcionadas
    """
    # URLs específicas a scrapear
    urls_a_scrapear = [
        "http://www.iztapalapa.uam.mx/",
        "https://cse.izt.uam.mx/index.php/home/preguntas"
    ]
    
    # Preguntas del cuestionario organizadas por categoría
    cuestionario = {
        "Becas": [
            "¿Qué tipo de becas hay?",
            "¿En cuál link se pueden ver las fechas de convocatoria de las becas?"
        ],
        "Proyecto Terminal": [
            "¿Cuál es el proceso para solicitar la apertura de mi grupo?",
            "¿Dónde puedo consultar qué proyectos tiene cada profesor?",
            "¿Puedo hacer proyecto terminal con profesores que no pertenezcan al grupo de profesores que soportan mi licenciatura?",
            "¿Dónde debo entregar mi reporte de proyecto terminal con las firmas de mi asesor y coordinador?",
            "¿Mi proyecto terminal lo puedo vender fuera de la UAM?"
        ],
        "Quinta oportunidad": [
            "¿Puedo elegir a mis sinodales?",
            "¿Puedo solicitar un profesor o ayudante que me ayude a preparar mi UEA?",
            "¿Qué UEA puedo pasar llevando cursos intertrimestrales?"
        ],
        "Actividades culturales": [
            "¿Dónde puedo consultar qué actividades hay para inscribirme?",
            "¿Me interesa integrarme al grupo de danza dónde puedo consultar los horarios?",
            "¿Me interesa integrarme al coro de la UAM dónde puedo consultar los horarios?",
            "¿Hay grupo de teatro en la UAM? ¿cómo puedo integrarme?"
        ],
        "COSIB": [
            "¿Qué es COSIB?",
            "¿Qué áreas tiene COSIB?",
            "¿Dónde puedo consultar los costos de los servicios de COSIB en la UAMI?"
        ],
        "Representante estudiantil": [
            "¿Cómo puedo saber quién es y dónde localizarlo?",
            "¿Para qué me sirve conocer a mi representante estudiantil?"
        ],
        "Laboratorios de la UAM": [
            "¿Qué laboratorios de investigación tiene la UAMI?",
            "¿Dónde puedo consultar qué profesores los dirigen y qué líneas de investigación tiene cada laboratorio?"
        ],
        "Supercómputo": [
            "¿Qué es?",
            "¿Quién lo dirige?",
            "¿Dónde puedo consultar qué proyectos dirige?",
            "¿Cómo puedo tener acceso a su equipo?"
        ],
        "Derechos de autor": [
            "¿Mi servicio social lo puedo vender fuera de la UAMI?",
            "¿Mi proyecto terminal lo puedo vender fuera de la UAM?"
        ],
        "Eventos UAMI": [
            "¿Dónde puedo consultar los eventos dentro de la UAMI para participar en la organización o logística?"
        ],
        "Tutores": [
            "¿Cuál es su función?",
            "¿Quién lo asigna?",
            "¿Todos tienen uno?",
            "¿Puedo cambiar de tutor?"
        ]
    }
    
    #simular un navegador
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, como Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    print("Iniciando scraping específico de las páginas proporcionadas...")
    print(f"URLs a scrapear: {urls_a_scrapear}")
    print(f"Total de preguntas: {sum(len(p) for p in cuestionario.values())}")
    print("-" * 50)
    
    try:
        # Estructura para almacenar resultados
        resultados = {}
        for categoria, preguntas in cuestionario.items():
            resultados[categoria] = {}
            for pregunta in preguntas:
                resultados[categoria][pregunta] = {
                    'respuestas_directas': [],
                    'informacion_relacionada': [],
                    'enlaces_relevantes': [],
                    'fuentes': []
                }
        
        # Scrapear cada URL
        for url in urls_a_scrapear:
            print(f"Scrapeando: {url}")
            
            try:
                # Hacer la solicitud HTTP
                respuesta = requests.get(url, headers=headers, timeout=15)
                respuesta.raise_for_status()
                
                # Analizar el contenido HTML
                soup = BeautifulSoup(respuesta.content, 'html.parser')
                
                # Buscar información para cada pregunta
                for categoria, preguntas in cuestionario.items():
                    for pregunta in preguntas:
                        resultado_pregunta = find_question_info(soup, pregunta, categoria, url)
                        
                        # Agregar resultados encontrados
                        if resultado_pregunta['respuestas_directas']:
                            resultados[categoria][pregunta]['respuestas_directas'].extend(resultado_pregunta['respuestas_directas'])
                        
                        if resultado_pregunta['informacion_relacionada']:
                            resultados[categoria][pregunta]['informacion_relacionada'].extend(resultado_pregunta['informacion_relacionada'])
                        
                        if resultado_pregunta['enlaces_relevantes']:
                            resultados[categoria][pregunta]['enlaces_relevantes'].extend(resultado_pregunta['enlaces_relevantes'])
                        
                        if url not in resultados[categoria][pregunta]['fuentes'] and (
                            resultado_pregunta['respuestas_directas'] or 
                            resultado_pregunta['informacion_relacionada'] or 
                            resultado_pregunta['enlaces_relevantes']):
                            resultados[categoria][pregunta]['fuentes'].append(url)
                
                time.sleep(1)  # Espera entre solicitudes
                
            except requests.exceptions.RequestException as e:
                print(f"Error al acceder a {url}: {e}")
                continue
            except Exception as e:
                print(f"Error inesperado procesando {url}: {e}")
                continue
        
        # Procesar y limpiar resultados
        resultados = process_results(resultados)
        
        # Guardar resultados en JSON
        with open('servicio.json', 'w', encoding='utf-8') as f:
            json.dump(resultados, f, ensure_ascii=False, indent=2)
        
        print(f"\nScraping completado. Se procesaron {len(urls_a_scrapear)} páginas.")
        print("Resultados guardados en 'uam_persona2_respuestas_especificas.json'")
        
        # Generar un resumen
        generate_summary(resultados)
        
        return resultados
        
    except Exception as e:
        print(f"Error inesperado: {e}")
        return None
