"""
Módulo filtro_china: Filtra noticias que mencionan a China.
"""
import json
import logging
import re
from typing import List

from parser import NewsItem

logger = logging.getLogger(__name__)


def load_keywords(config_path: str) -> List[str]:
    """
    Carga keywords desde archivo JSON.
    
    Args:
        config_path: Ruta al archivo keywords.json
        
    Returns:
        Lista de keywords en minúsculas
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        keywords = config.get('keywords', [])
        # Normalizar a minúsculas
        keywords = [kw.casefold() for kw in keywords]
        
        logger.info(f"Cargadas {len(keywords)} keywords de {config_path}")
        return keywords
        
    except FileNotFoundError:
        logger.error(f"Archivo de keywords no encontrado: {config_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error parseando JSON en {config_path}: {e}")
        return []


def matches_china(item: NewsItem, keywords: List[str]) -> bool:
    """
    Determina si una noticia menciona a China.
    
    Args:
        item: NewsItem a evaluar
        keywords: Lista de keywords a buscar
        
    Returns:
        True si el título o descripción contienen alguna keyword
    """
    # Combinar título y descripción
    text = f"{item.titular} {item.descripcion}".casefold()
    
    # Buscar cada keyword
    for keyword in keywords:
        # Usar word boundaries para evitar coincidencias parciales
        # Escapar keyword por si contiene caracteres especiales de regex
        pattern = r'\b' + re.escape(keyword) + r'\b'
        
        if re.search(pattern, text, re.IGNORECASE):
            logger.debug(f"Match encontrado: '{keyword}' en '{item.titular[:50]}...'")
            return True
    
    return False


def filter_china_news(items: List[NewsItem], keywords: List[str]) -> List[NewsItem]:
    """
    Filtra lista de noticias para retener solo las que mencionan a China.
    
    Args:
        items: Lista de NewsItem
        keywords: Lista de keywords
        
    Returns:
        Lista filtrada de NewsItem
    """
    filtered = [item for item in items if matches_china(item, keywords)]
    
    logger.info(f"Filtradas {len(filtered)} noticias de {len(items)} totales")
    return filtered
