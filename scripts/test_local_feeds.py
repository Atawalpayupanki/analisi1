"""
Script de prueba para verificar la lectura de feeds RSS locales.
"""
import sys
import os

# Asegurar que el directorio src estÃ¡ en el path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from feeds_list import load_feeds_zh
from downloader import download_feeds_sync
from parser import parse_feed

def test_local_feeds():
    """Prueba la carga de feeds locales de Xinhuanet."""
    print("=" * 60)
    print("PRUEBA: Carga de feeds RSS locales de Xinhuanet")
    print("=" * 60)
    
    # Cargar configuracion de feeds chinos
    print("\n1. Cargando configuracion de feeds...")
    try:
        feeds = load_feeds_zh("config/rss_feeds_zh.json")
    except Exception as e:
        print(f"Error cargando configuracion: {e}")
        return False
    
    # Filtrar solo los feeds estaticos (file://)
    local_feeds = [f for f in feeds if f['url'].startswith('file://')]
    
    if not local_feeds:
        print(" [WARN] No se encontraron feeds locales (file://) en rss_feeds_zh.json")
        return False

    print(f"   [OK] Encontrados {len(local_feeds)} feeds locales")
    for feed in local_feeds:
        # Safe print for Windows console
        safe_name = feed['nombre'].encode('ascii', 'replace').decode('ascii')
        print(f"     - {safe_name}: {feed['url']}")
    
    # Descargar feeds
    print("\n2. Descargando/leyendo feeds locales...")
    try:
        results = download_feeds_sync(local_feeds)
    except Exception as e:
        print(f"Error en download_feeds_sync: {e}")
        return False
    
    # Verificar resultados
    print("\n3. Verificando resultados...")
    success_count = 0
    fail_count = 0
    
    for feed, content in results:
        if content:
            success_count += 1
            safe_name = feed['nombre'].encode('ascii', 'replace').decode('ascii')
            print(f"   [OK] {safe_name}: LEIDO ({len(content)} caracteres)")
            
            # Intentar parsear el feed
            try:
                # parse_feed(xml_content, feed_url, medio_name)
                news_items = parse_feed(content, feed['url'], feed['nombre'])
                print(f"     -> Parseadas {len(news_items)} noticias")
                
                # Mostrar las primeras 3 noticias
                for i, item in enumerate(news_items[:3], 1):
                    # Usar repr para evitar problemas de codificacin con caracteres chinos en consola
                    safe_title = item.titular.encode('ascii', 'replace').decode('ascii')
                    print(f"       {i}. {safe_title}")
            except Exception as e:
                print(f"     [ERROR] Error parseando: {e}")
        else:
            fail_count += 1
            print(f"   [FALLO] {feed['nombre']}: NO SE PUDO LEER")
    
    # Resumen
    print("\n" + "=" * 60)
    print(f"RESUMEN: {success_count} exitosos, {fail_count} fallidos")
    print("=" * 60)
    
    return success_count > 0

if __name__ == "__main__":
    success = test_local_feeds()
    sys.exit(0 if success else 1)
