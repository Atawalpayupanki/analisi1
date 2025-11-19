"""
Módulo feeds_list: Carga y normaliza URLs de feeds RSS.
"""
import json
import logging
from typing import List, Dict
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def validate_url(url: str) -> bool:
    """
    Valida que una URL tenga esquema http o https.
    
    Args:
        url: URL a validar
        
    Returns:
        True si la URL es válida, False en caso contrario
    """
    try:
        parsed = urlparse(url)
        return parsed.scheme in ('http', 'https') and bool(parsed.netloc)
    except Exception as e:
        logger.warning(f"Error validando URL '{url}': {e}")
        return False


def load_feeds(config_path: str) -> List[Dict[str, str]]:
    """
    Carga feeds desde archivo JSON y normaliza la lista.
    
    Args:
        config_path: Ruta al archivo feeds.json
        
    Returns:
        Lista de diccionarios con 'nombre' y 'url' para cada feed
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        logger.error(f"Archivo de configuración no encontrado: {config_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error parseando JSON en {config_path}: {e}")
        return []
    
    feeds = []
    seen_urls = set()
    
    for medio in config.get('feeds', []):
        nombre = medio.get('nombre', 'Desconocido')
        urls = medio.get('urls', [])
        
        for url in urls:
            # Normalizar y validar
            url = url.strip()
            
            if not validate_url(url):
                logger.warning(f"URL inválida ignorada: {url}")
                continue
            
            # Eliminar duplicados
            if url in seen_urls:
                logger.debug(f"URL duplicada ignorada: {url}")
                continue
            
            seen_urls.add(url)
            feeds.append({
                'nombre': nombre,
                'url': url
            })
    
    logger.info(f"Cargados {len(feeds)} feeds únicos de {len(config.get('feeds', []))} medios")
    return feeds
