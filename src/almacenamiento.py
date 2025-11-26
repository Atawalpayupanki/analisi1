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


def load_existing_jsonl(output_path: str) -> List[dict]:
    """
    Carga noticias existentes desde un archivo JSONL.
    
    Args:
        output_path: Ruta del archivo JSONL
        
    Returns:
        Lista de diccionarios con las noticias existentes
    """
    existing_items = []
    
    if not Path(output_path).exists():
        return existing_items
    
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        item = json.loads(line)
                        existing_items.append(item)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Error parseando línea en {output_path}: {e}")
                        continue
        
        logger.info(f"Cargadas {len(existing_items)} noticias existentes de {output_path}")
        return existing_items
        
    except Exception as e:
        logger.error(f"Error leyendo archivo existente {output_path}: {e}")
        return existing_items


def save_jsonl(items: List[NewsItem], output_path: str) -> None:
    """
    Guarda noticias en formato JSON Lines, añadiendo a las existentes sin duplicar.
    
    Args:
        items: Lista de NewsItem nuevos
        output_path: Ruta del archivo de salida
    """
    try:
        # Crear directorio si no existe
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Cargar noticias existentes
        existing_items = load_existing_jsonl(output_path)
        
        # Crear set de URLs existentes para deduplicación rápida
        existing_urls = {item.get('enlace', '') for item in existing_items if item.get('enlace')}
        
        # Convertir nuevos items a dict
        new_items = []
        new_count = 0
        for item in items:
            item_dict = {
                'nombre_del_medio': item.nombre_del_medio,
                'rss_origen': item.rss_origen,
                'titular': item.titular,
                'enlace': item.enlace,
                'descripcion': item.descripcion,
                'fecha': item.fecha or item.fecha_raw
            }
            
            # Solo añadir si no existe (deduplicar por URL)
            if item.enlace and item.enlace not in existing_urls:
                new_items.append(item_dict)
                existing_urls.add(item.enlace)
                new_count += 1
            elif not item.enlace:
                # Si no tiene URL, añadirlo de todas formas (raro pero posible)
                new_items.append(item_dict)
                new_count += 1
        
        # Combinar: existentes + nuevos
        all_items = existing_items + new_items
        
        # Guardar todo
        with open(output_path, 'w', encoding='utf-8') as f:
            for item_dict in all_items:
                f.write(json.dumps(item_dict, ensure_ascii=False) + '\n')
        
        logger.info(f"Guardados {len(all_items)} ítems totales en {output_path} ({new_count} nuevos, {len(existing_items)} existentes)")
        
    except Exception as e:
        logger.error(f"Error guardando JSONL en {output_path}: {e}")
        raise


def load_existing_csv(output_path: str) -> List[dict]:
    """
    Carga noticias existentes desde un archivo CSV.
    
    Args:
        output_path: Ruta del archivo CSV
        
    Returns:
        Lista de diccionarios con las noticias existentes
    """
    existing_items = []
    
    if not Path(output_path).exists():
        return existing_items
    
    try:
        with open(output_path, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_items.append(row)
        
        logger.info(f"Cargadas {len(existing_items)} noticias existentes de {output_path}")
        return existing_items
        
    except Exception as e:
        logger.error(f"Error leyendo archivo CSV existente {output_path}: {e}")
        return existing_items


def save_csv(items: List[NewsItem], output_path: str) -> None:
    """
    Guarda noticias en formato CSV con UTF-8 BOM, añadiendo a las existentes sin duplicar.
    
    Args:
        items: Lista de NewsItem nuevos
        output_path: Ruta del archivo de salida
    """
    try:
        # Crear directorio si no existe
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Cargar noticias existentes
        existing_items = load_existing_csv(output_path)
        
        # Crear set de URLs existentes para deduplicación rápida
        existing_urls = {item.get('enlace', '') for item in existing_items if item.get('enlace')}
        
        # Convertir nuevos items a dict
        new_items = []
        new_count = 0
        for item in items:
            item_dict = {
                'nombre_del_medio': item.nombre_del_medio,
                'rss_origen': item.rss_origen,
                'titular': item.titular,
                'enlace': item.enlace,
                'descripcion': item.descripcion,
                'fecha': item.fecha or item.fecha_raw
            }
            
            # Solo añadir si no existe (deduplicar por URL)
            if item.enlace and item.enlace not in existing_urls:
                new_items.append(item_dict)
                existing_urls.add(item.enlace)
                new_count += 1
            elif not item.enlace:
                # Si no tiene URL, añadirlo de todas formas (raro pero posible)
                new_items.append(item_dict)
                new_count += 1
        
        # Combinar: existentes + nuevos
        all_items = existing_items + new_items
        
        # Guardar todo
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
            
            for item_dict in all_items:
                writer.writerow(item_dict)
        
        logger.info(f"Guardados {len(all_items)} ítems totales en {output_path} ({new_count} nuevos, {len(existing_items)} existentes)")
        
    except Exception as e:
        logger.error(f"Error guardando CSV en {output_path}: {e}")
        raise


def save_results(items: List[NewsItem], output_dir: str, base_name: str = 'output') -> None:
    """
    Guarda resultados en ambos formatos (JSONL y CSV), añadiendo a los archivos existentes.
    
    Args:
        items: Lista de NewsItem nuevos
        output_dir: Directorio de salida
        base_name: Nombre base para los archivos
    """
    jsonl_path = f"{output_dir}/{base_name}.jsonl"
    csv_path = f"{output_dir}/{base_name}.csv"
    
    save_jsonl(items, jsonl_path)
    save_csv(items, csv_path)
    
    logger.info(f"Resultados guardados en {output_dir}")
