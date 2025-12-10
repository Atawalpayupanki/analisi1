"""
Módulo almacenamiento: Guarda noticias en el CSV maestro centralizado.

Este módulo ahora utiliza noticias_db para almacenamiento unificado.
"""
import logging
from typing import List
from pathlib import Path

from parser import NewsItem
from noticias_db import obtener_db, guardar_db, NoticiasDB

logger = logging.getLogger(__name__)


def save_results(items: List[NewsItem], output_dir: str, base_name: str = 'output') -> dict:
    """
    Guarda resultados de RSS en el CSV maestro centralizado.
    
    Los artículos nuevos se añaden con estado='nuevo'.
    Los artículos que ya existen se ignoran (deduplicación por URL).
    
    Args:
        items: Lista de NewsItem nuevos del RSS
        output_dir: Directorio de salida (se usa para determinar ruta del CSV maestro)
        base_name: Nombre base (ignorado, se usa siempre noticias_china.csv)
        
    Returns:
        Diccionario con estadísticas: {'nuevos': int, 'duplicados': int, 'total': int}
    """
    # Ruta del CSV maestro
    csv_path = f"{output_dir}/noticias_china.csv"
    
    # Obtener instancia de la DB
    db = obtener_db(csv_path)
    
    stats = {
        'nuevos': 0,
        'duplicados': 0,
        'total': len(items)
    }
    
    for item in items:
        # Convertir NewsItem a diccionario
        datos = {
            'url': item.enlace,
            'medio': item.nombre_del_medio,
            'titular': item.titular,
            'fecha': item.fecha or item.fecha_raw or '',
            'descripcion': item.descripcion,
            'estado': 'nuevo'
        }
        
        # Intentar añadir (retorna False si ya existe)
        if db.añadir_articulo(datos):
            stats['nuevos'] += 1
        else:
            stats['duplicados'] += 1
    
    # Guardar cambios
    if stats['nuevos'] > 0:
        db.guardar()
        logger.info(f"Guardados {stats['nuevos']} artículos nuevos en {csv_path}")
    
    if stats['duplicados'] > 0:
        logger.info(f"Ignorados {stats['duplicados']} artículos duplicados")
    
    logger.info(f"Total procesados: {stats['total']} | Nuevos: {stats['nuevos']} | Duplicados: {stats['duplicados']}")
    
    return stats


def obtener_articulos_por_estado(output_dir: str, estado: str) -> List[dict]:
    """
    Obtiene artículos filtrados por estado.
    
    Args:
        output_dir: Directorio de datos
        estado: Estado a filtrar ('nuevo', 'extraido', 'por_clasificar', 'clasificado', 'error')
        
    Returns:
        Lista de diccionarios con los artículos
    """
    csv_path = f"{output_dir}/noticias_china.csv"
    db = obtener_db(csv_path)
    return db.obtener_por_estado(estado)


def actualizar_estado_articulo(output_dir: str, url: str, estado: str, error_msg: str = '') -> bool:
    """
    Actualiza el estado de un artículo.
    
    Args:
        output_dir: Directorio de datos
        url: URL del artículo
        estado: Nuevo estado
        error_msg: Mensaje de error (si aplica)
        
    Returns:
        True si se actualizó correctamente
    """
    csv_path = f"{output_dir}/noticias_china.csv"
    db = obtener_db(csv_path)
    resultado = db.actualizar_estado(url, estado, error_msg)
    if resultado:
        db.guardar()
    return resultado


def obtener_estadisticas(output_dir: str) -> dict:
    """
    Obtiene estadísticas de la base de datos.
    
    Args:
        output_dir: Directorio de datos
        
    Returns:
        Diccionario con conteo por estado y total
    """
    csv_path = f"{output_dir}/noticias_china.csv"
    db = obtener_db(csv_path)
    
    stats = db.contar_por_estado()
    stats['total'] = db.total()
    
    return stats


# Mantener compatibilidad con código antiguo (deprecated)
def load_existing_jsonl(output_path: str) -> List[dict]:
    """DEPRECATED: Usar obtener_db().datos en su lugar."""
    logger.warning("load_existing_jsonl está deprecado. Usar noticias_db.")
    csv_path = str(Path(output_path).parent / "noticias_china.csv")
    db = obtener_db(csv_path)
    return db.datos


def load_existing_csv(output_path: str) -> List[dict]:
    """DEPRECATED: Usar obtener_db().datos en su lugar."""
    logger.warning("load_existing_csv está deprecado. Usar noticias_db.")
    csv_path = str(Path(output_path).parent / "noticias_china.csv")
    db = obtener_db(csv_path)
    return db.datos
