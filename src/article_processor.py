"""
Módulo orquestador para el procesamiento de artículos.
Coordina la descarga, extracción y limpieza.

Ahora usa el CSV maestro centralizado para leer artículos pendientes
y actualizar su estado tras el procesamiento.
"""

import logging
import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

try:
    from src.article_downloader import download_article_html
    from src.article_extractor import extract_article_text
    from src.article_cleaner import clean_article_text
    from src.article_enricher import detect_language
    from src.custom_scrapers import scrape_custom
    from src.noticias_db import obtener_db, guardar_db

except ImportError:
    from article_downloader import download_article_html
    from article_extractor import extract_article_text
    from article_cleaner import clean_article_text
    from article_enricher import detect_language
    from custom_scrapers import scrape_custom
    from noticias_db import obtener_db, guardar_db


logger = logging.getLogger(__name__)

@dataclass
class ArticleResult:
    """Resultado completo del procesamiento de un artículo."""
    # Datos originales
    nombre_del_medio: str
    enlace: str
    titular: str
    fecha: str
    descripcion: str
    
    # Datos extraídos
    texto: str = ""
    idioma: Optional[str] = None
    autor: Optional[str] = None
    fecha_publicacion: Optional[str] = None
    
    # Metadatos del proceso
    scrape_status: str = "pending" # ok, error_descarga, no_contenido, blocked, error_parseo
    error_message: str = ""
    extraction_method: str = "none"
    char_count: int = 0
    word_count: int = 0
    download_time: float = 0.0
    extraction_time: float = 0.0

@dataclass
class ProcessingReport:
    """Resumen de la ejecución."""
    start_time: str
    end_time: str = ""
    duration_seconds: float = 0.0
    total_articles: int = 0
    successful: int = 0
    failed_download: int = 0
    failed_extraction: int = 0
    no_content: int = 0
    blocked: int = 0
    extraction_methods: Dict[str, int] = field(default_factory=dict)

def process_single_article(news_item: Dict, config: Optional[dict] = None) -> ArticleResult:
    """
    Procesa un único artículo: descarga -> extrae -> limpia.
    """
    url = news_item.get('enlace', news_item.get('url', ''))
    
    result = ArticleResult(
        nombre_del_medio=news_item.get('nombre_del_medio', news_item.get('medio', '')),
        enlace=url,
        titular=news_item.get('titular', ''),
        fecha=news_item.get('fecha', ''),
        descripcion=news_item.get('descripcion', '')
    )
    
    if not url:
        result.scrape_status = "error_datos"
        result.error_message = "URL vacía"
        return result
        
    # Limpieza básica de la descripción si es necesario
    cleaner_config = config.get('cleaner', {}) if config else None

    # 1. Intentar Scraping Personalizado
    custom_data = scrape_custom(url, result.nombre_del_medio)
    if custom_data and custom_data.get('texto'):
        result.texto = custom_data['texto']
        # Usar el título extraído si es mejor que el del RSS
        if not result.titular and custom_data.get('titulo'):
            result.titular = custom_data['titulo']
            
        result.extraction_method = "custom_scraper"
        
        # Limpieza post-extracción personalizada
        if cleaner_config:
             remove_patterns = cleaner_config.get('remove_patterns')
             result.texto = clean_article_text(result.texto, remove_patterns=remove_patterns)
        
        result.idioma = detect_language(result.texto, None)
        result.char_count = len(result.texto)
        result.word_count = len(result.texto.split())
        result.scrape_status = "ok"
        return result

    # 2. Intentar Scraping Genérico
    # Configuración
    timeout = 15
    if config and 'downloader' in config:
        timeout = config['downloader'].get('timeout', 15)
        
    # Descarga
    download_res = download_article_html(url, timeout=timeout)
    result.download_time = download_res.download_time
    
    # Si la descarga falla, pero tenemos descripción RSS, usaremos eso como fallback al final
    download_failed = False
    if download_res.status_code and download_res.status_code >= 400:
        download_failed = True
        result.error_message = download_res.error_message or f"HTTP {download_res.status_code}"
    elif not download_res.html:
        download_failed = True
        result.error_message = download_res.error_message or "HTML vacío"

    if not download_failed:
        # Extracción Genérica
        start_extract = time.time()
        extractor_config = config.get('extractor', {}) if config else None
        extract_res = extract_article_text(download_res.html, url, extractor_config)
        result.extraction_time = time.time() - start_extract
        
        if extract_res.extraction_status == 'ok' and extract_res.text:
            result.extraction_method = extract_res.extraction_method
            
            remove_patterns = cleaner_config.get('remove_patterns') if cleaner_config else None
            clean_text = clean_article_text(extract_res.text, remove_patterns=remove_patterns)
            
            result.texto = clean_text
            result.idioma = detect_language(clean_text, extract_res.language)
            result.char_count = len(clean_text)
            result.word_count = len(clean_text.split())
            result.scrape_status = "ok"
            
            # Metadatos extra
            if extract_res.metadata:
                result.autor = extract_res.metadata.get('author')
                result.fecha_publicacion = extract_res.metadata.get('date')
                
            return result

    # 3. Fallback: Usar descripción del RSS si todo lo demás falló
    rss_description = news_item.get('descripcion', '').strip()
    if rss_description:
        logger.info(f"Usando descripción RSS como fallback para {url}")
        result.texto = rss_description
        result.extraction_method = "rss_summary_fallback"
        result.scrape_status = "ok" # Consideramos ok porque tenemos ALGO de contenido
        
        if cleaner_config:
             remove_patterns = cleaner_config.get('remove_patterns')
             result.texto = clean_article_text(result.texto, remove_patterns=remove_patterns)
        
        result.idioma = detect_language(result.texto, None)
        result.char_count = len(result.texto)
        result.word_count = len(result.texto.split())
        
        return result
    
    # Si llegamos aquí, falló todo
    if download_failed:
        result.scrape_status = "error_descarga"
        if download_res.is_blocked:
            result.scrape_status = "blocked_fallback_required"
    else:
        result.scrape_status = "no_contenido"
        result.error_message = "No se pudo extraer texto ni hay resumen RSS"
        
    return result


