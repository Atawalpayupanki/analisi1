"""
Módulo parser: Parsea feeds RSS y normaliza datos.
"""
import logging
import html
from typing import List, Optional
from datetime import datetime

import feedparser
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class NewsItem(BaseModel):
    """Modelo de datos para una noticia."""
    nombre_del_medio: str
    rss_origen: str
    titular: str
    enlace: str
    descripcion: str
    fecha_raw: str = ""
    fecha: Optional[str] = None
    
    class Config:
        # Permitir campos extra si es necesario
        extra = 'ignore'


def clean_html(html_text: str) -> str:
    """
    Limpia etiquetas HTML y decodifica entidades.
    
    Args:
        html_text: Texto con HTML
        
    Returns:
        Texto limpio sin HTML
    """
    if not html_text:
        return ""
    
    try:
        # Parsear y extraer texto
        soup = BeautifulSoup(html_text, 'lxml')
        text = soup.get_text(separator=' ', strip=True)
        
        # Decodificar entidades HTML
        text = html.unescape(text)
        
        # Normalizar espacios
        text = ' '.join(text.split())
        
        return text
    except Exception as e:
        logger.warning(f"Error limpiando HTML: {e}")
        # Fallback: al menos decodificar entidades
        return html.unescape(html_text)


def normalize_date(date_str: str) -> Optional[str]:
    """
    Normaliza una fecha a formato ISO 8601 UTC.
    
    Args:
        date_str: Cadena de fecha en cualquier formato
        
    Returns:
        Fecha en formato ISO 8601 o None si no se puede parsear
    """
    if not date_str:
        return None
    
    try:
        # Parsear fecha con dateutil (muy flexible)
        dt = date_parser.parse(date_str)
        
        # Convertir a UTC si tiene timezone, sino asumir UTC
        if dt.tzinfo is None:
            # Sin timezone, asumir UTC
            dt = dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
        
        # Convertir a UTC
        dt_utc = dt.astimezone(datetime.now().astimezone().tzinfo)
        
        # Formato ISO 8601
        return dt_utc.isoformat()
    except Exception as e:
        logger.debug(f"No se pudo parsear fecha '{date_str}': {e}")
        return None


def parse_feed(xml_content: str, feed_url: str, medio_name: str) -> List[NewsItem]:
    """
    Parsea un feed RSS y extrae noticias.
    
    Args:
        xml_content: Contenido XML del feed
        feed_url: URL del feed (para referencia)
        medio_name: Nombre del medio
        
    Returns:
        Lista de NewsItem parseados
    """
    if not xml_content:
        logger.warning(f"Contenido vacío para feed {feed_url}")
        return []
    
    try:
        # Parsear con feedparser
        feed = feedparser.parse(xml_content)
        
        if feed.bozo:
            logger.warning(f"Feed mal formado (bozo): {feed_url} - {feed.get('bozo_exception', '')}")
        
        items = []
        
        for entry in feed.entries:
            try:
                # Extraer campos
                titular = entry.get('title', '').strip()
                enlace = entry.get('link', '').strip()
                
                # Descripción puede estar en summary o description
                descripcion_raw = entry.get('summary', '') or entry.get('description', '')
                descripcion = clean_html(descripcion_raw)
                
                # Fecha
                fecha_raw = entry.get('published', '') or entry.get('updated', '')
                fecha = normalize_date(fecha_raw)
                
                # Validar campos mínimos
                if not titular:
                    logger.debug(f"Entrada sin título en {feed_url}, ignorada")
                    continue
                
                item = NewsItem(
                    nombre_del_medio=medio_name,
                    rss_origen=feed_url,
                    titular=titular,
                    enlace=enlace,
                    descripcion=descripcion,
                    fecha_raw=fecha_raw,
                    fecha=fecha
                )
                
                items.append(item)
                
            except Exception as e:
                logger.warning(f"Error parseando entrada en {feed_url}: {e}")
                continue
        
        logger.info(f"Parseados {len(items)} ítems de {feed_url}")
        return items
        
    except Exception as e:
        logger.error(f"Error parseando feed {feed_url}: {e}")
        return []
