@echo off
echo ========================================
echo   Actualizando Feeds de Xinhuanet
echo ========================================
echo.

cd /d "%~dp0"

echo [1/2] Generando feeds RSS...
python custom_scraper.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: No se pudieron generar los feeds
    echo Verifica que Python y las dependencias estén instaladas
    echo Ejecuta: pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo [2/2] Feeds generados exitosamente
echo.
echo Para servir los feeds, ejecuta:
echo   python -m http.server 8000
echo.
echo Luego agrega a tu lector RSS:
echo   http://localhost:8000/xinhua_china.xml
echo.

pause
