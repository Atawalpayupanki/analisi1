# -*- coding: utf-8 -*-
"""
Script para iniciar el servidor API Flask y abrir el visualizador automaticamente.

Este script:
1. Inicia el servidor API Flask en el puerto 5000
2. Espera a que el servidor este listo
3. Abre el visualizador HTML en el navegador

Uso:
    python iniciar_visualizador.py
"""
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
import threading
import requests


# Rutas del proyecto
SCRIPT_DIR = Path(__file__).parent
API_SERVER_PATH = SCRIPT_DIR / "src" / "api_server.py"
VISUALIZADOR_HTML = SCRIPT_DIR / "visualizador.html"


def check_api_health(max_attempts=10, wait_seconds=3):
    """
    Verifica si el servidor API está corriendo y respondiendo.
    
    Args:
        max_attempts: Número máximo de intentos
        wait_seconds: Segundos a esperar entre intentos
        
    Returns:
        bool: True si el servidor está listo, False en caso contrario
    """
    api_url = "http://127.0.0.1:5000/api/health"
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(api_url, timeout=2)
            if response.status_code == 200:
                print(f"[OK] Servidor API esta listo!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        if attempt < max_attempts - 1:
            print(f"[ESPERA] Esperando al servidor API... (intento {attempt + 1}/{max_attempts})")
            time.sleep(wait_seconds)
    
    print("[ERROR] No se pudo conectar al servidor API")
    return False


def start_api_server():
    """Inicia el servidor API Flask en un proceso separado."""
    print(f"[INICIO] Iniciando servidor API Flask...")
    print(f"[RUTA] Ejecutando: {API_SERVER_PATH}")
    
    # Iniciar el servidor como subproceso
    # Importante: Pasar os.environ para que encuentre los paquetes instalados
    import os
    env = os.environ.copy()
    
    process = subprocess.Popen(
        [sys.executable, str(API_SERVER_PATH)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        # No crear nueva consola para poder capturar logs si hay error
        # creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
    )
    
    return process


def start_simple_http_server():
    """Inicia un servidor HTTP simple para servir el HTML (para evitar CORS)."""
    import http.server
    import socketserver
    
    # Configurar el manejador de peticiones
    class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            # Agregar headers CORS
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            super().end_headers()

    # Cambiar al directorio del proyecto
    import os
    os.chdir(SCRIPT_DIR)

    # Buscar puerto libre empezando por 8000
    start_port = 8000
    max_retries = 10
    
    for port in range(start_port, start_port + max_retries):
        try:
            # Crear servidor
            with socketserver.TCPServer(("", port), MyHTTPRequestHandler) as httpd:
                print(f"[HTTP] Servidor HTTP iniciado en http://localhost:{port}")
                print(f"[VISUALIZADOR] Abriendo visualizador...")
                print(f"[AVISO] Presiona Ctrl+C para detener ambos servidores")
                
                # Abrir navegador después de un pequeño delay
                def open_browser():
                    time.sleep(1)
                    webbrowser.open(f"http://localhost:{port}/visualizador.html")
                
                browser_thread = threading.Thread(target=open_browser)
                browser_thread.start()
                
                # Servir indefinidamente
                try:
                    httpd.serve_forever()
                except KeyboardInterrupt:
                    print("\n[OK] Servidores detenidos")
                
                # Si llegamos aquí, salimos del loop
                return
                
        except OSError as e:
            if "Address already in use" in str(e) or "[WinError 10048]" in str(e):
                print(f"[INFO] Puerto {port} ocupado, probando siguiente...")
                continue
            else:
                raise e
    
    print(f"[ERROR] No se pudo encontrar un puerto libre entre {start_port} y {start_port + max_retries}")


def main():
    """Función principal."""
    print("=" * 60)
    print(" INICIALIZADOR DEL VISUALIZADOR DE NOTICIAS")
    print("=" * 60)
    print()
    
    # Verificar que los archivos existen
    if not API_SERVER_PATH.exists():
        print(f"[ERROR] No se encontro el servidor API en {API_SERVER_PATH}")
        return
    
    if not VISUALIZADOR_HTML.exists():
        print(f"[ERROR] No se encontro el visualizador en {VISUALIZADOR_HTML}")
        return
    
    # Paso 1: Iniciar servidor API
    api_process = start_api_server()
    print()
    
    # Paso 2: Esperar a que el servidor API esté listo
    if not check_api_health():
        print("[ERROR] El servidor API no pudo iniciarse correctamente")
        # Leer error si existe
        if api_process.poll() is not None:
            _, stderr = api_process.communicate()
            if stderr:
                print(f"[ERROR DETALLE] {stderr.decode('utf-8', errors='ignore')}")
        api_process.terminate()
        return
    
    print()
    print("=" * 60)
    print(" SISTEMA LISTO")
    print("=" * 60)
    print()
    print(" [API] Servidor API Flask: http://127.0.0.1:5000")
    print(" [HTTP] Servidor HTTP:     http://127.0.0.1:8000 (o superior)")
    print()
    print(" [INFO] El visualizador se abrira automaticamente en tu navegador")
    print()
    print("=" * 60)
    print()
    
    # Paso 3: Iniciar servidor HTTP y abrir navegador
    try:
        start_simple_http_server()
    except KeyboardInterrupt:
        print("\n[STOP] Deteniendo servidores...")
    finally:
        api_process.terminate()
        print("[OK] Sistema cerrado correctamente")


if __name__ == "__main__":
    main()
