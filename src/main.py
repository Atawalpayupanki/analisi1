"""
RSS China News Filter - Orquestador principal

Descarga feeds RSS, parsea noticias y filtra las que mencionan a China.
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import List

from tqdm import tqdm

from feeds_list import load_feeds
from downloader import download_feeds_async, download_feeds_sync
from parser import parse_feed, NewsItem
from filtro_china import load_keywords, filter_china_news
from deduplicador import deduplicate
from almacenamiento import save_results


def setup_logging(log_level: str, log_dir: str) -> None:
    """
    Configura logging a consola y archivo.
    
    Args:
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
        log_dir: Directorio para archivos de log
    """
    # Crear directorio de logs
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Configurar formato
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Nivel de logging
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configurar root logger
    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            # Consola
            logging.StreamHandler(sys.stdout),
            # Archivo
            logging.FileHandler(
                f"{log_dir}/rss_china.log",
                encoding='utf-8',
                mode='a'
            )
        ]
    )


def parse_args():
    """Parsea argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description='Descarga feeds RSS y filtra noticias sobre China'
    )
    
    parser.add_argument(
        '--config',
        default='config/feeds.json',
        help='Ruta al archivo de configuración de feeds (default: config/feeds.json)'
    )
    
    parser.add_argument(
        '--keywords',
        default='config/keywords.json',
        help='Ruta al archivo de keywords (default: config/keywords.json)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='data',
        help='Directorio de salida (default: data/)'
    )
    
    parser.add_argument(
        '--async',
        dest='use_async',
        action='store_true',
        help='Usar descargas asíncronas (recomendado para >20 feeds)'
    )
    
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Nivel de logging (default: INFO)'
    )
    
    parser.add_argument(
        '--log-dir',
        default='logs',
        help='Directorio para archivos de log (default: logs/)'
    )
    
    return parser.parse_args()


async def main_async(args) -> None:
    """Función principal con descargas asíncronas."""
    logger = logging.getLogger(__name__)
    
    # Estadísticas
    stats = {
        'feeds_total': 0,
        'feeds_ok': 0,
        'feeds_error': 0,
        'items_total': 0,
        'items_china': 0,
        'items_unique': 0
    }
    
    logger.info("=== Iniciando RSS China News Filter (modo asíncrono) ===")
    
    # 1. Cargar feeds
    logger.info(f"Cargando feeds desde {args.config}")
    feeds = load_feeds(args.config)
    stats['feeds_total'] = len(feeds)
    
    if not feeds:
        logger.error("No se cargaron feeds. Abortando.")
        return
    
    # 2. Cargar keywords
    logger.info(f"Cargando keywords desde {args.keywords}")
    keywords = load_keywords(args.keywords)
    
    if not keywords:
        logger.error("No se cargaron keywords. Abortando.")
        return
    
    # 3. Descargar feeds
    logger.info(f"Descargando {len(feeds)} feeds...")
    download_results = await download_feeds_async(feeds)
    
    # 4. Parsear feeds
    logger.info("Parseando feeds...")
    all_items: List[NewsItem] = []
    
    for feed, content in tqdm(download_results, desc="Parseando"):
        if content:
            items = parse_feed(
                content, 
                feed['url'], 
                feed.get('nombre', 'Desconocido'),
                procedencia=feed.get('procedencia', 'Occidental'),
                idioma=feed.get('idioma', 'es')
            )
            all_items.extend(items)
            stats['feeds_ok'] += 1
        else:
            stats['feeds_error'] += 1
            logger.warning(f"Feed sin contenido: {feed['url']}")
    
    stats['items_total'] = len(all_items)
    logger.info(f"Total de ítems parseados: {stats['items_total']}")
    
    # 5. Filtrar por China
    logger.info("Filtrando noticias sobre China...")
    china_items = filter_china_news(all_items, keywords)
    stats['items_china'] = len(china_items)
    
    # 6. Deduplicar
    logger.info("Eliminando duplicados...")
    unique_items = deduplicate(china_items)
    stats['items_unique'] = len(unique_items)
    
    # 7. Guardar resultados
    if unique_items:
        logger.info(f"Guardando {len(unique_items)} noticias únicas...")
        save_results(unique_items, args.output_dir)
    else:
        logger.warning("No se encontraron noticias sobre China")
    
    # 8. Resumen
    print("\n" + "="*60)
    print("RESUMEN DE EJECUCIÓN")
    print("="*60)
    print(f"Feeds consultados:        {stats['feeds_total']}")
    print(f"  - Exitosos:             {stats['feeds_ok']}")
    print(f"  - Fallidos:             {stats['feeds_error']}")
    print(f"Ítems analizados:         {stats['items_total']}")
    print(f"Ítems sobre China:        {stats['items_china']}")
    print(f"Ítems únicos guardados:   {stats['items_unique']}")
    print("="*60)
    
    if unique_items:
        print(f"\nResultados guardados en:")
        print(f"  - {args.output_dir}/output.jsonl")
        print(f"  - {args.output_dir}/output.csv")
    
    logger.info("=== Proceso completado ===")


