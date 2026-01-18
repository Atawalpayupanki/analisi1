"""
Script para generar el feed de Xinhua desde la GUI.
Este script actúa como un puente para ejecutar update_xinhua_feeds.py desde la carpeta src.
"""
import sys
import os
import subprocess
from pathlib import Path

def generate_feeds():
    """
    Ejecuta el script update_xinhua_feeds.py ubicado en el directorio raíz del proyecto.
    """
    # Obtener el directorio actual (src) y subir un nivel para encontrar el script
    current_dir = Path(__file__).parent.absolute()
    project_root = current_dir.parent
    script_path = project_root / "update_xinhua_feeds.py"
    
    if not script_path.exists():
        print(f"Error: No se encuentra el script en {script_path}")
        return False
        
    print(f"Ejecutando script de actualización de feeds: {script_path}")
    
    try:
        # Ejecutar el script usando el mismo intérprete de Python
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8' # Forzar UTF-8 para capturar correctamente caracteres chinos
        )
        
        # Imprimir la salida para que sea capturada por la GUI
        print(result.stdout)
        
        if result.stderr:
            print("Errores/Warnings:", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            
        print("Proceso finalizado correctamente.")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar el script: {e}")
        if e.stdout:
            print("Salida parcial:", e.stdout)
        if e.stderr:
            print("Error detallado:", e.stderr, file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error inesperado: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    success = generate_feeds()
    sys.exit(0 if success else 1)
