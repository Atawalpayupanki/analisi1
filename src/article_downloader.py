"""
Módulo de descarga de artículos para el extractor de noticias.
Maneja descargas HTTP con reintentos, rate limiting y detección de bloqueos.
"""

import logging
import time
import requests
from urllib.parse import urlparse
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log

# Configuración de logging
logger = logging.getLogger(__name__)

# Excepciones que merecen reintento
RETRYABLE_EXCEPTIONS = (
    requests.exceptions.Timeout,
    requests.exceptions.ConnectionError,
    requests.exceptions.ChunkedEncodingError,
    requests.exceptions.ProxyError,
    requests.exceptions.SSLError
)

@dataclass
class DownloadResult:
    """Resultado de la descarga de un artículo."""
    url: str
    html: Optional[str]
    status_code: Optional[int]
    error_message: Optional[str] = None
    final_url: Optional[str] = None
    download_time: float = 0.0
    is_blocked: bool = False

class DomainRateLimiter:
    """Controla la frecuencia de peticiones por dominio."""
    
    def __init__(self, delay_seconds: float = 1.0):
        self.delay = delay_seconds
        self.last_request_time: Dict[str, float] = {}
        
    def wait_if_needed(self, url: str):
        """Espera si es necesario antes de hacer una petición al dominio de la URL."""
        domain = urlparse(url).netloc
        now = time.time()
        last_time = self.last_request_time.get(domain, 0)
        
        elapsed = now - last_time
        if elapsed < self.delay:
            wait_time = self.delay - elapsed
            logger.debug(f"Rate limiting para {domain}: esperando {wait_time:.2f}s")
            time.sleep(wait_time)
            
        self.last_request_time[domain] = time.time()

# Instancia global por defecto
rate_limiter = DomainRateLimiter()

def detect_blocking(html: str, status_code: int) -> bool:
    """
    Detecta si la respuesta indica un bloqueo (captcha, firewall, etc.).
    
    Args:
        html: Contenido HTML recibido
        status_code: Código de estado HTTP
        
    Returns:
        bool: True si se detecta bloqueo
    """
    # Solo detectar bloqueos basándose en códigos HTTP específicos
    # 403 Forbidden: acceso denegado por el servidor
    # 429 Too Many Requests: límite de peticiones excedido
    if status_code in [403, 429]:
        logger.warning(f"Bloqueo detectado por código HTTP: {status_code}")
        return True
        
    # No buscar patrones de texto para evitar falsos positivos
    # (artículos legítimos pueden mencionar "robot", "captcha", etc.)
    return False

@retry(
    retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def _make_request(url: str, timeout: int, headers: dict) -> requests.Response:
    """Función interna para realizar la petición con reintentos."""
    return requests.get(url, timeout=timeout, headers=headers)

def download_article_html(
    url: str, 
    timeout: int = 15, 
    headers: Optional[dict] = None,
    verify_ssl: bool = True
) -> DownloadResult:
    """
    Descarga el HTML de una URL de artículo.
    
    Args:
        url: URL a descargar
        timeout: Tiempo máximo de espera en segundos
        headers: Headers HTTP personalizados
        verify_ssl: Verificar certificados SSL
        
    Returns:
        DownloadResult con el resultado
    """
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; RSSChinaBot/1.0; +http://localhost)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8'
        }
        
    # Aplicar rate limiting
    rate_limiter.wait_if_needed(url)
    
    start_time = time.time()
    
    try:
        response = _make_request(url, timeout, headers)
        download_time = time.time() - start_time
        
        # Detectar encoding si no viene en headers
        if response.encoding is None:
            response.encoding = response.apparent_encoding
            
        html_content = response.text
        status_code = response.status_code
        final_url = response.url
        
        # Verificar éxito HTTP
        if status_code >= 400:
            error_msg = f"HTTP {status_code}"
            is_blocked = detect_blocking(html_content, status_code)
            if is_blocked:
                error_msg += " (Bloqueo detectado)"
                
            return DownloadResult(
                url=url,
                html=html_content if not is_blocked else None, # No guardar HTML de bloqueo
                status_code=status_code,
                error_message=error_msg,
                final_url=final_url,
                download_time=download_time,
                is_blocked=is_blocked
            )
            
        # Verificar bloqueos en contenido 200 OK
        is_blocked = detect_blocking(html_content, status_code)
        if is_blocked:
            return DownloadResult(
                url=url,
                html=None,
                status_code=status_code,
                error_message="Bloqueo detectado en contenido 200 OK",
                final_url=final_url,
                download_time=download_time,
                is_blocked=True
            )
            
        return DownloadResult(
            url=url,
            html=html_content,
            status_code=status_code,
            final_url=final_url,
            download_time=download_time
        )
        
    except Exception as e:
        download_time = time.time() - start_time
        logger.error(f"Error descargando {url}: {str(e)}")
        return DownloadResult(
            url=url,
            html=None,
            status_code=None,
            error_message=str(e),
            download_time=download_time
        )

def download_articles_batch(
    urls: List[str], 
    concurrency: int = 5,
    timeout: int = 15
) -> List[DownloadResult]:
    """
    Descarga múltiples artículos en paralelo.
    
    Args:
        urls: Lista de URLs
        concurrency: Número de hilos simultáneos
        timeout: Timeout por petición
        
    Returns:
        Lista de DownloadResult
    """
    results = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        # Mapear futuros a URLs
        future_to_url = {
            executor.submit(download_article_html, url, timeout): url 
            for url in urls
        }
        
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Excepción no manejada en thread para {url}: {e}")
                results.append(DownloadResult(
                    url=url,
                    html=None,
                    status_code=None,
                    error_message=f"Thread exception: {str(e)}"
                ))
                
    return results