def main_sync(args) -> None:
    """Función principal con descargas síncronas."""
    logger = logging.getLogger(__name__)
    
    # Estadísticas
    stats = {
        'feeds_total': 0,
        'feeds_ok': 0,
        'feeds_error': 0,
        'items_total': 0,
        'items_china': 0,
        'items_unique': 0
    }
    
    logger.info("=== Iniciando RSS China News Filter (modo síncrono) ===")
    
    # 1. Cargar feeds
    logger.info(f"Cargando feeds desde {args.config}")
    feeds = load_feeds(args.config)
    stats['feeds_total'] = len(feeds)
    
    if not feeds:
        logger.error("No se cargaron feeds. Abortando.")
        return
    
    # 2. Cargar keywords
    logger.info(f"Cargando keywords desde {args.keywords}")
    keywords = load_keywords(args.keywords)
    
    if not keywords:
        logger.error("No se cargaron keywords. Abortando.")
        return
    
    # 3. Descargar feeds
    logger.info(f"Descargando {len(feeds)} feeds...")
    download_results = download_feeds_sync(feeds)
    
    # 4. Parsear feeds
    logger.info("Parseando feeds...")
    all_items: List[NewsItem] = []
    
    for feed, content in tqdm(download_results, desc="Parseando"):
        if content:
            items = parse_feed(
                content, 
                feed['url'], 
                feed.get('nombre', 'Desconocido'),
                procedencia=feed.get('procedencia', 'Occidental'),
                idioma=feed.get('idioma', 'es')
            )
            all_items.extend(items)
            stats['feeds_ok'] += 1
        else:
            stats['feeds_error'] += 1
            logger.warning(f"Feed sin contenido: {feed['url']}")
    
    stats['items_total'] = len(all_items)
    logger.info(f"Total de ítems parseados: {stats['items_total']}")
    
    # 5. Filtrar por China
    logger.info("Filtrando noticias sobre China...")
    china_items = filter_china_news(all_items, keywords)
    stats['items_china'] = len(china_items)
    
    # 6. Deduplicar
    logger.info("Eliminando duplicados...")
    unique_items = deduplicate(china_items)
    stats['items_unique'] = len(unique_items)
    
    # 7. Guardar resultados
    if unique_items:
        logger.info(f"Guardando {len(unique_items)} noticias únicas...")
        save_results(unique_items, args.output_dir)
    else:
        logger.warning("No se encontraron noticias sobre China")
    
    # 8. Resumen
    print("\n" + "="*60)
    print("RESUMEN DE EJECUCIÓN")
    print("="*60)
    print(f"Feeds consultados:        {stats['feeds_total']}")
    print(f"  - Exitosos:             {stats['feeds_ok']}")
    print(f"  - Fallidos:             {stats['feeds_error']}")
    print(f"Ítems analizados:         {stats['items_total']}")
    print(f"Ítems sobre China:        {stats['items_china']}")
    print(f"Ítems únicos guardados:   {stats['items_unique']}")
    print("="*60)
    
    if unique_items:
        print(f"\nResultados guardados en:")
        print(f"  - {args.output_dir}/output.jsonl")
        print(f"  - {args.output_dir}/output.csv")
    
    logger.info("=== Proceso completado ===")


if __name__ == '__main__':
    args = parse_args()
    
    # Configurar logging
    setup_logging(args.log_level, args.log_dir)
    
    # Ejecutar
    try:
        if args.use_async:
            asyncio.run(main_async(args))
        else:
            main_sync(args)
    except KeyboardInterrupt:
        print("\n\nProceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error fatal: {e}", exc_info=True)
        sys.exit(1)
