"""
Módulo almacenamiento: Guarda noticias en JSON Lines y CSV.
"""
import csv
import json
import logging
from pathlib import Path
from typing import List

from parser import NewsItem

logger = logging.getLogger(__name__)


def save_jsonl(items: List[NewsItem], output_path: str) -> None:
    """
    Guarda noticias en formato JSON Lines.
    
    Args:
        items: Lista de NewsItem
        output_path: Ruta del archivo de salida
    """
    try:
        # Crear directorio si no existe
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in items:
                # Convertir a dict y escribir como línea JSON
                item_dict = {
                    'nombre_del_medio': item.nombre_del_medio,
                    'rss_origen': item.rss_origen,
                    'titular': item.titular,
                    'enlace': item.enlace,
                    'descripcion': item.descripcion,
                    'fecha': item.fecha or item.fecha_raw
                }
                f.write(json.dumps(item_dict, ensure_ascii=False) + '\n')
        
        logger.info(f"Guardados {len(items)} ítems en {output_path}")
        
    except Exception as e:
        logger.error(f"Error guardando JSONL en {output_path}: {e}")
        raise


def save_csv(items: List[NewsItem], output_path: str) -> None:
    """
    Guarda noticias en formato CSV con UTF-8 BOM.
    
    Args:
        items: Lista de NewsItem
        output_path: Ruta del archivo de salida
    """
    try:
        # Crear directorio si no existe
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # UTF-8 con BOM para compatibilidad con Excel en Windows
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            fieldnames = [
                'nombre_del_medio',
                'rss_origen',
                'titular',
                'enlace',
                'descripcion',
                'fecha'
            ]
            
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            
            for item in items:
                writer.writerow({
                    'nombre_del_medio': item.nombre_del_medio,
                    'rss_origen': item.rss_origen,
                    'titular': item.titular,
                    'enlace': item.enlace,
                    'descripcion': item.descripcion,
                    'fecha': item.fecha or item.fecha_raw
                })
        
        logger.info(f"Guardados {len(items)} ítems en {output_path}")
        
    except Exception as e:
        logger.error(f"Error guardando CSV en {output_path}: {e}")
        raise


def save_results(items: List[NewsItem], output_dir: str, base_name: str = 'output') -> None:
    """
    Guarda resultados en ambos formatos (JSONL y CSV).
    
    Args:
        items: Lista de NewsItem
        output_dir: Directorio de salida
        base_name: Nombre base para los archivos
    """
    jsonl_path = f"{output_dir}/{base_name}.jsonl"
    csv_path = f"{output_dir}/{base_name}.csv"
    
    save_jsonl(items, jsonl_path)
    save_csv(items, csv_path)
    
    logger.info(f"Resultados guardados en {output_dir}")
