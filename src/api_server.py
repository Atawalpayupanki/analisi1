"""
Servidor API para operaciones de edición y eliminación de noticias.

Este módulo proporciona endpoints REST para:
- Actualizar categorías de noticias (tema, imagen_de_china)
- Eliminar noticias de la base de datos
- Obtener listas de categorías válidas

Autor: Sistema de Análisis de Noticias sobre China
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any
from urllib.parse import unquote
from flask import Flask, request, jsonify
from flask_cors import CORS

# Importar el gestor de base de datos
import sys
sys.path.append(str(Path(__file__).parent))
from noticias_db import obtener_db, recargar_db
from clasificador_langchain import CATEGORIAS_TEMA, CATEGORIAS_IMAGEN

logger = logging.getLogger(__name__)

# Crear aplicación Flask
app = Flask(__name__)
CORS(app)  # Habilitar CORS para peticiones desde el navegador

# Ruta al CSV por defecto
DEFAULT_CSV_PATH = Path(__file__).parent.parent / "data" / "noticias_china.csv"


@app.route('/api/categorias', methods=['GET'])
def get_categorias():
    """
    Obtiene las listas de categorías válidas.
    
    Returns:
        JSON con listas de temas e imágenes
    """
    try:
        return jsonify({
            'success': True,
            'data': {
                'temas': CATEGORIAS_TEMA,
                'imagenes': CATEGORIAS_IMAGEN
            }
        })
    except Exception as e:
        logger.error(f"Error obteniendo categorías: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/noticia/<path:url_encoded>', methods=['PUT'])
def actualizar_noticia(url_encoded: str):
    """
    Actualiza las categorías de una noticia.
    
    Args:
        url_encoded: URL de la noticia (URL encoded)
        
    Body JSON:
        {
            "tema": "Nuevo tema",
            "imagen_de_china": "Nueva imagen"
        }
        
    Returns:
        JSON con resultado de la operación
    """
    try:
        # Decodificar URL
        url = unquote(url_encoded)
        
        # Obtener datos del body
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No se proporcionaron datos'
            }), 400
        
        tema = data.get('tema')
        imagen = data.get('imagen_de_china')
        
        # Validar que al menos uno de los campos esté presente
        if not tema and not imagen:
            return jsonify({
                'success': False,
                'error': 'Debe proporcionar al menos tema o imagen_de_china'
            }), 400
        
        # Validar categorías
        if tema and tema not in CATEGORIAS_TEMA:
            return jsonify({
                'success': False,
                'error': f'Tema inválido. Debe ser uno de: {CATEGORIAS_TEMA}'
            }), 400
        
        if imagen and imagen not in CATEGORIAS_IMAGEN:
            return jsonify({
                'success': False,
                'error': f'Imagen inválida. Debe ser una de: {CATEGORIAS_IMAGEN}'
            }), 400
        
        # Obtener instancia de la base de datos
        db = obtener_db(str(DEFAULT_CSV_PATH))
        
        # Verificar que la noticia existe
        noticia = db.obtener_por_url(url)
        if not noticia:
            return jsonify({
                'success': False,
                'error': f'No se encontró la noticia con URL: {url}'
            }), 404
        
        # Preparar datos a actualizar
        datos_actualizacion = {}
        if tema:
            datos_actualizacion['tema'] = tema
        if imagen:
            datos_actualizacion['imagen_de_china'] = imagen
        
        # Actualizar en la base de datos
        success = db.actualizar_articulo(url, datos_actualizacion)
        
        if success:
            # Guardar cambios
            db.guardar()
            logger.info(f"Noticia actualizada: {url} - {datos_actualizacion}")
            
            return jsonify({
                'success': True,
                'message': 'Noticia actualizada correctamente',
                'data': datos_actualizacion
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No se pudo actualizar la noticia'
            }), 500
            
    except Exception as e:
        logger.error(f"Error actualizando noticia: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/noticia/<path:url_encoded>', methods=['DELETE'])
def eliminar_noticia(url_encoded: str):
    """
    Elimina una noticia de la base de datos.
    
    Args:
        url_encoded: URL de la noticia (URL encoded)
        
    Returns:
        JSON con resultado de la operación
    """
    try:
        # Decodificar URL
        url = unquote(url_encoded)
        
        # Obtener instancia de la base de datos
        db = obtener_db(str(DEFAULT_CSV_PATH))
        
        # Verificar que la noticia existe
        noticia = db.obtener_por_url(url)
        if not noticia:
            return jsonify({
                'success': False,
                'error': f'No se encontró la noticia con URL: {url}'
            }), 404
        
        # Eliminar de la base de datos
        success = db.eliminar_articulo(url)
        
        if success:
            # Guardar cambios
            db.guardar()
            logger.info(f"Noticia eliminada: {url}")
            
            return jsonify({
                'success': True,
                'message': 'Noticia eliminada correctamente'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No se pudo eliminar la noticia'
            }), 500
            
    except Exception as e:
        logger.error(f"Error eliminando noticia: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/noticias/batch-delete', methods=['POST'])
def eliminar_noticias_batch():
    """
    Elimina múltiples noticias de la base de datos.
    
    Body JSON:
        {
            "urls": ["url1", "url2", ...]
        }
        
    Returns:
        JSON con resultado de la operación
    """
    try:
        data = request.get_json()
        if not data or 'urls' not in data:
            return jsonify({
                'success': False,
                'error': 'No se proporcionaron URLs (campo "urls")'
            }), 400
        
        urls = data['urls']
        if not isinstance(urls, list):
            return jsonify({
                'success': False,
                'error': 'El campo "urls" debe ser una lista'
            }), 400
            
        # Obtener instancia de la base de datos
        db = obtener_db(str(DEFAULT_CSV_PATH))
        
        eliminated_count = 0
        errors = []
        
        for url in urls:
            if db.eliminar_articulo(url):
                eliminated_count += 1
            else:
                errors.append(url)
        
        if eliminated_count > 0:
            db.guardar()
            logger.info(f"Eliminadas {eliminated_count} noticias en lote")
            
        return jsonify({
            'success': True,
            'message': f'Se eliminaron {eliminated_count} noticias correctamente',
            'eliminated_count': eliminated_count,
            'errors': errors
        })

    except Exception as e:
        logger.error(f"Error en eliminación por lotes: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Endpoint de health check para verificar que el servidor está funcionando.
    
    Returns:
        JSON con estado del servidor
    """
    return jsonify({
        'success': True,
        'status': 'running',
        'message': 'API Server is running'
    })


def run_server(host: str = '127.0.0.1', port: int = 5000, debug: bool = False):
    """
    Inicia el servidor API.
    
    Args:
        host: Host donde escuchar
        port: Puerto donde escuchar
        debug: Modo debug de Flask
    """
    logger.info(f"Iniciando servidor API en {host}:{port}")
    app.run(host=host, port=port, debug=debug, use_reloader=False)


if __name__ == '__main__':
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Iniciar servidor
    run_server(debug=True)
