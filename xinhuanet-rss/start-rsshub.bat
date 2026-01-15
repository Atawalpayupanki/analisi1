@echo off
echo ========================================
echo   Iniciando RSSHub para Xinhuanet
echo ========================================
echo.

REM Verificar si Docker está instalado
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker no está instalado o no está en el PATH
    echo Por favor, instala Docker Desktop desde: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo [1/3] Verificando si el contenedor RSSHub ya existe...
docker ps -a | findstr rsshub-xinhuanet >nul 2>&1
if %errorlevel% equ 0 (
    echo Contenedor encontrado. Iniciando...
    docker start rsshub-xinhuanet
) else (
    echo Contenedor no encontrado. Creando nuevo contenedor...
    docker pull diygod/rsshub
    docker run -d --name rsshub-xinhuanet --restart unless-stopped -p 1200:1200 diygod/rsshub
)

echo.
echo [2/3] Esperando a que RSSHub inicie...
timeout /t 5 /nobreak >nul

echo.
echo [3/3] Verificando estado...
docker ps | findstr rsshub-xinhuanet >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   ✓ RSSHub iniciado correctamente
    echo ========================================
    echo.
    echo Accede a RSSHub en: http://localhost:1200
    echo.
    echo Feeds disponibles:
    echo   - Nacional:        http://localhost:1200/xinhua/china
    echo   - Internacional:   http://localhost:1200/xinhua/world
    echo   - Finanzas:        http://localhost:1200/xinhua/finance
    echo   - Tecnología:      http://localhost:1200/xinhua/tech
    echo   - Deportes:        http://localhost:1200/xinhua/sports
    echo   - Entretenimiento: http://localhost:1200/xinhua/ent
    echo.
    echo Para ver todos los feeds, consulta feeds.json
    echo.
) else (
    echo.
    echo ERROR: RSSHub no pudo iniciarse
    echo Revisa los logs con: docker logs rsshub-xinhuanet
    echo.
)

pause
