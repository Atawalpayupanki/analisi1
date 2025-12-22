"""
Script para crear un servidor HTTP local simple y abrir el visualizador.
Esto soluciona el problema de CORS al cargar el CSV.
"""
import http.server
import socketserver
import webbrowser
import os
from pathlib import Path
import threading
import time

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Agregar headers CORS
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

def start_server():
    """Inicia el servidor HTTP."""
    # Cambiar al directorio del proyecto
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Crear servidor
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"🌐 Servidor iniciado en http://localhost:{PORT}")
        print(f"📊 Abriendo visualizador...")
        print(f"⚠️  Presiona Ctrl+C para detener el servidor")
        
        # Abrir navegador después de un pequeño delay
        def open_browser():
            time.sleep(1)
            webbrowser.open(f"http://localhost:{PORT}/visualizador.html")
        
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.start()
        
        # Servir indefinidamente
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n✅ Servidor detenido")

if __name__ == "__main__":
    start_server()
