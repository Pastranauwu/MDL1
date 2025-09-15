import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin
import time


def extraer_paginas_uam():
    """
    Función principal para hacer scraping específico de las dos páginas proporcionadas
    """

    # URLs específicas a scrapear
    urls_a_extraer = [
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
            "¿Dónde puedo consultar los eventos dentro de la UAMI para participar en la organización o logística? (aplicar examen de admisión, atención de módulos informativos, atención de stand en la kermes UAMI, etc.)"
        ],
        "Tutores": [
            "¿Cuál es su función?",
            "¿Quién lo asigna?",
            "¿Todos tienen uno?",
            "¿Puedo cambiar de tutor?"
        ]
    }

    # Headers para simular un navegador
    encabezados = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/91.0.4472.124 Safari/537.36'
    }

    print("Iniciando scraping específico de las páginas proporcionadas...")
    print(f"URLs a scrapear: {urls_a_extraer}")
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
        for url in urls_a_extraer:
            print(f"Extrayendo: {url}")
            try:
                # Hacer la solicitud HTTP
                respuesta = requests.get(url, headers=encabezados, timeout=15)
                respuesta.raise_for_status()

                # Parsear el contenido HTML
                sopa = BeautifulSoup(respuesta.content, 'html.parser')

                # Buscar información para cada pregunta
                for categoria, preguntas in cuestionario.items():
                    for pregunta in preguntas:
                        resultado_pregunta = buscar_info_pregunta(sopa, pregunta, categoria, url)

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
                            resultado_pregunta['enlaces_relevantes']
                        ):
                            resultados[categoria][pregunta]['fuentes'].append(url)

                time.sleep(1)  # Espera entre solicitudes

            except requests.exceptions.RequestException as e:
                print(f"Error al acceder a {url}: {e}")
                continue
            except Exception as e:
                print(f"Error inesperado procesando {url}: {e}")
                continue

        # Procesar y limpiar resultados
        resultados = procesar_resultados(resultados)

        # Guardar resultados en JSON
        with open('uam_persona2_respuestas_especificas.json', 'w', encoding='utf-8') as f:
            json.dump(resultados, f, ensure_ascii=False, indent=2)

        print(f"\nScraping completado. Se procesaron {len(urls_a_extraer)} páginas.")
        print("Resultados guardados en 'uam_persona2_respuestas_especificas.json'")

        # Generar un resumen
        generar_resumen(resultados)

        return resultados

    except Exception as e:
        print(f"Error inesperado: {e}")
        return None


