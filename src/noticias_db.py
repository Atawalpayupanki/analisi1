"""
Módulo de base de datos centralizada para noticias.

Este módulo proporciona acceso unificado al CSV maestro de noticias,
permitiendo operaciones CRUD y gestión de estados de procesamiento.

Autor: Sistema de Análisis de Noticias sobre China
Fecha: 2025-12-10
"""

import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Ruta por defecto del CSV maestro
DEFAULT_DB_PATH = "data/noticias_china.csv"

# Estados posibles de un artículo
ESTADOS = {
    'nuevo': 'Recién añadido desde RSS',
    'extraido': 'Texto completo extraído',
    'por_clasificar': 'Listo para clasificar',
    'clasificado': 'Clasificación completada',
    'error': 'Error en algún paso'
}

# Columnas del CSV maestro
COLUMNAS = [
    'url',              # Clave única
    'medio',            # Nombre del periódico
    'procedencia',      # Procedencia del medio: Occidental | China
    'idioma',           # Idioma del texto: es, zh, etc.
    'titular',          # Título del artículo
    'fecha',            # Fecha de publicación
    'descripcion',      # Descripción corta del RSS
    'texto_completo',   # Texto extraído
    'tema',             # Tema clasificado por LLM
    'imagen_de_china',  # Imagen de China (LLM)
    'resumen',          # Resumen en 2 frases (LLM)
    'estado',           # Estado actual
    'fecha_procesado',  # Timestamp último proceso
    'error_msg'         # Mensaje de error si aplica
]


