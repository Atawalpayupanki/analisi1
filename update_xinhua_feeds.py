"""
Xinhua Feeds Updater
Actualiza los feeds RSS estáticos de Xinhuanet usando el scraper personalizado
"""

import sys
import subprocess
import io
import shutil
from pathlib import Path
from datetime import datetime

# Configurar salida UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def update_feeds():
    """Ejecuta el scraper personalizado para actualizar los feeds"""
    
    base_dir = Path(__file__).parent
    scraper_path = base_dir / "xinhuanet-rss" / "custom_scraper.py"
    feeds_dir = base_dir / "feeds"
    xinhua_feeds_dir = base_dir / "xinhuanet-rss" / "feeds"
    
    if not scraper_path.exists():
        print(f"[X] Error: No se encuentra el scraper en {scraper_path}")
        return False
    
    print("=" * 60)
    print("[UPDATE] Actualizando feeds RSS de Xinhuanet")
    print("=" * 60)
    print(f"[TIME] Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Ejecutar el scraper con encoding UTF-8 explícito
        env = dict()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        result = subprocess.run(
            [sys.executable, str(scraper_path)],
            capture_output=True,
            timeout=300,  # 5 minutos máximo
            env={**dict(__import__('os').environ), **env}
        )
        
        # Decodificar salida con UTF-8
        stdout = result.stdout.decode('utf-8', errors='replace') if result.stdout else ""
        stderr = result.stderr.decode('utf-8', errors='replace') if result.stderr else ""
        
        # Mostrar salida
        if stdout:
            print(stdout)
        
        if stderr:
            print("[!] Advertencias/Errores:")
            print(stderr)
        
        if result.returncode == 0:
            # Copiar feeds también a la carpeta principal de feeds
            success_copy = copy_feeds_to_main(xinhua_feeds_dir, feeds_dir)
            
            print()
            print("=" * 60)
            print("[OK] Feeds actualizados correctamente")
            print(f"[TIME] Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)
            print()
            print("[FILES] Feeds disponibles en:")
            print(f"  1. {xinhua_feeds_dir}")
            print(f"  2. {feeds_dir}")
            print()
            print("Feeds generados:")
            print("  - xinhua_china.xml      (Nacional)")
            print("  - xinhua_world.xml      (Internacional)")
            print("  - xinhua_finance.xml    (Finanzas)")
            print("  - xinhua_tech.xml       (Tecnologia)")
            print("  - xinhua_sports.xml     (Deportes)")
            print("  - xinhua_ent.xml        (Entretenimiento)")
            print()
            print("[INFO] Estos feeds se usan como fallback cuando RSSHub no esta disponible")
            return True
        else:
            print()
            print("=" * 60)
            print(f"[X] Error al actualizar feeds (codigo: {result.returncode})")
            print("=" * 60)
            return False
            
    except subprocess.TimeoutExpired:
        print()
        print("=" * 60)
        print("[X] Timeout: El scraper tardo mas de 5 minutos")
        print("=" * 60)
        return False
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"[X] Error inesperado: {e}")
        print("=" * 60)
        return False


def copy_feeds_to_main(source_dir: Path, dest_dir: Path) -> bool:
    """Copia los feeds de Xinhua a la carpeta principal de feeds"""
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        feed_files = list(source_dir.glob("xinhua_*.xml"))
        copied = 0
        
        for feed_file in feed_files:
            dest_file = dest_dir / feed_file.name
            shutil.copy2(feed_file, dest_file)
            copied += 1
        
        print(f"[COPY] Copiados {copied} feeds a {dest_dir}")
        return True
    except Exception as e:
        print(f"[!] Error al copiar feeds: {e}")
        return False


def main():
    """Función principal"""
    success = update_feeds()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
