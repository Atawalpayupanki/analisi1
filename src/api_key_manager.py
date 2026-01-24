"""
Gestor de API Keys con sistema de cooldown.

Este módulo implementa un singleton thread-safe para gestionar el estado
de las API keys de Groq, rastreando cuándo alcanzan límites de tasa (429)
y evitando reintentos hasta que expire el tiempo de cooldown.
"""

import os
import time
import threading
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


class APIKeyManager:
    """
    Singleton thread-safe para gestionar el estado de API keys.
    
    Rastrea cuándo cada API key alcanza el límite de peticiones (429)
    y almacena el timestamp de cuándo volverá a estar disponible.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._cooldowns: Dict[str, float] = {}  # {key_name: timestamp_disponible}
        self._lock_cooldowns = threading.Lock()
        
        # Lista de nombres de variables de entorno para API keys
        self.api_key_vars = [
            "GROQ_API_KEY",
            "GROQ_API_KEY_BACKUP",
            "GROQ_API_KEY_3",
            "GROQ_API_KEY_4",
            "GROQ_API_KEY_5",
            "GROQ_API_KEY_6",
            "GROQ_API_KEY_7",
            "GROQ_API_KEY_8"
        ]
    
    def is_available(self, key_name: str) -> bool:
        """
        Verifica si una API key está disponible (no en cooldown).
        
        Args:
            key_name: Nombre de la variable de entorno de la API key
            
        Returns:
            True si la key está disponible, False si está en cooldown
        """
        with self._lock_cooldowns:
            if key_name not in self._cooldowns:
                return True
            
            # Verificar si el cooldown ya expiró
            available_at = self._cooldowns[key_name]
            if time.time() >= available_at:
                # Cooldown expirado, eliminar entrada
                del self._cooldowns[key_name]
                return True
            
            return False
    
    def set_cooldown(self, key_name: str, wait_seconds: int):
        """
        Establece un cooldown para una API key.
        
        Args:
            key_name: Nombre de la variable de entorno de la API key
            wait_seconds: Segundos de espera antes de que vuelva a estar disponible
        """
        with self._lock_cooldowns:
            available_at = time.time() + wait_seconds
            self._cooldowns[key_name] = available_at
    
    def get_wait_time(self, key_name: str) -> int:
        """
        Obtiene el tiempo de espera restante para una API key.
        
        Args:
            key_name: Nombre de la variable de entorno de la API key
            
        Returns:
            Segundos restantes de espera, o 0 si está disponible
        """
        with self._lock_cooldowns:
            if key_name not in self._cooldowns:
                return 0
            
            available_at = self._cooldowns[key_name]
            remaining = int(available_at - time.time())
            
            if remaining <= 0:
                # Cooldown expirado
                del self._cooldowns[key_name]
                return 0
            
            return remaining
    
    def get_available_keys(self) -> List[str]:
        """
        Obtiene la lista de API keys que están actualmente disponibles.
        
        Returns:
            Lista de nombres de variables de entorno de keys disponibles
        """
        available = []
        for key_var in self.api_key_vars:
            if os.getenv(key_var) and self.is_available(key_var):
                available.append(key_var)
        return available
    
    def get_all_keys_status(self) -> List[Tuple[str, str, int, bool]]:
        """
        Obtiene el estado de todas las API keys configuradas.
        
        Returns:
            Lista de tuplas (key_name, status, wait_seconds, is_configured)
            - key_name: Nombre de la variable de entorno
            - status: "disponible", "cooldown", o "no_configurada"
            - wait_seconds: Segundos restantes de espera (0 si disponible)
            - is_configured: True si la key está configurada en .env
        """
        status_list = []
        
        for key_var in self.api_key_vars:
            is_configured = bool(os.getenv(key_var))
            
            if not is_configured:
                status_list.append((key_var, "no_configurada", 0, False))
                continue
            
            wait_time = self.get_wait_time(key_var)
            
            if wait_time > 0:
                status_list.append((key_var, "cooldown", wait_time, True))
            else:
                status_list.append((key_var, "disponible", 0, True))
        
        return status_list
    
    def get_next_available_key(self) -> Optional[Tuple[str, int]]:
        """
        Obtiene la próxima API key que estará disponible.
        
        Returns:
            Tupla (key_name, seconds_until_available) o None si hay keys disponibles ahora
        """
        available = self.get_available_keys()
        if available:
            return None  # Hay keys disponibles ahora
        
        # Encontrar la key con menor tiempo de espera
        min_wait = float('inf')
        next_key = None
        
        for key_var in self.api_key_vars:
            if not os.getenv(key_var):
                continue
            
            wait_time = self.get_wait_time(key_var)
            if 0 < wait_time < min_wait:
                min_wait = wait_time
                next_key = key_var
        
        if next_key:
            return (next_key, int(min_wait))
        
        return None
    
    def clear_all_cooldowns(self):
        """
        Limpia todos los cooldowns. Útil para testing o reset manual.
        """
        with self._lock_cooldowns:
            self._cooldowns.clear()


# Instancia global singleton
_manager = APIKeyManager()


def get_api_key_manager() -> APIKeyManager:
    """
    Obtiene la instancia singleton del APIKeyManager.
    
    Returns:
        Instancia de APIKeyManager
    """
    return _manager