class NoticiasDB:
    """Gestor de la base de datos de noticias."""
    
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        """
        Inicializa el gestor de la base de datos.
        
        Args:
            db_path: Ruta al archivo CSV maestro
        """
        self.db_path = Path(db_path)
        self.datos: List[Dict[str, Any]] = []
        self.urls_index: set = set()  # Índice para búsqueda rápida
        self._dirty = False  # Flag para cambios sin guardar
        
    def cargar(self) -> int:
        """
        Carga los datos del CSV maestro.
        
        Returns:
            Número de registros cargados
        """
        self.datos = []
        self.urls_index = set()
        
        if not self.db_path.exists():
            logger.info(f"Archivo {self.db_path} no existe. Se creará al guardar.")
            return 0
        
        try:
            with open(self.db_path, 'r', encoding='utf-8-sig', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.datos.append(row)
                    if row.get('url'):
                        self.urls_index.add(row['url'])
            
            logger.info(f"Cargados {len(self.datos)} artículos de {self.db_path}")
            return len(self.datos)
            
        except Exception as e:
            logger.error(f"Error cargando {self.db_path}: {e}")
            return 0
    
    def guardar(self) -> bool:
        """
        Guarda los datos al CSV maestro.
        
        Returns:
            True si se guardó correctamente
        """
        try:
            # Crear directorio si no existe
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.db_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=COLUMNAS, quoting=csv.QUOTE_ALL)
                writer.writeheader()
                
                for row in self.datos:
                    # Asegurar que todas las columnas existen
                    row_completo = {col: row.get(col, '') for col in COLUMNAS}
                    writer.writerow(row_completo)
            
            self._dirty = False
            logger.info(f"Guardados {len(self.datos)} artículos en {self.db_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando {self.db_path}: {e}")
            return False
    
    def existe_url(self, url: str) -> bool:
        """
        Verifica si una URL ya existe en la base de datos.
        
        Args:
            url: URL a verificar
            
        Returns:
            True si existe
        """
        return url in self.urls_index
    
    def añadir_articulo(self, datos: Dict[str, Any]) -> bool:
        """
        Añade un nuevo artículo si no existe.
        
        Args:
            datos: Diccionario con los datos del artículo
                   Debe incluir al menos 'url'
                   
        Returns:
            True si se añadió, False si ya existía
        """
        url = datos.get('url', '')
        
        if not url:
            logger.warning("Intento de añadir artículo sin URL")
            return False
        
        if self.existe_url(url):
            logger.debug(f"Artículo ya existe: {url[:50]}...")
            return False
        
        # Crear registro con todas las columnas
        nuevo = {col: '' for col in COLUMNAS}
        nuevo.update({
            'url': url,
            'medio': datos.get('medio', datos.get('nombre_del_medio', '')),
            'procedencia': datos.get('procedencia', 'Occidental'),
            'idioma': datos.get('idioma', 'es'),
            'titular': datos.get('titular', datos.get('titulo', '')),
            'fecha': datos.get('fecha', ''),
            'descripcion': datos.get('descripcion', ''),
            'texto_completo': datos.get('texto_completo', datos.get('texto', '')),
            'tema': datos.get('tema', ''),
            'imagen_de_china': datos.get('imagen_de_china', ''),
            'resumen': datos.get('resumen', datos.get('resumen_dos_frases', '')),
            'estado': datos.get('estado', 'nuevo'),
            'fecha_procesado': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'error_msg': datos.get('error_msg', '')
        })
        
        self.datos.append(nuevo)
        self.urls_index.add(url)
        self._dirty = True
        
        logger.debug(f"Añadido artículo: {nuevo['titular'][:50]}...")
        return True
    
    def actualizar_articulo(self, url: str, datos: Dict[str, Any]) -> bool:
        """
        Actualiza un artículo existente.
        
        Args:
            url: URL del artículo a actualizar
            datos: Diccionario con los campos a actualizar
            
        Returns:
            True si se actualizó
        """
        if not self.existe_url(url):
            logger.warning(f"Artículo no existe para actualizar: {url[:50]}...")
            return False
        
        for row in self.datos:
            if row.get('url') == url:
                for key, value in datos.items():
                    if key in COLUMNAS:
                        row[key] = value
                row['fecha_procesado'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self._dirty = True
                logger.debug(f"Actualizado artículo: {url[:50]}...")
                return True
        
        return False
    
    def actualizar_estado(self, url: str, estado: str, error_msg: str = '') -> bool:
        """
        Cambia el estado de un artículo.
        
        Args:
            url: URL del artículo
            estado: Nuevo estado (nuevo, extraido, por_clasificar, clasificado, error)
            error_msg: Mensaje de error (solo si estado='error')
            
        Returns:
            True si se actualizó
        """
        if estado not in ESTADOS:
            logger.warning(f"Estado inválido: {estado}")
            return False
        
        datos = {'estado': estado}
        if estado == 'error' and error_msg:
            datos['error_msg'] = error_msg
        
        return self.actualizar_articulo(url, datos)
    
    def marcar_error(self, url: str, mensaje: str) -> bool:
        """
        Marca un artículo con error.
        
        Args:
            url: URL del artículo
            mensaje: Descripción del error
            
        Returns:
            True si se actualizó
        """
        return self.actualizar_estado(url, 'error', mensaje)

    def eliminar_articulo(self, url: str) -> bool:
        """
        Elimina un artículo de la base de datos.
        
        Args:
            url: URL del artículo a eliminar
            
        Returns:
            True si se eliminó, False si no existía
        """
        if not self.existe_url(url):
            return False
            
        initial_len = len(self.datos)
        self.datos = [row for row in self.datos if row.get('url') != url]
        
        if len(self.datos) < initial_len:
            self.urls_index.remove(url)
            self._dirty = True
            logger.info(f"Artículo eliminado: {url}")
            return True
        return False
    
    def obtener_por_estado(self, estado: str) -> List[Dict[str, Any]]:
        """
        Obtiene artículos filtrados por estado.
        
        Args:
            estado: Estado a filtrar
            
        Returns:
            Lista de artículos con ese estado
        """
        return [row for row in self.datos if row.get('estado') == estado]
    
    def obtener_por_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un artículo por su URL.
        
        Args:
            url: URL del artículo
            
        Returns:
            Diccionario con los datos o None
        """
        for row in self.datos:
            if row.get('url') == url:
                return row
        return None
    
    def contar_por_estado(self) -> Dict[str, int]:
        """
        Cuenta artículos por estado.
        
        Returns:
            Diccionario {estado: cantidad}
        """
        conteo = {estado: 0 for estado in ESTADOS}
        for row in self.datos:
            estado = row.get('estado', 'nuevo')
            if estado in conteo:
                conteo[estado] += 1
            else:
                conteo['nuevo'] += 1  # Estado desconocido -> nuevo
        return conteo
    
    def total(self) -> int:
        """Retorna el número total de artículos."""
        return len(self.datos)
    
    def tiene_cambios(self) -> bool:
        """Indica si hay cambios sin guardar."""
        return self._dirty


# Instancia global para uso simplificado
_db_instance: Optional[NoticiasDB] = None


def obtener_db(db_path: str = DEFAULT_DB_PATH) -> NoticiasDB:
    """
    Obtiene la instancia global de la base de datos.
    
    Args:
        db_path: Ruta al CSV maestro
        
    Returns:
        Instancia de NoticiasDB
    """
    global _db_instance
    
    if _db_instance is None or str(_db_instance.db_path) != db_path:
        _db_instance = NoticiasDB(db_path)
        _db_instance.cargar()
    
    return _db_instance


def recargar_db() -> NoticiasDB:
    """Recarga la base de datos desde disco."""
    global _db_instance
    if _db_instance:
        _db_instance.cargar()
    return _db_instance


# Funciones de conveniencia
def existe_url(url: str) -> bool:
    """Verifica si una URL existe en la DB."""
    return obtener_db().existe_url(url)


def añadir_articulo(datos: Dict[str, Any]) -> bool:
    """Añade un artículo a la DB."""
    return obtener_db().añadir_articulo(datos)


def guardar_db() -> bool:
    """Guarda la DB a disco."""
    return obtener_db().guardar()


if __name__ == "__main__":
    # Test básico
    print("=== Test de NoticiasDB ===")
    
    db = NoticiasDB("data/test_noticias.csv")
    db.cargar()
    
    # Añadir artículo de prueba
    resultado = db.añadir_articulo({
        'url': 'https://ejemplo.com/noticia1',
        'medio': 'El País',
        'titular': 'Noticia de prueba',
        'fecha': '2025-12-10',
        'descripcion': 'Descripción de prueba'
    })
    print(f"Añadido: {resultado}")
    
    # Intentar duplicado
    resultado = db.añadir_articulo({
        'url': 'https://ejemplo.com/noticia1',
        'medio': 'El País',
        'titular': 'Otra noticia',
    })
    print(f"Duplicado evitado: {not resultado}")
    
    # Contar
    print(f"Total: {db.total()}")
    print(f"Por estado: {db.contar_por_estado()}")
    
    # Limpiar test
    Path("data/test_noticias.csv").unlink(missing_ok=True)
    print("=== Test completado ===")
