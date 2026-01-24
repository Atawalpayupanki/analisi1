"""
Scraper for La Vanguardia articles.
"""
import logging
import time
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

# Configuración de reintentos específica para scraping
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.RequestException, requests.Timeout)),
    reraise=True
)
def fetch_url(url: str, headers: Dict[str, str], timeout: int = 15) -> requests.Response:
    return requests.get(url, headers=headers, timeout=timeout)

def scrape_lavanguardia_article(url: str) -> Optional[Dict[str, str]]:
    """
    Extracts text from a La Vanguardia news article.
    
    Args:
        url: News URL
        
    Returns:
        dict with title and text, or None if failed
    """
    # La Vanguardia suele ser estricta con los bots, usamos un User-Agent realista
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
        'Referer': 'https://www.google.com/'
    }
    
    try:
        response = fetch_url(url, headers)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Eliminar scripts y estilos para limpiar
        for script in soup(["script", "style", "iframe", "noscript"]):
            script.decompose()
            
        # Extract title
        title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else "Sin título"
        
        # Extract article text
        # Selectores comunes en La Vanguardia
        selectors = [
            'div.article-modules',
            'div.article-body',
            'div.main-article-body',
            'div[itemprop="articleBody"]',
            'article'
        ]
        
        article_body = None
        for selector in selectors:
            article_body = soup.select_one(selector)
            if article_body:
                logger.debug(f"Encontrado cuerpo de artículo con selector: {selector}")
                break
        
        if article_body:
            # Obtener párrafos
            paragraphs = article_body.find_all('p')
            
            # Filtrar párrafos vacíos o irrelevantes (ej. "Lee también...")
            valid_paragraphs = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if not text:
                    continue
                # Filtros muy básicos de contenido basura
                if text.lower().startswith("lee también") or text.lower().startswith("newsletter"):
                    continue
                valid_paragraphs.append(text)
                
            text = '\n\n'.join(valid_paragraphs)
        else:
            logger.warning(f"No se encontró el cuerpo del artículo para {url}")
            text = ""
        
        if not text:
            return None
            
        return {
            'titulo': title,
            'texto': text
        }
        
    except Exception as e:
        logger.error(f"Error scraping La Vanguardia {url}: {e}")
        return None
