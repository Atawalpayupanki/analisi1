"""
Módulo de enriquecimiento de metadatos para artículos.
Maneja detección de idioma y extracción de metadatos adicionales.
"""

import logging
from typing import Optional, Dict, Any
from langdetect import detect, LangDetectException

logger = logging.getLogger(__name__)

def detect_language(text: str, hint_language: Optional[str] = None) -> Optional[str]:
    """
    Detecta el idioma del texto.
    
    Args:
        text: Texto a analizar
        hint_language: Idioma sugerido (ej. por trafilatura)
        
    Returns:
        Código de idioma (ej. 'es', 'en') o None
    """
    if not text or len(text) < 50:
        return hint_language
        
    # Si ya tenemos un hint confiable, lo usamos
    # (Trafilatura suele ser bueno, pero a veces falla)
    if hint_language and len(hint_language) == 2:
        return hint_language
        
    try:
        # Usar langdetect como fallback o confirmación
        detected = detect(text)
        return detected
    except LangDetectException:
        logger.warning("Falló detección de idioma con langdetect")
        return hint_language
    except Exception as e:
        logger.warning(f"Error en detección de idioma: {e}")
        return hint_language

def enrich_metadata(
    current_metadata: Dict[str, Any], 
    html: Optional[str], 
    url: str
) -> Dict[str, Any]:
    """
    Intenta extraer más metadatos del HTML si es posible.
    Por ahora, pasamos los metadatos existentes, pero aquí se podría
    añadir lógica para parsear Open Graph o JSON-LD si trafilatura falló.
    """
    # Placeholder para futura expansión
    return current_metadata
