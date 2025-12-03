"""
Script de prueba para verificar que el método de extracción actualizado funciona correctamente.
Este script prueba directamente el método con URLs de El País y El Mundo.
"""

import sys
sys.path.insert(0, 'src')

from article_downloader import download_article_html
from article_extractor import extract_article_text

def test_extraction(url, nombre_medio):
    """Prueba la extracción de un artículo."""
    print(f"\n{'='*80}")
    print(f"Probando: {nombre_medio}")
    print(f"URL: {url}")
    print(f"{'='*80}\n")
    
    # Descargar HTML
    print("1. Descargando HTML...")
    download_res = download_article_html(url, timeout=15)
    
    if not download_res.html:
        print(f"❌ Error en descarga: {download_res.error_message}")
        return False
    
    print(f"✅ HTML descargado ({len(download_res.html)} bytes)")
    
    # Extraer texto
    print("2. Extrayendo texto...")
    extract_res = extract_article_text(download_res.html, url)
    
    if extract_res.extraction_status != 'ok':
        print(f"❌ Error en extracción: {extract_res.extraction_status}")
        return False
    
    print(f"✅ Texto extraído exitosamente")
    print(f"   Método usado: {extract_res.extraction_method}")
    print(f"   Caracteres: {len(extract_res.text)}")
    print(f"   Palabras: {len(extract_res.text.split())}")
    
    # Mostrar preview
    print(f"\n3. Preview del texto extraído:")
    print(f"{'-'*80}")
    preview = extract_res.text[:500]
    print(preview)
    if len(extract_res.text) > 500:
        print("...")
    print(f"{'-'*80}\n")
    
    return True

if __name__ == '__main__':
    print("🧪 TEST DE EXTRACCIÓN DE ARTÍCULOS")
    print("Verificando que el método actualizado funciona correctamente\n")
    
    # URLs de prueba
    tests = [
        ("https://elpais.com/internacional/2025-12-03/malasia-retoma-la-busqueda-del-vuelo-mh370-uno-de-los-mayores-misterios-de-la-aviacion.html", "El País"),
        ("https://www.elmundo.es/papel/historias/2025/03/19/67d42506e9cf4a15708b459c.html", "El Mundo")
    ]
    
    results = []
    for url, nombre in tests:
        try:
            success = test_extraction(url, nombre)
            results.append((nombre, success))
        except Exception as e:
            print(f"❌ Excepción: {e}")
            results.append((nombre, False))
    
    # Resumen
    print(f"\n{'='*80}")
    print("RESUMEN DE PRUEBAS")
    print(f"{'='*80}")
    for nombre, success in results:
        status = "✅ ÉXITO" if success else "❌ FALLO"
        print(f"{nombre}: {status}")
    
    total = len(results)
    exitosos = sum(1 for _, s in results if s)
    print(f"\nTotal: {exitosos}/{total} pruebas exitosas")
