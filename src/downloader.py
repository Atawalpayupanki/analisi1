"""
Módulo downloader: Descarga feeds RSS con reintentos y manejo de errores.
"""
import logging
import time
from typing import Optional, List, Tuple, Dict
from urllib.parse import urlparse, unquote
from pathlib import Path

import requests
import aiohttp
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

# Configuración
DEFAULT_TIMEOUT = 10
DEFAULT_USER_AGENT = 'Mozilla/5.0 (compatible; RSSChinaBot/1.0; +https://example.com/bot)'
MAX_RETRIES = 3
RATE_LIMIT_DELAY = 0.5  # segundos entre peticiones al mismo dominio


class DownloadError(Exception):
    """Error durante la descarga de un feed."""
    pass


def read_local_file(url: str) -> Optional[str]:
    """
    Lee un archivo RSS local desde una URL file://.
    
    Args:
        url: URL con esquema file://
        
    Returns:
        Contenido del archivo o None si falla
    """
    try:
        # Parsear la URL y obtener la ruta del archivo
        parsed = urlparse(url)
        # Decodificar la ruta (convierte %20 a espacios, etc.)
        file_path = unquote(parsed.path)
        
        # En Windows, file:///c:/path tiene un / inicial que debemos quitar
        if file_path.startswith('/') and len(file_path) > 2 and file_path[2] == ':':
            file_path = file_path[1:]
        
        logger.debug(f"Leyendo archivo local: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"Archivo local leído exitosamente: {file_path}")
        return content
        
    except FileNotFoundError:
        logger.error(f"Archivo no encontrado: {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error leyendo archivo local {url}: {e}")
        return None


@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.RequestException, requests.Timeout)),
    reraise=True
)
def download_feed(url: str, timeout: int = DEFAULT_TIMEOUT) -> Optional[str]:
    """
    Descarga un feed RSS de forma síncrona con reintentos.
    Soporta URLs HTTP/HTTPS y archivos locales con file://.
    
    Args:
        url: URL del feed RSS
        timeout: Timeout en segundos
        
    Returns:
        Contenido XML del feed o None si falla
    """
    # Si es un archivo local, leerlo directamente
    if url.startswith('file://'):
        return read_local_file(url)
    
    headers = {
        'User-Agent': DEFAULT_USER_AGENT,
        'Accept': 'application/rss+xml, application/xml, text/xml, */*'
    }
    
    try:
        logger.debug(f"Descargando feed: {url}")
        response = requests.get(url, headers=headers, timeout=timeout)
        
        if response.status_code == 200:
            logger.info(f"Feed descargado exitosamente: {url}")
            return response.text
        else:
            logger.warning(f"HTTP {response.status_code} para {url}")
            return None
            
    except requests.Timeout:
        logger.error(f"Timeout descargando {url}")
        raise
    except requests.RequestException as e:
        logger.error(f"Error descargando {url}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado descargando {url}: {e}")
        return None