def save_results_to_db(results: List[ArticleResult], output_dir: str):
    """
    Actualiza el CSV maestro con los resultados de extracción.
    
    Args:
        results: Lista de ArticleResult procesados
        output_dir: Directorio de datos
    """
    csv_path = f"{output_dir}/noticias_china.csv"
    db = obtener_db(csv_path)
    
    for result in results:
        if not result.enlace:
            continue
            
        # Determinar estado basado en resultado
        if result.scrape_status == 'ok':
            nuevo_estado = 'extraido'
            error_msg = ''
        else:
            nuevo_estado = 'error'
            error_msg = f"{result.scrape_status}: {result.error_message}"
        
        # Actualizar en la DB
        db.actualizar_articulo(result.enlace, {
            'texto_completo': result.texto,
            'estado': nuevo_estado,
            'error_msg': error_msg
        })
    
    # Guardar cambios
    db.guardar()
    logger.info(f"Actualizados {len(results)} artículos en CSV maestro")


def process_articles(
    input_file: str = None, 
    config: Optional[dict] = None,
    max_articles: Optional[int] = None,
    output_dir: str = "data"
) -> ProcessingReport:
    """
    Procesa artículos pendientes desde el CSV maestro.
    
    Lee artículos con estado='nuevo' y los procesa para extraer texto.
    Actualiza el estado a 'extraido' o 'error' según resultado.
    
    Args:
        input_file: DEPRECATED - ahora se lee del CSV maestro
        config: Configuración opcional
        max_articles: Límite de artículos a procesar
        output_dir: Directorio de datos
        
    Returns:
        ProcessingReport con estadísticas
    """
    start_time = time.time()
    start_time_str = time.strftime("%Y-%m-%dT%H:%M:%S")
    
    # Cargar artículos pendientes del CSV maestro
    csv_path = f"{output_dir}/noticias_china.csv"
    db = obtener_db(csv_path)
    
    # Obtener artículos con estado='nuevo'
    articles_data = db.obtener_por_estado('nuevo')
    
    if not articles_data:
        logger.info("No hay artículos nuevos para procesar")
        return ProcessingReport(start_time=start_time_str)
        
    if max_articles:
        articles_data = articles_data[:max_articles]
        
    total = len(articles_data)
    logger.info(f"Iniciando procesamiento de {total} artículos nuevos")
    
    concurrency = 5
    if config and 'processing' in config:
        concurrency = config['processing'].get('concurrency', 5)
        
    results = []
    report = ProcessingReport(start_time=start_time_str, total_articles=total)
    
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        future_to_item = {
            executor.submit(process_single_article, item, config): item 
            for item in articles_data
        }
        
        for future in tqdm(as_completed(future_to_item), total=total, desc="Procesando artículos"):
            try:
                result = future.result()
                results.append(result)
                
                # Actualizar métricas
                if result.scrape_status == 'ok':
                    report.successful += 1
                    method = result.extraction_method
                    report.extraction_methods[method] = report.extraction_methods.get(method, 0) + 1
                elif result.scrape_status == 'error_descarga':
                    report.failed_download += 1
                elif result.scrape_status == 'no_contenido':
                    report.no_content += 1
                elif result.scrape_status == 'blocked_fallback_required':
                    report.blocked += 1
                else:
                    report.failed_extraction += 1
                    
            except Exception as e:
                logger.error(f"Excepción en procesamiento: {e}")
                report.failed_extraction += 1
                
    # Actualizar CSV maestro con resultados
    save_results_to_db(results, output_dir)
    
    # Finalizar reporte
    report.end_time = time.strftime("%Y-%m-%dT%H:%M:%S")
    report.duration_seconds = time.time() - start_time
    
    # Guardar reporte
    report_path = Path(output_dir) / "extraction_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(asdict(report), indent=2))
        
    return report


# Mantener compatibilidad - ahora redirige a la DB
def save_results(results: List[ArticleResult], output_dir: str, base_name: str = "articles_full"):
    """DEPRECATED: Usa save_results_to_db en su lugar."""
    logger.warning("save_results está deprecado. Usando save_results_to_db.")
    save_results_to_db(results, output_dir)
