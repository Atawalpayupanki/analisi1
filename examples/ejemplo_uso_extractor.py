#!/usr/bin/env python3
"""
Ejemplo de uso del módulo de extracción de artículos.

Este script muestra cómo usar el módulo de extracción de artículos
de forma programática (sin CLI).

NOTA: Este es un EJEMPLO de cómo sería la API. Los módulos aún no están implementados.
"""

from pathlib import Path
import json
import yaml
from typing import List, Dict

# Importaciones del módulo (a implementar)
# from article_processor import process_articles, ProcessingReport
# from article_downloader import download_article_html
# from article_extractor import extract_article_text
# from article_cleaner import clean_article_text


def load_config(config_path: str = "config/extractor_config.yaml") -> dict:
    """Carga configuración desde archivo YAML."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_news_items(input_file: str = "data/output.jsonl") -> List[Dict]:
    """Carga noticias filtradas desde archivo JSONL."""
    items = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))
    return items


def save_results(results: List[Dict], output_file: str = "data/articles_full.jsonl"):
    """Guarda resultados en archivo JSONL."""
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')


# ============================================================
# EJEMPLO 1: Uso Básico
# ============================================================

def ejemplo_basico():
    """Ejemplo de uso básico del módulo."""
    print("=" * 60)
    print("EJEMPLO 1: Uso Básico")
    print("=" * 60)
    
    # 1. Cargar configuración
    config = load_config()
    print(f"✓ Configuración cargada")
    
    # 2. Cargar noticias filtradas
    news_items = load_news_items()
    print(f"✓ {len(news_items)} noticias cargadas")
    
    # 3. Procesar artículos (API simplificada)
    # report = process_articles(
    #     input_file="data/output.jsonl",
    #     config=config
    # )
    
    # 4. Mostrar resultados
    # print(f"\n✓ Procesamiento completado:")
    # print(f"  - Total: {report.total_articles}")
    # print(f"  - Exitosos: {report.successful}")
    # print(f"  - Fallidos: {report.total_articles - report.successful}")
    
    print("\n[NOTA: Módulo aún no implementado]")


# ============================================================
# EJEMPLO 2: Procesar Un Solo Artículo
# ============================================================

def ejemplo_articulo_individual():
    """Ejemplo de procesamiento de un artículo individual."""
    print("\n" + "=" * 60)
    print("EJEMPLO 2: Procesar Artículo Individual")
    print("=" * 60)
    
    # Artículo de ejemplo
    news_item = {
        "nombre_del_medio": "El País",
        "enlace": "https://elpais.com/internacional/2025-11-26/ejemplo.html",
        "titular": "Ejemplo de titular sobre China",
        "fecha": "2025-11-26T10:00:00+00:00",
        "descripcion": "Descripción del artículo..."
    }
    
    print(f"\nProcesando: {news_item['titular']}")
    print(f"URL: {news_item['enlace']}")
    
    # 1. Descargar HTML
    # html, final_url, status = download_article_html(
    #     url=news_item['enlace'],
    #     timeout=15,
    #     headers={'User-Agent': 'Mozilla/5.0...'}
    # )
    
    # 2. Extraer texto
    # extraction_result = extract_article_text(html, final_url)
    
    # 3. Limpiar texto
    # clean_text = clean_article_text(extraction_result.texto)
    
    # 4. Resultado final
    # article_result = {
    #     **news_item,
    #     'texto': clean_text,
    #     'idioma': extraction_result.idioma,
    #     'scrape_status': extraction_result.extraction_status,
    #     'char_count': len(clean_text),
    #     'word_count': len(clean_text.split())
    # }
    
    print("\n[NOTA: Módulo aún no implementado]")


# ============================================================
# EJEMPLO 3: Configuración Personalizada
# ============================================================

def ejemplo_config_personalizada():
    """Ejemplo con configuración personalizada."""
    print("\n" + "=" * 60)
    print("EJEMPLO 3: Configuración Personalizada")
    print("=" * 60)
    
    # Configuración personalizada (sin archivo YAML)
    custom_config = {
        'downloader': {
            'timeout': 20,  # Más tiempo
            'max_retries': 5,  # Más reintentos
            'delay_between_requests_same_domain': 2.0  # Más cortés
        },
        'extractor': {
            'min_text_length_ok': 300,  # Más estricto
            'favor_precision': True
        },
        'processing': {
            'concurrency': 3,  # Más conservador
            'max_articles_per_run': 50  # Limitar cantidad
        },
        'fallback': {
            'playwright_enabled': False
        }
    }
    
    print("\nConfiguración personalizada:")
    print(f"  - Timeout: {custom_config['downloader']['timeout']}s")
    print(f"  - Concurrencia: {custom_config['processing']['concurrency']}")
    print(f"  - Límite: {custom_config['processing']['max_articles_per_run']} artículos")
    
    # Procesar con config personalizada
    # report = process_articles(
    #     input_file="data/output.jsonl",
    #     config=custom_config
    # )
    
    print("\n[NOTA: Módulo aún no implementado]")


# ============================================================
# EJEMPLO 4: Manejo de Errores
# ============================================================

def ejemplo_manejo_errores():
    """Ejemplo de manejo de errores."""
    print("\n" + "=" * 60)
    print("EJEMPLO 4: Manejo de Errores")
    print("=" * 60)
    
    # Simular procesamiento con errores
    results = [
        {
            'enlace': 'https://ejemplo1.com/articulo',
            'scrape_status': 'ok',
            'texto': 'Texto extraído correctamente...'
        },
        {
            'enlace': 'https://ejemplo2.com/articulo',
            'scrape_status': 'error_descarga',
            'error_message': 'HTTP 404 Not Found'
        },
        {
            'enlace': 'https://ejemplo3.com/articulo',
            'scrape_status': 'no_contenido_detectado',
            'error_message': 'Texto extraído muy corto (45 caracteres)'
        },
        {
            'enlace': 'https://ejemplo4.com/articulo',
            'scrape_status': 'blocked_fallback_required',
            'error_message': 'Captcha detected'
        }
    ]
    
    # Analizar resultados
    status_counts = {}
    for result in results:
        status = result['scrape_status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print("\nResultados del procesamiento:")
    for status, count in status_counts.items():
        print(f"  - {status}: {count}")
    
    # Identificar artículos problemáticos
    failed = [r for r in results if r['scrape_status'] != 'ok']
    
    print(f"\nArtículos fallidos ({len(failed)}):")
    for result in failed:
        print(f"  - {result['enlace']}")
        print(f"    Razón: {result['error_message']}")


# ============================================================
# EJEMPLO 5: Análisis de Resultados
# ============================================================

def ejemplo_analisis_resultados():
    """Ejemplo de análisis de resultados."""
    print("\n" + "=" * 60)
    print("EJEMPLO 5: Análisis de Resultados")
    print("=" * 60)
    
    # Simular resultados
    results = [
        {'texto': 'A' * 3500, 'scrape_status': 'ok', 'extraction_method': 'trafilatura'},
        {'texto': 'B' * 2800, 'scrape_status': 'ok', 'extraction_method': 'trafilatura'},
        {'texto': 'C' * 4200, 'scrape_status': 'ok', 'extraction_method': 'bs4_fallback'},
        {'texto': 'D' * 1500, 'scrape_status': 'ok', 'extraction_method': 'trafilatura'},
        {'texto': '', 'scrape_status': 'error_descarga', 'extraction_method': 'none'},
    ]
    
    # Calcular estadísticas
    successful = [r for r in results if r['scrape_status'] == 'ok']
    
    if successful:
        avg_length = sum(len(r['texto']) for r in successful) / len(successful)
        
        method_counts = {}
        for r in successful:
            method = r['extraction_method']
            method_counts[method] = method_counts.get(method, 0) + 1
        
        print(f"\nEstadísticas de texto extraído:")
        print(f"  - Artículos exitosos: {len(successful)}")
        print(f"  - Longitud promedio: {avg_length:.0f} caracteres")
        print(f"\nMétodos de extracción:")
        for method, count in method_counts.items():
            percentage = (count / len(successful)) * 100
            print(f"  - {method}: {count} ({percentage:.1f}%)")


# ============================================================
# EJEMPLO 6: Integración con Análisis
# ============================================================

def ejemplo_integracion_analisis():
    """Ejemplo de integración con análisis posterior."""
    print("\n" + "=" * 60)
    print("EJEMPLO 6: Integración con Análisis")
    print("=" * 60)
    
    # Cargar artículos completos
    # articles = load_news_items("data/articles_full.jsonl")
    
    # Filtrar solo exitosos
    # successful_articles = [
    #     a for a in articles 
    #     if a.get('scrape_status') == 'ok'
    # ]
    
    # Análisis de ejemplo: buscar términos específicos
    search_terms = ['xi jinping', 'taiwan', 'comercio']
    
    print(f"\nBuscando términos: {', '.join(search_terms)}")
    
    # for term in search_terms:
    #     matches = [
    #         a for a in successful_articles
    #         if term.lower() in a['texto'].lower()
    #     ]
    #     print(f"  - '{term}': {len(matches)} artículos")
    
    print("\n[NOTA: Módulo aún no implementado]")


# ============================================================
# MAIN
# ============================================================

def main():
    """Ejecuta todos los ejemplos."""
    print("\n" + "=" * 60)
    print("EJEMPLOS DE USO - Módulo de Extracción de Artículos")
    print("=" * 60)
    print("\nNOTA: Estos son ejemplos de cómo usar el módulo.")
    print("Los módulos aún no están implementados.\n")
    
    # Ejecutar ejemplos
    ejemplo_basico()
    ejemplo_articulo_individual()
    ejemplo_config_personalizada()
    ejemplo_manejo_errores()
    ejemplo_analisis_resultados()
    ejemplo_integracion_analisis()
    
    print("\n" + "=" * 60)
    print("PRÓXIMOS PASOS")
    print("=" * 60)
    print("\n1. Revisar documentación en docs/")
    print("2. Implementar módulos según especificación")
    print("3. Ejecutar tests con artículos reales")
    print("4. Ajustar configuración según resultados")
    print("\nVer: docs/RESUMEN_EJECUTIVO.md para roadmap completo\n")


if __name__ == '__main__':
    main()