async def download_feed_async(
    session: aiohttp.ClientSession,
    url: str,
    timeout: int = DEFAULT_TIMEOUT
) -> Tuple[str, Optional[str]]:
    """
    Descarga un feed RSS de forma asíncrona.
    Soporta URLs HTTP/HTTPS y archivos locales con file://.
    
    Args:
        session: Sesión aiohttp
        url: URL del feed RSS
        timeout: Timeout en segundos
        
    Returns:
        Tupla (url, contenido_xml) donde contenido puede ser None si falla
    """
    # Si es un archivo local, leerlo directamente (de forma síncrona)
    if url.startswith('file://'):
        content = read_local_file(url)
        return (url, content)
    
    headers = {
        'User-Agent': DEFAULT_USER_AGENT,
        'Accept': 'application/rss+xml, application/xml, text/xml, */*'
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            logger.debug(f"Descargando feed (intento {attempt + 1}): {url}")
            
            async with session.get(url, headers=headers, timeout=timeout) as response:
                if response.status == 200:
                    content = await response.text()
                    logger.info(f"Feed descargado exitosamente: {url}")
                    return (url, content)
                else:
                    logger.warning(f"HTTP {response.status} para {url}")
                    
        except asyncio.TimeoutError:
            logger.warning(f"Timeout en intento {attempt + 1} para {url}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(2 ** attempt)  # Backoff exponencial
        except aiohttp.ClientError as e:
            logger.warning(f"Error en intento {attempt + 1} para {url}: {e}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(2 ** attempt)
        except Exception as e:
            logger.error(f"Error inesperado descargando {url}: {e}")
            break
    
    logger.error(f"Falló descarga de {url} después de {MAX_RETRIES} intentos")
    return (url, None)


async def process_domain_feeds(
    session: aiohttp.ClientSession,
    domain_feeds: List[Dict[str, str]],
    timeout: int
) -> List[Tuple[Dict[str, str], Optional[str]]]:
    """
    Procesa los feeds de un dominio específico respetando el rate limit.
    """
    results = []
    for feed in domain_feeds:
        url = feed['url']
        # Usar download_feed_async que ya tenemos
        # Nota: download_feed_async devuelve (url, content)
        # Nosotros queremos devolver (feed_dict, content)
        _, content = await download_feed_async(session, url, timeout)
        results.append((feed, content))
        
        # Pausa entre peticiones al mismo dominio
        if len(domain_feeds) > 1:
            await asyncio.sleep(RATE_LIMIT_DELAY)
            
    return results


async def download_feeds_async(
    feeds: List[Dict[str, str]],
    timeout: int = DEFAULT_TIMEOUT
) -> List[Tuple[Dict[str, str], Optional[str]]]:
    """
    Descarga múltiples feeds de forma concurrente, paralelizando por dominio.
    Soporta URLs HTTP/HTTPS y archivos locales con file://.
    
    Args:
        feeds: Lista de diccionarios con 'nombre' y 'url'
        timeout: Timeout en segundos
        
    Returns:
        Lista de tuplas (feed_dict, contenido_xml)
    """
    # 1. Agrupar por dominio
    domain_feeds_map: Dict[str, List[Dict[str, str]]] = {}
    for feed in feeds:
        url = feed['url']
        if url.startswith('file://'):
            domain = 'local_files'
        else:
            try:
                domain = urlparse(url).netloc
            except Exception:
                domain = 'unknown'
                
        if domain not in domain_feeds_map:
            domain_feeds_map[domain] = []
        domain_feeds_map[domain].append(feed)
    
    # 2. Configurar sesión y límites
    timeout_config = aiohttp.ClientTimeout(total=timeout)
    # Limitar conexiones totales simultáneas
    connector = aiohttp.TCPConnector(limit=20)
    
    async with aiohttp.ClientSession(timeout=timeout_config, connector=connector) as session:
        tasks = []
        
        # 3. Crear tareas por dominio (cada dominio procesa sus feeds en serie)
        for domain, feeds_list in domain_feeds_map.items():
            if domain == 'local_files':
                # Archivos locales van aparte, aunque download_feed_async los maneja rápido
                task = process_domain_feeds(session, feeds_list, timeout)
            else:
                task = process_domain_feeds(session, feeds_list, timeout)
            tasks.append(task)
            
        # 4. Ejecutar todas las tareas de dominio en paralelo
        domain_results = await asyncio.gather(*tasks)
        
    # 5. Aplanar resultados
    all_results = []
    for dr in domain_results:
        all_results.extend(dr)
        
    return all_results


def download_feeds_sync(
    feeds: List[Dict[str, str]],
    timeout: int = DEFAULT_TIMEOUT
) -> List[Tuple[str, str, Optional[str]]]:
    """
    Descarga múltiples feeds de forma síncrona.
    
    Args:
        feeds: Lista de diccionarios con 'nombre' y 'url'
        timeout: Timeout en segundos
        
    Returns:
        Lista de tuplas (feed_dict, contenido_xml)
    """
    results = []
    domain_last_request: Dict[str, float] = {}
    
    for feed in feeds:
        url = feed['url']
        nombre = feed.get('nombre', 'Desconocido')
        domain = urlparse(url).netloc
        
        # Rate limiting
        if domain in domain_last_request:
            elapsed = time.time() - domain_last_request[domain]
            if elapsed < RATE_LIMIT_DELAY:
                time.sleep(RATE_LIMIT_DELAY - elapsed)
        
        try:
            content = download_feed(url, timeout)
            results.append((feed, content))
        except Exception as e:
            logger.error(f"Error final descargando {url}: {e}")
            results.append((feed, None))
        
        domain_last_request[domain] = time.time()
    
    return results
