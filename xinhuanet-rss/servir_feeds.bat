@echo off
echo ========================================
echo   Servidor de Feeds RSS de Xinhuanet
echo ========================================
echo.

cd /d "%~dp0"

echo Iniciando servidor HTTP en puerto 8000...
echo.
echo Los feeds estarán disponibles en:
echo   http://localhost:8000/xinhua_china.xml
echo   http://localhost:8000/feeds/xinhua_world.xml
echo   (y otros feeds en la carpeta feeds/)
echo.
echo Presiona Ctrl+C para detener el servidor
echo.

python -m http.server 8000
