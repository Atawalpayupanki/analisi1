"""
Módulo de extracción de texto para artículos de noticias.
Utiliza Trafilatura como método principal y BeautifulSoup como fallback.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import trafilatura
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

def extract_with_trafilatura(html: str, url: str, config: Optional[dict] = None) -> ExtractionResult:
    """
    Intenta extraer texto usando la librería Trafilatura.
    """
    try:
        # Configuración por defecto
        include_tables = True
        include_comments = False
        favor_precision = True
        
        if config:
            include_tables = config.get('include_tables', True)
            include_comments = config.get('include_comments', False)
            favor_precision = config.get('favor_precision', True)

        # Extraer texto
        text = trafilatura.extract(
            html,
            url=url,
            include_tables=include_tables,
            include_comments=include_comments,
            favor_precision=favor_precision,
            output_format='txt'
        )
        
        # Extraer metadatos
        metadata_raw = trafilatura.extract_metadata(html, url=url)
        metadata = {}
        language = None
        
        if metadata_raw:
            metadata = metadata_raw.as_dict()
            language = metadata.get('language')

        if text and len(text.strip()) > 0:
            return ExtractionResult(
                text=text,
                language=language,
                extraction_method='trafilatura',
                extraction_status='ok',
                metadata=metadata
            )
        else:
            return ExtractionResult(
                text=None,
                extraction_method='trafilatura',
                extraction_status='no_content'
            )
            
    except Exception as e:
        logger.warning(f"Error en extracción trafilatura para {url}: {e}")
        return ExtractionResult(
            text=None,
            extraction_method='trafilatura',
            extraction_status='error'
        )

def extract_with_fallback_bs4(html: str, url: str) -> ExtractionResult:
    """
    Intenta extraer texto usando BeautifulSoup y selectores específicos.
    Ahora extrae SOLO párrafos del cuerpo del artículo, excluyendo comentarios y contenido extra.
    """
    try:
        domain = urlparse(url).netloc
        # Eliminar 'www.' si existe para buscar en el diccionario
        domain_key = domain.replace('www.', '')
        
        # Selectores específicos por dominio - SOLO PÁRRAFOS DEL ARTÍCULO
        domain_paragraph_selectors = {
            'elpais.com': [
                'div.a_c_text p',  # Párrafos dentro del contenedor principal
                'div.articulo-cuerpo p',
                'div[itemprop="articleBody"] p'
            ],
            'elmundo.es': [
                'div.ue-c-article__body p',  # Párrafos del cuerpo del artículo
                'article.ue-l-article__body p',
                'div.ue-c-article__premium-body p'
            ],
            'abc.es': [
                'div.voc-article-content p',  # Párrafos del contenido del artículo
                'div.cuerpo-texto p',
                'article[itemprop="articleBody"] p'
            ],
            'lavanguardia.com': [
                'div.article-modules p',
                'div.article-body p',
                'div.main-article-body p'
            ],
            'larazon.es': [
                'div.article-content p',
                'div.texto-noticia p',
                'div.article-body-content p'
            ]
        }
        
        # Selectores genéricos de párrafos
        generic_paragraph_selectors = [
            'article p',
            'main p',
            'div[role="main"] p',
            'div.content p',
            'div.article p'
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
        paragraph_selectors = domain_paragraph_selectors.get(domain_key, [])
        paragraph_selectors.extend(generic_paragraph_selectors)
        
        paragraphs = []
        
        # Intentar con cada selector hasta encontrar párrafos
        for selector in paragraph_selectors:
            elements = soup.select(selector)
            if elements:
                # Extraer texto de cada párrafo
                for p in elements:
                    text = p.get_text(strip=True)
                    # Solo incluir párrafos con contenido sustancial
                    if len(text) > 30:  # Filtrar párrafos muy cortos
                        paragraphs.append(text)
                
                # Si encontramos suficientes párrafos, usar este selector
                if len(paragraphs) > 3:
                    break
        
        if paragraphs:
            # Unir párrafos con doble salto de línea
            extracted_text = '\n\n'.join(paragraphs)
            
            return ExtractionResult(
                text=extracted_text,
                language=None, # BS4 no detecta idioma
                extraction_method='bs4_fallback',
                extraction_status='ok'
            )
        else:
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
    Función principal de extracción. Orquesta los diferentes métodos.
    
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
        
    # 1. Intentar Trafilatura (Nivel 1)
    result = extract_with_trafilatura(html, url, config)
    
    min_length = 200
    if config:
        min_length = config.get('min_text_length_ok', 200)
    
    # Si es exitoso y tiene longitud suficiente, retornar
    if result.extraction_status == 'ok' and result.text and len(result.text) >= min_length:
        return result
        
    # 2. Intentar Fallback BS4 (Nivel 2)
    # Si trafilatura falló o devolvió texto muy corto
    logger.info(f"Trafilatura insuficiente para {url}, intentando fallback BS4...")
    bs4_result = extract_with_fallback_bs4(html, url)
    
    if bs4_result.extraction_status == 'ok' and bs4_result.text and len(bs4_result.text) >= min_length:
        # Preservar metadatos de trafilatura si existen
        bs4_result.metadata = result.metadata
        if not bs4_result.language:
            bs4_result.language = result.language
        return bs4_result
        
    # Si ambos fallan, retornar el mejor resultado (probablemente el de trafilatura aunque sea corto, o error)
    # Pero marcando el estado apropiado
    
    if result.text and len(result.text) > 0:
        result.extraction_status = 'no_content' # Texto insuficiente
        return result
        
    return ExtractionResult(
        text=None,
        extraction_method='all_failed',
        extraction_status='no_content'
    )
