"""
Módulo deduplicador: Elimina noticias duplicadas.
"""
import hashlib
import logging
from typing import List, Set

from parser import NewsItem

logger = logging.getLogger(__name__)


def compute_hash(title: str, description: str) -> str:
    """
    Calcula hash SHA256 de título + descripción.
    
    Args:
        title: Título de la noticia
        description: Descripción de la noticia
        
    Returns:
        Hash hexadecimal (primeros 16 caracteres)
    """
    content = f"{title}|{description}".encode('utf-8')
    return hashlib.sha256(content).hexdigest()[:16]


def deduplicate(items: List[NewsItem]) -> List[NewsItem]:
    """
    Elimina duplicados por URL o por hash de contenido.
    
    Args:
        items: Lista de NewsItem
        
    Returns:
        Lista sin duplicados
    """
    seen_urls: Set[str] = set()
    seen_hashes: Set[str] = set()
    unique_items = []
    
    for item in items:
        # Prioridad 1: deduplicar por URL si existe
        if item.enlace:
            if item.enlace in seen_urls:
                logger.debug(f"Duplicado por URL: {item.enlace}")
                continue
            seen_urls.add(item.enlace)
            unique_items.append(item)
        else:
            # Prioridad 2: deduplicar por hash de contenido
            content_hash = compute_hash(item.titular, item.descripcion)
            if content_hash in seen_hashes:
                logger.debug(f"Duplicado por hash: {item.titular[:50]}...")
                continue
            seen_hashes.add(content_hash)
            unique_items.append(item)
    
    duplicates_removed = len(items) - len(unique_items)
    if duplicates_removed > 0:
        logger.info(f"Eliminados {duplicates_removed} duplicados de {len(items)} ítems")
    
    return unique_items
