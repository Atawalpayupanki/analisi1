import sys
import os
from pathlib import Path

# Añadir src al path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from activity_logger import (
    get_logger, log_feed_processed, log_feed_failed, 
    log_article_added, log_error, log_process_started, log_process_completed
)

def test_logger():
    print("Iniciando prueba de logger...")
    
    # 1. Iniciar sesión
    logger = get_logger()
    logger.reset_session()
    print(f"Sesión iniciada: {logger.session_stats.session_start}")
    
    # 2. Simular proceso RSS
    log_process_started("Test RSS")
    
    # Simular feeds
    log_feed_processed("El País", "http://elpais.com/rss", 10)
    log_feed_processed("El Mundo", "http://elmundo.es/rss", 5)
    log_feed_failed("Feed Roto", "http://roto.com/rss", "404 Not Found")
    
    # Simular artículos
    log_article_added("Título de prueba 1", "El País", "http://url1.com")
    log_article_added("Título de prueba 2", "El Mundo", "http://url2.com")
    
    log_process_completed("Test RSS", {"feeds_processed": 3, "articles_added": 2})
    
    # 3. Verificar stats
    stats = logger.get_session_stats()
    print("\nEstadísticas de sesión simulada:")
    print(f"Feeds OK: {stats['feeds_ok']}")
    print(f"Feeds Error: {stats['feeds_error']}")
    print(f"Artículos: {stats['articles_added']}")
    
    assert stats['feeds_ok'] == 2
    assert stats['feeds_error'] == 1
    assert stats['articles_added'] == 2
    
    print("\n✅ Prueba completada con éxito. Los logs se han guardado.")

if __name__ == "__main__":
    test_logger()
