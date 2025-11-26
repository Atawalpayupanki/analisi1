"""
CLI para el módulo de extracción de artículos.
Permite ejecutar el proceso desde la línea de comandos.
"""

import argparse
import logging
import yaml
import sys
from pathlib import Path
from typing import Dict, Any

# Añadir directorio raíz al path para imports
sys.path.append(str(Path(__file__).parent.parent))

from src.article_processor import process_articles

def load_config(config_path: str) -> Dict[str, Any]:
    """Carga la configuración desde un archivo YAML."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error cargando configuración {config_path}: {e}")
        return {}

def setup_logging(log_level: str, log_file: str):
    """Configura el sistema de logging."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Crear directorio de logs si no existe
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def parse_args():
    """Parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description="Extractor de Artículos Completos - RSS China News Filter")
    
    parser.add_argument(
        '--input', 
        type=str, 
        default='data/output.jsonl',
        help='Archivo de entrada con noticias filtradas (JSONL)'
    )
    
    parser.add_argument(
        '--config', 
        type=str, 
        default='config/extractor_config.yaml',
        help='Archivo de configuración YAML'
    )
    
    parser.add_argument(
        '--output-dir', 
        type=str, 
        default='data',
        help='Directorio de salida'
    )
    
    parser.add_argument(
        '--concurrency', 
        type=int, 
        help='Número de hilos simultáneos (sobrescribe config)'
    )
    
    parser.add_argument(
        '--max-articles', 
        type=int, 
        help='Límite de artículos a procesar (para testing)'
    )
    
    parser.add_argument(
        '--log-level', 
        type=str, 
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Nivel de logging'
    )
    
    parser.add_argument(
        '--enable-playwright', 
        action='store_true',
        help='Activar fallback con Playwright (si está instalado)'
    )
    
    return parser.parse_args()

def main():
    """Función principal."""
    args = parse_args()
    
    # Cargar configuración
    config = load_config(args.config)
    
    # Sobrescribir con argumentos CLI
    if args.concurrency:
        if 'processing' not in config:
            config['processing'] = {}
        config['processing']['concurrency'] = args.concurrency
        
    if args.enable_playwright:
        if 'fallback' not in config:
            config['fallback'] = {}
        config['fallback']['playwright_enabled'] = True
        
    if args.output_dir:
        if 'output' not in config:
            config['output'] = {}
        # Actualizar rutas relativas al nuevo output_dir
        out_path = Path(args.output_dir)
        config['output']['jsonl_path'] = str(out_path / "articles_full.jsonl")
        config['output']['csv_path'] = str(out_path / "articles_full.csv")
        config['output']['failed_path'] = str(out_path / "failed_extractions.jsonl")
        config['output']['report_path'] = str(out_path / "extraction_report.json")
    
    # Configurar logging
    log_file = "logs/article_extractor.log"
    if 'logging' in config:
        log_file = config['logging'].get('log_file', log_file)
        
    setup_logging(args.log_level, log_file)
    logger = logging.getLogger(__name__)
    
    logger.info("Iniciando extractor de artículos...")
    logger.info(f"Input: {args.input}")
    logger.info(f"Config: {args.config}")
    
    try:
        report = process_articles(
            input_file=args.input,
            config=config,
            max_articles=args.max_articles
        )
        
        print("\n" + "="*50)
        print("RESUMEN DE EJECUCIÓN")
        print("="*50)
        print(f"Duración: {report.duration_seconds:.2f} segundos")
        print(f"Total procesado: {report.total_articles}")
        print(f"✅ Exitosos: {report.successful}")
        print(f"❌ Fallos descarga: {report.failed_download}")
        print(f"⚠️  Sin contenido: {report.no_content}")
        print(f"🔒 Bloqueados: {report.blocked}")
        print(f"💥 Errores extracción: {report.failed_extraction}")
        print("-" * 30)
        print("Métodos usados:")
        for method, count in report.extraction_methods.items():
            print(f"  - {method}: {count}")
        print("="*50)
        print(f"Reporte completo guardado en: {config.get('output', {}).get('report_path', 'data/extraction_report.json')}")
        
    except KeyboardInterrupt:
        logger.warning("Proceso interrumpido por el usuario")
        print("\nProceso interrumpido.")
    except Exception as e:
        logger.critical(f"Error fatal: {e}", exc_info=True)
        print(f"\nError fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
