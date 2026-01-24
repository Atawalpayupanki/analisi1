"""
Módulo para gestionar scrapers personalizados.
Integra los scrapers de diferentes medios.
"""
import logging
from typing import Optional, Dict

# Importar scrapers estáticos
try:
    from .scrapers import scrape_elmundo_article, scrape_elpais_article, scrape_lavanguardia_article
except ImportError:
    # Fallback para cuando se ejecuta desde fuera del paquete
    try:
        from scrapers import scrape_elmundo_article, scrape_elpais_article, scrape_lavanguardia_article
    except ImportError:
        pass

logger = logging.getLogger(__name__)

def scrape_custom(url: str, source_name: str) -> Optional[Dict[str, str]]:
    """
    Intenta extraer el artículo usando un scraper personalizado basado en el nombre del medio.
    
    Args:
        url: URL del artículo.
        source_name: Nombre del medio (ej. "El Mundo", "El País").
        
    Returns:
        dict con 'titulo' y 'texto' si tiene éxito, o None si no hay scraper o falla.
    """
    source_lower = source_name.lower().strip()
    
    try:
        if "el mundo" in source_lower:
            logger.info(f"Usando scraper personalizado para El Mundo: {url}")
            return scrape_elmundo_article(url)
            
        elif "el país" in source_lower or "el pais" in source_lower:
            logger.info(f"Usando scraper personalizado para El País: {url}")
            return scrape_elpais_article(url)
            
        elif "la vanguardia" in source_lower or "lavanguardia" in source_lower:
            logger.info(f"Usando scraper personalizado para La Vanguardia: {url}")
            return scrape_lavanguardia_article(url)
                
    except Exception as e:
        logger.error(f"Error en scraper personalizado para {source_name}: {e}")
        return None
        
    return None


