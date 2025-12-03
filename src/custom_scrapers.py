"""
Módulo para gestionar scrapers personalizados.
Carga dinámicamente los scrapers de carpetas con nombres no estándar (espacios).
"""
import sys
import importlib.util
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def load_module_from_path(module_name, file_path):
    """Carga un módulo desde una ruta de archivo específica."""
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            return module
    except Exception as e:
        logger.error(f"Error cargando módulo {module_name} desde {file_path}: {e}")
    return None

# Rutas a los scrapers (ajustar según la estructura del proyecto)
BASE_DIR = Path(__file__).resolve().parent.parent
EL_MUNDO_PATH = BASE_DIR / "scrap el mundo" / "scrape_elmundo.py"
EL_PAIS_PATH = BASE_DIR / "scrap el pais" / "scrape_elpais.py"

# Cargar módulos
elmundo_scraper = load_module_from_path("scrape_elmundo", EL_MUNDO_PATH)
elpais_scraper = load_module_from_path("scrape_elpais", EL_PAIS_PATH)

def scrape_custom(url: str, source_name: str):
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
        if "el mundo" in source_lower and elmundo_scraper:
            logger.info(f"Usando scraper personalizado para El Mundo: {url}")
            return elmundo_scraper.scrape_elmundo_article(url)
            
        elif "el país" in source_lower or "el pais" in source_lower:
            if elpais_scraper:
                logger.info(f"Usando scraper personalizado para El País: {url}")
                return elpais_scraper.scrape_elpais_article(url)
                
    except Exception as e:
        logger.error(f"Error en scraper personalizado para {source_name}: {e}")
        return None
        
    return None
