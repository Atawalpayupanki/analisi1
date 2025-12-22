"""
Módulo parser: Parsea feeds RSS y normaliza datos.
"""
import logging
import html
import re
from typing import List, Optional
from datetime import datetime, timedelta, timezone

import feedparser
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Antigüedad máxima en días para noticias (por defecto 30 días)
MAX_NEWS_AGE_DAYS = 30


class NewsItem(BaseModel):
    """Modelo de datos para una noticia."""
    nombre_del_medio: str
    rss_origen: str
    procedencia: str = "Occidental"  # Occidental | China
    idioma: str = "es"  # es, zh, etc.
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


def extract_date_from_url(url: str) -> Optional[str]:
    """
    Intenta extraer la fecha de la URL (común en medios chinos).
    
    Patrones soportados:
    - /YYYYMM/DD/ (ej: /202512/14/)
    - /YYYY-MM/DD/ (ej: /2022-12/14/)
    - /YYYY/MM/DD/ (ej: /2025/12/14/)
    
    Args:
        url: URL del artículo
        
    Returns:
        Fecha en formato ISO 8601 o None si no se encuentra
    """
    if not url:
        return None
    
    # Patrón 1: /YYYYMM/DD/ (ej: /202512/14/)
    match = re.search(r'/(\d{4})(\d{2})/(\d{2})/', url)
    if match:
        try:
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            dt = datetime(year, month, day, tzinfo=timezone.utc)
            return dt.isoformat()
        except ValueError:
            pass
    
    # Patrón 2: /YYYY-MM/DD/ o /YYYY/MM/DD/
    match = re.search(r'/(\d{4})[-/](\d{2})/(\d{2})/', url)
    if match:
        try:
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            dt = datetime(year, month, day, tzinfo=timezone.utc)
            return dt.isoformat()
        except ValueError:
            pass
    
    return None


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


def is_recent_news(fecha_iso: Optional[str], max_age_days: int = MAX_NEWS_AGE_DAYS) -> bool:
    """
    Verifica si una noticia es reciente (dentro del límite de días).
    
    Args:
        fecha_iso: Fecha en formato ISO 8601
        max_age_days: Máximo de días de antigüedad permitidos
        
    Returns:
        True si la noticia es reciente o no tiene fecha, False si es muy antigua
    """
    if not fecha_iso:
        # Si no hay fecha, la consideramos válida (no podemos filtrar)
        return True
    
    try:
        dt = date_parser.parse(fecha_iso)
        now = datetime.now(timezone.utc)
        
        # Si no tiene timezone, asumir UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        age = now - dt
        return age.days <= max_age_days
    except Exception:
        return True  # En caso de error, no filtrar


def parse_feed(xml_content: str, feed_url: str, medio_name: str, 
               procedencia: str = "Occidental", idioma: str = "es") -> List[NewsItem]:
    """
    Parsea un feed RSS y extrae noticias.
    
    Args:
        xml_content: Contenido XML del feed
        feed_url: URL del feed (para referencia)
        medio_name: Nombre del medio
        procedencia: Procedencia del medio (Occidental | China)
        idioma: Idioma del contenido (es, zh, etc.)
        
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
                
                # Fecha - primero intentar del RSS, luego de la URL
                fecha_raw = entry.get('published', '') or entry.get('updated', '')
                fecha = normalize_date(fecha_raw)
                
                # Fallback: extraer fecha de la URL (común en medios chinos)
                if not fecha and enlace:
                    fecha = extract_date_from_url(enlace)
                    if fecha:
                        fecha_raw = f"(extraída de URL)"
                
                # Filtrar noticias muy antiguas
                if not is_recent_news(fecha):
                    logger.debug(f"Noticia descartada por antigüedad: {fecha} - {titular[:50]}...")
                    continue
                
                # Validar campos mínimos
                if not titular:
                    logger.debug(f"Entrada sin título en {feed_url}, ignorada")
                    continue
                
                item = NewsItem(
                    nombre_del_medio=medio_name,
                    rss_origen=feed_url,
                    procedencia=procedencia,
                    idioma=idioma,
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

