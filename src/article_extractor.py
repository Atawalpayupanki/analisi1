"""
Módulo de extracción de texto para artículos de noticias.
Utiliza BeautifulSoup con selectores CSS específicos por dominio.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

@dataclass
class ExtractionResult:
    """Resultado de la extracción de texto."""
    text: Optional[str] = None
    language: Optional[str] = None
    extraction_method: str = 'none'  # 'trafilatura', 'bs4_fallback', 'playwright', 'none'
    extraction_status: str = 'error' # 'ok', 'no_content', 'error'
    metadata: Dict[str, Any] = field(default_factory=dict)


def extract_with_fallback_bs4(html: str, url: str) -> ExtractionResult:
    """
    Extrae texto usando BeautifulSoup con el mismo método que los ejemplos de scrap el mundo y scrap el pais.
    Primero busca el contenedor del artículo, luego extrae todos los párrafos dentro de él.
    """
    try:
        domain = urlparse(url).netloc
        # Eliminar 'www.' si existe para buscar en el diccionario
        domain_key = domain.replace('www.', '')
        
        # Selectores específicos por dominio - CONTENEDORES DEL ARTÍCULO
        # Siguiendo el patrón de los ejemplos: primero encontrar el contenedor, luego los párrafos
        domain_body_selectors = {
            'elpais.com': [
                'article',  # Método del ejemplo scrap_elpais.py
                'div.a_c_text',
                'div.articulo-cuerpo',
                'div[itemprop="articleBody"]'
            ],
            'elmundo.es': [
                'div.ue-l-article__body',  # Método del ejemplo scrape_elmundo.py
                'div.ue-c-article__body',
                'div.ue-c-article__premium-body'
            ],
            'abc.es': [
                'div.voc-article-content',
                'div.cuerpo-texto',
                'article[itemprop="articleBody"]'
            ],
            'lavanguardia.com': [
                'div.article-modules',
                'div.article-body',
                'div.main-article-body'
            ],
            'larazon.es': [
                'div.article-content',
                'div.texto-noticia',
                'div.article-body-content'
            ]
        }
        
        # Selectores genéricos de contenedores
        generic_body_selectors = [
            'article',
            'main',
            'div[role="main"]',
            'div.content',
            'div.article'
        ]
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Eliminar elementos no deseados ANTES de extraer
        unwanted_selectors = [
            'script', 'style', 'nav', 'header', 'footer', 'aside',
            'div.comments', 'div[id*="comment"]', 'section[id*="comment"]',
            'div.related', 'div.relacionados', 'div[class*="related"]',
            'div.subscription', 'div[class*="suscri"]', 'div[class*="paywall"]',
            'div.social', 'div[class*="share"]',
            'div.author-bio', 'div[class*="autor"]',
            'div.tags', 'div[class*="etiqueta"]', 'div[class*="archivado"]',
            'div.disqus', 'div[id*="disqus"]',
            'div.newsletter', 'div[class*="newsletter"]'
        ]
        
        for selector in unwanted_selectors:
            for element in soup.select(selector):
                element.decompose()
        
        # Obtener selectores específicos del dominio
        body_selectors = domain_body_selectors.get(domain_key, [])
        body_selectors.extend(generic_body_selectors)
        
        # MÉTODO DE LOS EJEMPLOS: Buscar el contenedor del artículo primero
        article_body = None
        for selector in body_selectors:
            article_body = soup.find(selector.split()[0], class_=selector.split('.')[-1] if '.' in selector else None) if '.' in selector else soup.find(selector)
            if article_body:
                logger.info(f"Contenedor encontrado con selector: {selector}")
                break
        
        # Si no encontramos con find(), intentar con select()
        if not article_body:
            for selector in body_selectors:
                elements = soup.select(selector)
                if elements:
                    article_body = elements[0]
                    logger.info(f"Contenedor encontrado con select: {selector}")
                    break
        
        if article_body:
            # MÉTODO DE LOS EJEMPLOS: Obtener todos los párrafos dentro del contenedor
            paragraphs = article_body.find_all('p')
            
            # Extraer texto de cada párrafo, filtrando los vacíos
            text_paragraphs = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text:  # Solo incluir párrafos con contenido
                    text_paragraphs.append(text)
            
            if text_paragraphs:
                # MÉTODO DE LOS EJEMPLOS: Unir con doble salto de línea
                extracted_text = '\n\n'.join(text_paragraphs)
                
                return ExtractionResult(
                    text=extracted_text,
                    language=None,  # BS4 no detecta idioma
                    extraction_method='bs4_fallback',
                    extraction_status='ok'
                )
        
        # Si no encontramos contenido, retornar no_content
        return ExtractionResult(
            text=None,
            extraction_method='bs4_fallback',
            extraction_status='no_content'
        )

    except Exception as e:
        logger.warning(f"Error en fallback BS4 para {url}: {e}")
        return ExtractionResult(
            text=None,
            extraction_method='bs4_fallback',
            extraction_status='error'
        )

def extract_article_text(html: str, url: str, config: Optional[dict] = None) -> ExtractionResult:
    """
    Función principal de extracción usando BeautifulSoup.
    
    Args:
        html: Contenido HTML
        url: URL del artículo
        config: Configuración opcional
        
    Returns:
        ExtractionResult
    """
    if not html:
        return ExtractionResult(
            text=None,
            extraction_method='none',
            extraction_status='no_content'
        )
    
    min_length = 200
    if config:
        min_length = config.get('min_text_length_ok', 200)
    
    # Usar BeautifulSoup directamente como método principal
    logger.info(f"Extrayendo contenido de {url} con BeautifulSoup...")
    bs4_result = extract_with_fallback_bs4(html, url)
    
    if bs4_result.extraction_status == 'ok' and bs4_result.text and len(bs4_result.text) >= min_length:
        return bs4_result
    
    # Si BS4 no extrajo suficiente contenido
    if bs4_result.text and len(bs4_result.text) > 0:
        bs4_result.extraction_status = 'no_content'  # Texto insuficiente
        return bs4_result
        
    return ExtractionResult(
        text=None,
        extraction_method='bs4_failed',
        extraction_status='no_content'
    )
