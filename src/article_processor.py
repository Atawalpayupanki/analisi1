"""
Módulo orquestador para el procesamiento de artículos.
Coordina la descarga, extracción y limpieza.
"""

import logging
import json
import csv
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
except ImportError:
    from article_downloader import download_article_html
    from article_extractor import extract_article_text
    from article_cleaner import clean_article_text
    from article_enricher import detect_language

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
    url = news_item.get('enlace', '')
    
    result = ArticleResult(
        nombre_del_medio=news_item.get('nombre_del_medio', ''),
        enlace=url,
        titular=news_item.get('titular', ''),
        fecha=news_item.get('fecha', ''),
        descripcion=news_item.get('descripcion', '')
    )
    
    if not url:
        result.scrape_status = "error_datos"
        result.error_message = "URL vacía"
        return result
        
    # 1. Prioridad: Usar descripción del RSS si está disponible
    rss_description = news_item.get('descripcion', '').strip()
    
    # Limpieza básica de la descripción si es necesario
    cleaner_config = config.get('cleaner', {}) if config else None
    
    if rss_description:
        logger.info(f"Usando descripción RSS para {url}")
        result.texto = rss_description
        result.extraction_method = "rss_summary"
        result.scrape_status = "ok"
        
        if cleaner_config:
             remove_patterns = cleaner_config.get('remove_patterns')
             result.texto = clean_article_text(result.texto, remove_patterns=remove_patterns)
        
        result.idioma = detect_language(result.texto, None)
        result.char_count = len(result.texto)
        result.word_count = len(result.texto.split())
        
        # No descargamos ni extraemos si ya tenemos el resumen
        return result

    # 2. Si no hay resumen, intentar Scraping
    # Configuración
    timeout = 15
    if config and 'downloader' in config:
        timeout = config['downloader'].get('timeout', 15)
        
    # Descarga
    download_res = download_article_html(url, timeout=timeout)
    result.download_time = download_res.download_time
    
    if download_res.status_code and download_res.status_code >= 400:
        result.scrape_status = "error_descarga"
        result.error_message = download_res.error_message or f"HTTP {download_res.status_code}"
        if download_res.is_blocked:
            result.scrape_status = "blocked_fallback_required"
        return result
        
    if not download_res.html:
        result.scrape_status = "error_descarga"
        result.error_message = download_res.error_message or "HTML vacío"
        return result
        
    # Extracción
    start_extract = time.time()
    extractor_config = config.get('extractor', {}) if config else None
    extract_res = extract_article_text(download_res.html, url, extractor_config)
    result.extraction_time = time.time() - start_extract
    result.extraction_method = extract_res.extraction_method
    
    # Limpieza
    if extract_res.extraction_status != 'ok' or not extract_res.text:
        result.scrape_status = extract_res.extraction_status
        result.error_message = "No se pudo extraer texto ni hay resumen RSS"
        return result
    else:
        # Caso normal: extracción exitosa
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

def save_results(results: List[ArticleResult], output_dir: str, base_name: str = "articles_full"):
    """Guarda los resultados en JSONL y CSV."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Guardar JSONL
    jsonl_path = output_path / f"{base_name}.jsonl"
    with open(jsonl_path, 'w', encoding='utf-8') as f:
        for res in results:
            f.write(json.dumps(asdict(res), ensure_ascii=False) + '\n')
            
    # Guardar CSV
    csv_path = output_path / f"{base_name}.csv"
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        if results:
            # Obtener campos de la dataclass
            fieldnames = [field.name for field in list(results[0].__dataclass_fields__.values())]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for res in results:
                writer.writerow(asdict(res))
                
    # Guardar fallidos
    failed = [res for res in results if res.scrape_status != 'ok']
    if failed:
        failed_path = output_path / "failed_extractions.jsonl"
        with open(failed_path, 'w', encoding='utf-8') as f:
            for res in failed:
                fail_data = {
                    'url': res.enlace,
                    'medio': res.nombre_del_medio,
                    'status': res.scrape_status,
                    'error': res.error_message,
                    'timestamp': time.strftime("%Y-%m-%dT%H:%M:%S")
                }
                f.write(json.dumps(fail_data, ensure_ascii=False) + '\n')

def process_articles(
    input_file: str, 
    config: Optional[dict] = None,
    max_articles: Optional[int] = None
) -> ProcessingReport:
    """
    Procesa una lista de artículos desde un archivo JSONL.
    """
    start_time = time.time()
    start_time_str = time.strftime("%Y-%m-%dT%H:%M:%S")
    
    # Cargar artículos
    articles_data = []
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    articles_data.append(json.loads(line))
    except FileNotFoundError:
        logger.error(f"Archivo no encontrado: {input_file}")
        return ProcessingReport(start_time=start_time_str)
        
    if max_articles:
        articles_data = articles_data[:max_articles]
        
    total = len(articles_data)
    logger.info(f"Iniciando procesamiento de {total} artículos")
    
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
                
    # Guardar resultados
    output_dir = "data"
    if config and 'output' in config:
        output_dir = str(Path(config['output'].get('jsonl_path', 'data/articles_full.jsonl')).parent)
        
    save_results(results, output_dir)
    
    # Finalizar reporte
    report.end_time = time.strftime("%Y-%m-%dT%H:%M:%S")
    report.duration_seconds = time.time() - start_time
    
    # Guardar reporte
    report_path = Path(output_dir) / "extraction_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(asdict(report), indent=2))
        
    return report
