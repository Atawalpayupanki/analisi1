"""
Módulo de limpieza y normalización de texto para artículos de noticias.
"""

import re
import unicodedata
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Patrones regex para eliminar ruido común en noticias
DEFAULT_REMOVE_PATTERNS = [
    r"Leer también:.*?(?=\n|$)",
    r"Ver galería.*?(?=\n|$)",
    r"Relacionado:.*?(?=\n|$)",
    r"Suscríbete.*?(?=\n|$)",
    r"Más información.*?(?=\n|$)",
    r"\[foto\]|\[vídeo\]|\[galería\]",
    r"Compartir en.*?(?=\n|$)",
    r"Síguenos en.*?(?=\n|$)",
    r"Te puede interesar:.*?(?=\n|$)",
    r"Newsletter.*?(?=\n|$)",
    r"Sigue leyendo.*?(?=\n|$)",
    r"Archivado en:.*?(?=\n|$)"
]

def normalize_text(text: str) -> str:
    """
    Normaliza caracteres Unicode y espacios.
    """
    if not text:
        return ""
        
    # Normalización Unicode (NFKC para compatibilidad)
    text = unicodedata.normalize('NFKC', text)
    
    # Reemplazar espacios no rompibles y otros espacios raros por espacio normal
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def clean_article_text(
    text: str, 
    remove_patterns: Optional[List[str]] = None,
    max_consecutive_newlines: int = 2
) -> str:
    """
    Limpia el texto extraído eliminando ruido y normalizando formato.
    
    Args:
        text: Texto crudo a limpiar
        remove_patterns: Lista de regex para eliminar
        max_consecutive_newlines: Máximo de saltos de línea permitidos
        
    Returns:
        Texto limpio
    """
    if not text:
        return ""
        
    # 1. Normalización básica inicial
    # Preservamos saltos de línea por ahora
    text = unicodedata.normalize('NFKC', text)
    
    # 2. Eliminar patrones de ruido
    patterns = DEFAULT_REMOVE_PATTERNS
    if remove_patterns:
        patterns = remove_patterns
        
    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.MULTILINE)
        
    # 3. Limpieza línea por línea
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        # Eliminar líneas muy cortas que parecen basura (ej. "|", "-", "•")
        if len(line) < 3 and not re.match(r'[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ]', line):
            continue
        if line:
            cleaned_lines.append(line)
            
    # 4. Reconstruir texto
    # Unir con saltos de línea
    text = '\n\n'.join(cleaned_lines)
    
    # 5. Controlar saltos de línea consecutivos
    if max_consecutive_newlines > 0:
        newline_pattern = r'\n{' + str(max_consecutive_newlines + 1) + r',}'
        text = re.sub(newline_pattern, '\n' * max_consecutive_newlines, text)
        
    return text.strip()
