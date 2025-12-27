"""
Módulo de logging de actividad para el analizador de noticias.

Registra todos los eventos importantes del programa:
- Feeds procesados (éxito/error)
- Artículos añadidos/duplicados
- Extracciones de texto
- Clasificaciones LLM
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Literal
from dataclasses import dataclass, field, asdict
import threading

# Tipos de eventos
EventType = Literal[
    "feed_processed",        # Feed RSS procesado correctamente
    "feed_failed",           # Feed RSS falló
    "article_added",         # Artículo añadido al CSV
    "article_duplicate",     # Artículo duplicado ignorado
    "extraction_success",    # Extracción de texto exitosa
    "extraction_failed",     # Extracción de texto fallida
    "classification_success",# Clasificación LLM exitosa
    "classification_failed", # Clasificación LLM fallida
    "process_started",       # Proceso iniciado
    "process_completed",     # Proceso completado
    "error"                  # Error general
]

@dataclass
class ActivityEvent:
    """Representa un evento de actividad."""
    timestamp: str
    event_type: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SessionStats:
    """Estadísticas de la sesión actual."""
    session_start: str = ""
    feeds_total: int = 0
    feeds_ok: int = 0
    feeds_error: int = 0
    articles_added: int = 0
    articles_duplicate: int = 0
    extractions_success: int = 0
    extractions_failed: int = 0
    classifications_success: int = 0
    classifications_failed: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def reset(self):
        """Reinicia todas las estadísticas excepto session_start."""
        self.feeds_total = 0
        self.feeds_ok = 0
        self.feeds_error = 0
        self.articles_added = 0
        self.articles_duplicate = 0
        self.extractions_success = 0
        self.extractions_failed = 0
        self.classifications_success = 0
        self.classifications_failed = 0


class ActivityLogger:
    """
    Gestor centralizado de logs de actividad.
    
    Guarda eventos en:
    - logs/activity_log.jsonl - Log de todos los eventos
    - logs/session_stats.json - Estadísticas de sesión actual
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, logs_dir: Optional[str] = None):
        """Singleton pattern para garantizar una única instancia."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, logs_dir: Optional[str] = None):
        if self._initialized:
            return
            
        # Determinar directorio de logs
        if logs_dir:
            self.logs_dir = Path(logs_dir)
        else:
            # Buscar directorio logs relativo al proyecto
            src_dir = Path(__file__).parent
            project_dir = src_dir.parent
            self.logs_dir = project_dir / "logs"
        
        # Crear directorio si no existe
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Archivos de log
        self.activity_log_path = self.logs_dir / "activity_log.jsonl"
        self.session_stats_path = self.logs_dir / "session_stats.json"
        
        # Estadísticas de sesión
        self.session_stats = SessionStats(
            session_start=datetime.now().isoformat()
        )
        
        # Cache de eventos recientes (para mostrar en GUI)
        self.recent_events: List[ActivityEvent] = []
        self.max_recent_events = 500
        
        # Cargar eventos existentes
        self._load_recent_events()
        
        self._initialized = True
    
    def _load_recent_events(self):
        """Carga los últimos eventos del archivo de log."""
        try:
            if self.activity_log_path.exists():
                with open(self.activity_log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # Cargar solo los últimos N eventos
                    for line in lines[-self.max_recent_events:]:
                        try:
                            data = json.loads(line.strip())
                            self.recent_events.append(ActivityEvent(**data))
                        except:
                            pass
        except Exception:
            pass
    
    def log_event(self, event_type: EventType, message: str, 
                  details: Optional[Dict[str, Any]] = None):
        """
        Registra un evento de actividad.
        
        Args:
            event_type: Tipo de evento
            message: Mensaje descriptivo
            details: Detalles adicionales (opcional)
        """
        event = ActivityEvent(
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            message=message,
            details=details or {}
        )
        
        # Actualizar estadísticas según tipo
        self._update_stats(event_type, details)
        
        # Añadir a cache de eventos recientes
        self.recent_events.append(event)
        if len(self.recent_events) > self.max_recent_events:
            self.recent_events.pop(0)
        
        # Guardar en archivo
        self._save_event(event)
        self._save_session_stats()
    
    def _update_stats(self, event_type: EventType, details: Optional[Dict[str, Any]]):
        """Actualiza estadísticas según el tipo de evento."""
        if event_type == "feed_processed":
            self.session_stats.feeds_ok += 1
            self.session_stats.feeds_total += 1
        elif event_type == "feed_failed":
            self.session_stats.feeds_error += 1
            self.session_stats.feeds_total += 1
        elif event_type == "article_added":
            self.session_stats.articles_added += 1
        elif event_type == "article_duplicate":
            self.session_stats.articles_duplicate += 1
        elif event_type == "extraction_success":
            self.session_stats.extractions_success += 1
        elif event_type == "extraction_failed":
            self.session_stats.extractions_failed += 1
        elif event_type == "classification_success":
            self.session_stats.classifications_success += 1
        elif event_type == "classification_failed":
            self.session_stats.classifications_failed += 1
    
    def _save_event(self, event: ActivityEvent):
        """Guarda un evento en el archivo de log."""
        try:
            with open(self.activity_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event.to_dict(), ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"Error guardando evento: {e}")
    
    def _save_session_stats(self):
        """Guarda las estadísticas de sesión."""
        try:
            with open(self.session_stats_path, 'w', encoding='utf-8') as f:
                json.dump(self.session_stats.to_dict(), f, 
                         ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error guardando stats: {e}")
    
    def reset_session(self):
        """Reinicia las estadísticas de sesión."""
        self.session_stats.reset()
        self.session_stats.session_start = datetime.now().isoformat()
        self._save_session_stats()
        
        # Registrar inicio de nueva sesión
        self.log_event("process_started", "Nueva sesión iniciada")
    
    def get_recent_events(self, limit: int = 100, 
                          event_type: Optional[str] = None) -> List[Dict]:
        """
        Obtiene eventos recientes, opcionalmente filtrados.
        
        Args:
            limit: Número máximo de eventos
            event_type: Filtrar por tipo (opcional)
        
        Returns:
            Lista de eventos como diccionarios
        """
        events = self.recent_events
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        # Devolver los más recientes primero
        return [e.to_dict() for e in reversed(events[-limit:])]
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Obtiene las estadísticas de sesión actual."""
        return self.session_stats.to_dict()
    
    def get_historical_stats(self) -> Dict[str, Any]:
        """
        Calcula estadísticas históricas desde el archivo de log.
        
        Returns:
            Diccionario con totales históricos
        """
        stats = {
            "total_events": 0,
            "feeds_processed": 0,
            "feeds_failed": 0,
            "articles_added": 0,
            "classifications_success": 0,
            "classifications_failed": 0,
            "first_event": None,
            "last_event": None
        }
        
        try:
            if not self.activity_log_path.exists():
                return stats
                
            with open(self.activity_log_path, 'r', encoding='utf-8') as f:
                first_line = None
                last_line = None
                
                for line in f:
                    if not first_line:
                        first_line = line
                    last_line = line
                    
                    try:
                        data = json.loads(line.strip())
                        stats["total_events"] += 1
                        
                        event_type = data.get("event_type", "")
                        if event_type == "feed_processed":
                            stats["feeds_processed"] += 1
                        elif event_type == "feed_failed":
                            stats["feeds_failed"] += 1
                        elif event_type == "article_added":
                            stats["articles_added"] += 1
                        elif event_type == "classification_success":
                            stats["classifications_success"] += 1
                        elif event_type == "classification_failed":
                            stats["classifications_failed"] += 1
                    except:
                        pass
                
                if first_line:
                    try:
                        stats["first_event"] = json.loads(first_line).get("timestamp")
                    except:
                        pass
                if last_line:
                    try:
                        stats["last_event"] = json.loads(last_line).get("timestamp")
                    except:
                        pass
                        
        except Exception as e:
            print(f"Error leyendo stats históricas: {e}")
        
        return stats
    
    def clear_old_logs(self, days: int = 30):
        """
        Limpia eventos más antiguos que N días.
        
        Args:
            days: Número de días a mantener
        """
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=days)
        
        try:
            if not self.activity_log_path.exists():
                return
            
            # Leer todos los eventos
            kept_events = []
            with open(self.activity_log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        event_time = datetime.fromisoformat(data["timestamp"])
                        if event_time >= cutoff:
                            kept_events.append(line)
                    except:
                        pass
            
            # Reescribir solo los eventos recientes
            with open(self.activity_log_path, 'w', encoding='utf-8') as f:
                f.writelines(kept_events)
            
            # Actualizar cache
            self.recent_events = []
            self._load_recent_events()
            
        except Exception as e:
            print(f"Error limpiando logs: {e}")


# Instancia global para fácil acceso
_logger: Optional[ActivityLogger] = None

def get_logger(logs_dir: Optional[str] = None) -> ActivityLogger:
    """Obtiene la instancia del logger de actividad."""
    global _logger
    if _logger is None:
        _logger = ActivityLogger(logs_dir)
    return _logger


# Funciones de conveniencia para logging rápido
def log_feed_processed(nombre: str, url: str, items_count: int = 0):
    """Registra un feed procesado correctamente."""
    get_logger().log_event(
        "feed_processed",
        f"Feed procesado: {nombre}",
        {"url": url, "items": items_count, "nombre": nombre}
    )

def log_feed_failed(nombre: str, url: str, error: str):
    """Registra un feed que falló."""
    get_logger().log_event(
        "feed_failed",
        f"Feed fallido: {nombre}",
        {"url": url, "error": error, "nombre": nombre}
    )

def log_article_added(titulo: str, medio: str, url: str):
    """Registra un artículo añadido."""
    get_logger().log_event(
        "article_added",
        f"Artículo añadido: {titulo[:50]}...",
        {"titulo": titulo, "medio": medio, "url": url}
    )

def log_article_duplicate(titulo: str, medio: str):
    """Registra un artículo duplicado."""
    get_logger().log_event(
        "article_duplicate",
        f"Duplicado ignorado: {titulo[:50]}...",
        {"titulo": titulo, "medio": medio}
    )

def log_extraction_success(url: str, chars_extracted: int = 0):
    """Registra una extracción exitosa."""
    get_logger().log_event(
        "extraction_success",
        f"Extracción exitosa: {url[:50]}...",
        {"url": url, "chars": chars_extracted}
    )

def log_extraction_failed(url: str, error: str):
    """Registra una extracción fallida."""
    get_logger().log_event(
        "extraction_failed",
        f"Extracción fallida: {url[:50]}...",
        {"url": url, "error": error}
    )

def log_classification_success(titulo: str, tema: str, imagen: str):
    """Registra una clasificación exitosa."""
    get_logger().log_event(
        "classification_success",
        f"Clasificado: {titulo[:50]}...",
        {"titulo": titulo, "tema": tema, "imagen_de_china": imagen}
    )

def log_classification_failed(titulo: str, error: str):
    """Registra una clasificación fallida."""
    get_logger().log_event(
        "classification_failed",
        f"Clasificación fallida: {titulo[:50]}...",
        {"titulo": titulo, "error": error}
    )

def log_process_started(process_type: str):
    """Registra el inicio de un proceso."""
    get_logger().log_event(
        "process_started",
        f"Proceso iniciado: {process_type}",
        {"type": process_type}
    )

def log_process_completed(process_type: str, summary: Dict[str, Any]):
    """Registra la finalización de un proceso."""
    get_logger().log_event(
        "process_completed",
        f"Proceso completado: {process_type}",
        {"type": process_type, **summary}
    )

def log_error(message: str, error: str, details: Optional[Dict] = None):
    """Registra un error general."""
    get_logger().log_event(
        "error",
        message,
        {"error": error, **(details or {})}
    )
