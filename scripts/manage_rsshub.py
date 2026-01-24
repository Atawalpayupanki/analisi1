"""
RSSHub Management Script
Gestiona el servicio RSSHub Docker para feeds de Xinhuanet
"""

import subprocess
import sys
import time
import argparse
import requests
import io
from pathlib import Path

# Configurar salida UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class RSSHubManager:
    """Gestor para el servicio RSSHub Docker"""
    
    def __init__(self):
        self.rsshub_dir = Path(__file__).parent.parent / "xinhuanet-rss"
        self.base_url = "http://localhost:1200"
        self.container_name = "rsshub-xinhuanet"
    
    def check_docker(self) -> bool:
        """Verifica si Docker está instalado y corriendo"""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                print("[X] Docker no está instalado")
                return False
            
            # Verificar si Docker daemon está corriendo
            result = subprocess.run(
                ["docker", "ps"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                print("[X] Docker no está corriendo. Inicia Docker Desktop primero.")
                return False
            
            print("[OK] Docker está disponible")
            return True
            
        except FileNotFoundError:
            print("[X] Docker no está instalado")
            return False
        except subprocess.TimeoutExpired:
            print("[X] Docker no responde")
            return False
    
    def is_running(self) -> bool:
        """Verifica si el contenedor RSSHub está corriendo"""
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={self.container_name}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return self.container_name in result.stdout
        except Exception:
            return False
    
    def start(self) -> bool:
        """Inicia el servicio RSSHub"""
        if not self.check_docker():
            return False
        
        if self.is_running():
            print(f"[OK] RSSHub ya está corriendo")
            return True
        
        print(f"[*] Iniciando RSSHub...")
        
        try:
            # Cambiar al directorio xinhuanet-rss
            result = subprocess.run(
                ["docker-compose", "up", "-d"],
                cwd=self.rsshub_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                print(f"[X] Error al iniciar RSSHub:")
                print(result.stderr)
                return False
            
            # Esperar a que el servicio esté listo
            print("[...] Esperando a que RSSHub esté listo...")
            for i in range(30):
                if self.check_health():
                    print(f"[OK] RSSHub iniciado correctamente en {self.base_url}")
                    return True
                time.sleep(1)
            
            print("[!] RSSHub iniciado pero no responde. Puede necesitar más tiempo.")
            return True
            
        except subprocess.TimeoutExpired:
            print("[X] Timeout al iniciar RSSHub")
            return False
        except Exception as e:
            print(f"[X] Error: {e}")
            return False
    
    def stop(self) -> bool:
        """Detiene el servicio RSSHub"""
        if not self.is_running():
            print("[i] RSSHub no está corriendo")
            return True
        
        print("[STOP] Deteniendo RSSHub...")
        
        try:
            result = subprocess.run(
                ["docker-compose", "down"],
                cwd=self.rsshub_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                print(f"[X] Error al detener RSSHub:")
                print(result.stderr)
                return False
            
            print("[OK] RSSHub detenido")
            return True
            
        except Exception as e:
            print(f"[X] Error: {e}")
            return False
    
    def restart(self) -> bool:
        """Reinicia el servicio RSSHub"""
        print("[RESTART] Reiniciando RSSHub...")
        self.stop()
        time.sleep(2)
        return self.start()
    
    def check_health(self) -> bool:
        """Verifica si RSSHub está respondiendo"""
        try:
            response = requests.get(self.base_url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def status(self) -> None:
        """Muestra el estado del servicio RSSHub"""
        print("=" * 60)
        print("[STATUS] Estado de RSSHub")
        print("=" * 60)
        
        # Docker
        docker_ok = self.check_docker()
        
        # Contenedor
        running = self.is_running()
        status_icon = "[OK]" if running else "[X]"
        print(f"{status_icon} Contenedor: {'Corriendo' if running else 'Detenido'}")
        
        # Health check
        if running:
            healthy = self.check_health()
            health_icon = "[OK]" if healthy else "[!]"
            print(f"{health_icon} Servicio: {'Respondiendo' if healthy else 'No responde'}")
            print(f"[URL] {self.base_url}")
        
        # Feeds disponibles
        if running and self.check_health():
            print("\n[FEEDS] Feeds disponibles:")
            feeds = [
                ("Nacional", "/xinhua/china"),
                ("Internacional", "/xinhua/world"),
                ("Finanzas", "/xinhua/finance"),
                ("Tecnología", "/xinhua/tech"),
                ("Deportes", "/xinhua/sports"),
                ("Entretenimiento", "/xinhua/ent"),
                ("Militar", "/xinhua/mil"),
                ("Hong Kong/Macao", "/xinhua/gangao"),
                ("Taiwán", "/xinhua/tw"),
                ("Últimas", "/xinhua/latest"),
            ]
            
            for name, path in feeds:
                print(f"  • {name:20} -> {self.base_url}{path}")
        
        print("=" * 60)
    
    def test_feeds(self) -> None:
        """Prueba la disponibilidad de los feeds"""
        if not self.is_running() or not self.check_health():
            print("[X] RSSHub no está corriendo. Inicia el servicio primero.")
            return
        
        print("[TEST] Probando feeds de Xinhuanet...")
        print("=" * 60)
        
        feeds = [
            ("Nacional", "/xinhua/china"),
            ("Internacional", "/xinhua/world"),
            ("Finanzas", "/xinhua/finance"),
            ("Tecnología", "/xinhua/tech"),
            ("Deportes", "/xinhua/sports"),
            ("Entretenimiento", "/xinhua/ent"),
        ]
        
        for name, path in feeds:
            url = f"{self.base_url}{path}"
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    # Verificar que es XML válido
                    if 'xml' in response.headers.get('content-type', '').lower():
                        print(f"[OK] {name:20} -> OK ({len(response.content)} bytes)")
                    else:
                        print(f"[!] {name:20} -> Responde pero no es XML")
                else:
                    print(f"[X] {name:20} -> Error {response.status_code}")
            except requests.Timeout:
                print(f"[TIMEOUT] {name:20} -> Timeout")
            except Exception as e:
                print(f"[X] {name:20} -> {str(e)[:50]}")
        
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Gestor de RSSHub para feeds de Xinhuanet"
    )
    parser.add_argument(
        'action',
        choices=['start', 'stop', 'restart', 'status', 'test'],
        help='Acción a realizar'
    )
    
    args = parser.parse_args()
    manager = RSSHubManager()
    
    if args.action == 'start':
        success = manager.start()
        sys.exit(0 if success else 1)
    
    elif args.action == 'stop':
        success = manager.stop()
        sys.exit(0 if success else 1)
    
    elif args.action == 'restart':
        success = manager.restart()
        sys.exit(0 if success else 1)
    
    elif args.action == 'status':
        manager.status()
        sys.exit(0)
    
    elif args.action == 'test':
        manager.test_feeds()
        sys.exit(0)


if __name__ == '__main__':
    main()