def buscar_info_pregunta(sopa, pregunta, categoria, url_base):
    """
    Busca información relacionada con una pregunta específica en el HTML
    """
    resultados = {
        'respuestas_directas': [],
        'informacion_relacionada': [],
        'enlaces_relevantes': [],
        'fuentes': []
    }

    # Palabras clave de la pregunta
    palabras_clave = extraer_palabras_clave(pregunta)

    # 1. Buscar respuestas directas
    elementos_texto = sopa.find_all(['p', 'div', 'li', 'td', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span'])
    for elem in elementos_texto:
        texto = elem.get_text().strip()
        if texto and len(texto) > 10:
            # Respuesta directa
            if es_respuesta_directa(texto, pregunta, palabras_clave):
                texto_corto = texto[:800] + "..." if len(texto) > 800 else texto
                resultados['respuestas_directas'].append(texto_corto)

            # Información relacionada
            elif contiene_palabras_clave(texto, palabras_clave):
                texto_corto = texto[:500] + "..." if len(texto) > 500 else texto
                resultados['informacion_relacionada'].append(texto_corto)

    # 2. Buscar enlaces relevantes
    enlaces = sopa.find_all('a', href=True)
    for enlace in enlaces:
        texto_enlace = enlace.get_text().strip()
        href = enlace['href']
        if texto_enlace and (contiene_palabras_clave(texto_enlace, palabras_clave) or contiene_palabras_clave(href, palabras_clave)):
            url_completa = urljoin(url_base, href)
            resultados['enlaces_relevantes'].append({
                'texto': texto_enlace,
                'url': url_completa,
                'relevancia': calcular_relevancia(texto_enlace, pregunta, palabras_clave)
            })

    return resultados


def es_respuesta_directa(texto, pregunta, palabras_clave):
    """
    Determina si un texto parece ser una respuesta directa a la pregunta
    """
    texto_lower = texto.lower()
    # Patrones que indican una respuesta directa
    patrones = [
        r'es\s+necesario\s+', r'debe\s+', r'se\s+requiere\s+', r'proceso\s+', r'pasos\s+', r'procedimiento\s+',
        r'puede\s+', r'debe\s+contactar\s+', r'dirigirse\s+a\s+', r'consultar\s+en\s+', r'página\s+web',
        r'sitio\s+web', r'portal\s+', r'link\s+', r'enlace\s+', r'url\s+'
    ]

    coincide_palabras = contiene_palabras_clave(texto, palabras_clave)
    coincide_patron = any(re.search(p, texto_lower) for p in patrones)

    return coincide_palabras and (coincide_patron or len(texto) < 300)


def calcular_relevancia(texto_enlace, pregunta, palabras_clave):
    """
    Calcula la relevancia de un enlace para la pregunta
    """
    relevancia = 0
    texto_lower = texto_enlace.lower()

    for palabra in palabras_clave:
        if palabra in texto_lower:
            relevancia += 1

    # Palabras que aumentan relevancia
    impulso = ['guía', 'manual', 'proceso', 'procedimiento', 'requisitos', 'convocatoria', 'registro',
               'formulario', 'solicitud', 'información', 'contacto', 'horarios', 'calendario',
               'fechas', 'costos', 'precios', 'tarifas']
    for t in impulso:
        if t in texto_lower:
            relevancia += 2

    return relevancia


def extraer_palabras_clave(pregunta):
    """
    Extrae palabras clave de una pregunta
    """
    stop_words = {'qué', 'dónde', 'cómo', 'cuál', 'quién', 'cuándo', 'por', 'para',
                  'mi', 'me', 'hay', 'puedo', 'puede', 'de', 'la', 'el', 'los', 'las',
                  'un', 'una', 'unos', 'unas', 'y', 'o', 'con', 'al', 'del', 'se',
                  'su', 'sus', 'lo', 'le', 'es', 'son', 'tiene', 'tienen', 'algún',
                  'alguna', 'algunos', 'algunas'}

    palabras = re.findall(r'\b[a-záéíóúñ]+\b', pregunta.lower())
    return [p for p in palabras if p not in stop_words and len(p) > 2]


def contiene_palabras_clave(texto, palabras_clave):
    """
    Verifica si un texto contiene las palabras clave
    """
    if not palabras_clave:
        return False
    texto_lower = texto.lower()
    return any(p in texto_lower for p in palabras_clave)


def procesar_resultados(resultados):
    """
    Procesa y limpia los resultados eliminando duplicados y organizando la información
    """
    for categoria in resultados:
        for pregunta in resultados[categoria]:
            # Eliminar duplicados
            resultados[categoria][pregunta]['respuestas_directas'] = list(set(resultados[categoria][pregunta]['respuestas_directas']))
            resultados[categoria][pregunta]['informacion_relacionada'] = list(set(resultados[categoria][pregunta]['informacion_relacionada']))

            # Ordenar enlaces
            if resultados[categoria][pregunta]['enlaces_relevantes']:
                resultados[categoria][pregunta]['enlaces_relevantes'].sort(key=lambda x: x['relevancia'], reverse=True)

            # Eliminar duplicados de enlaces
            vistos = set()
            unicos = []
            for enlace in resultados[categoria][pregunta]['enlaces_relevantes']:
                if enlace['url'] not in vistos:
                    vistos.add(enlace['url'])
                    unicos.append(enlace)
            resultados[categoria][pregunta]['enlaces_relevantes'] = unicos

            # Limitar cantidad
            resultados[categoria][pregunta]['respuestas_directas'] = resultados[categoria][pregunta]['respuestas_directas'][:3]
            resultados[categoria][pregunta]['informacion_relacionada'] = resultados[categoria][pregunta]['informacion_relacionada'][:5]
            resultados[categoria][pregunta]['enlaces_relevantes'] = resultados[categoria][pregunta]['enlaces_relevantes'][:5]

    return resultados


def generar_resumen(resultados):
    """
    Genera un resumen de los resultados obtenidos
    """
    print("\n" + "=" * 60)
    print("RESUMEN DE RESULTADOS")
    print("=" * 60)

    total = 0
    con_respuesta = 0
    con_enlaces = 0

    for categoria, preguntas in resultados.items():
        print(f"\n{categoria}:")
        for pregunta, datos in preguntas.items():
            total += 1
            tiene_respuesta = len(datos['respuestas_directas']) > 0
            tiene_enlaces = len(datos['enlaces_relevantes']) > 0

            if tiene_respuesta:
                con_respuesta += 1
                estado = "✓ Respondida"
            elif tiene_enlaces:
                con_enlaces += 1
                estado = "➤ Enlaces encontrados"
            else:
                estado = "✗ Sin información"

            print(f" - {pregunta}: {estado}")

    print("\n" + "=" * 60)
    print(f"Total preguntas: {total}")
    print(f"Preguntas con respuestas directas: {con_respuesta}")
    print(f"Preguntas con enlaces relevantes: {con_enlaces}")
    print(f"Preguntas sin información: {total - con_respuesta - con_enlaces}")
    print("=" * 60)


if __name__ == "__main__":
    # Ejecutar scraping
    resultados = extraer_paginas_uam()

    # Si hay error, generar datos de ejemplo
    if not resultados:
        print("\nGenerando datos de ejemplo debido a error en el scraping...")
        datos_ejemplo = {
            "Becas": {
                "¿Qué tipo de becas hay?": {
                    "respuestas_directas": [
                        "La UAM Iztapalapa ofrece diferentes tipos de becas: becas de excelencia académica, becas de apoyo económico, becas para movilidad estudiantil, becas deportivas y culturales.",
                        "Existen becas internas y externas, incluyendo becas de manutención, transporte y apoyo a la titulación."
                    ],
                    "informacion_relacionada": [
                        "Las becas se otorgan según criterios académicos y socioeconómicos establecidos en cada convocatoria.",
                        "Para mayor información sobre becas, consultar la página de la Dirección de Servicios Educativos."
                    ],
                    "enlaces_relevantes": [
                        {"texto": "Becas y apoyos", "url": "http://www.iztapalapa.uam.mx/index.php/becas-y-apoyos", "relevancia": 5},
                        {"texto": "Convocatorias de becas", "url": "http://www.iztapalapa.uam.mx/index.php/becas/convocatorias", "relevancia": 4}
                    ],
                    "fuentes": ["http://www.iztapalapa.uam.mx/"]
                }
            }
        }
        with open('servicio.json', 'w', encoding='utf-8') as f:
            json.dump(datos_ejemplo, f, ensure_ascii=False, indent=2)
        print("Datos de ejemplo generados: 'servicio.json'")
