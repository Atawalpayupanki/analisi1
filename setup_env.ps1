# Script para configurar el entorno virtual y instalar dependencias
# Ejecutar desde la raiz del proyecto: .\setup_env.ps1

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Configuracion del Entorno Virtual - China RSS" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar si Python esta instalado
Write-Host "[1/5] Verificando instalacion de Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK Python encontrado: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "ERROR Python no encontrado. Por favor, instala Python 3.8 o superior." -ForegroundColor Red
    exit 1
}

# 2. Eliminar entorno virtual anterior si existe
if (Test-Path ".venv") {
    Write-Host "[2/5] Eliminando entorno virtual anterior..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force .venv
    Write-Host "OK Entorno virtual anterior eliminado" -ForegroundColor Green
} else {
    Write-Host "[2/5] No hay entorno virtual anterior" -ForegroundColor Yellow
}

# 3. Crear nuevo entorno virtual
Write-Host "[3/5] Creando nuevo entorno virtual..." -ForegroundColor Yellow
python -m venv .venv
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK Entorno virtual creado exitosamente" -ForegroundColor Green
} else {
    Write-Host "ERROR al crear el entorno virtual" -ForegroundColor Red
    exit 1
}

# 4. Activar entorno virtual
Write-Host "[4/5] Activando entorno virtual..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1
Write-Host "OK Entorno virtual activado" -ForegroundColor Green

# 5. Actualizar pip e instalar dependencias
Write-Host "[5/5] Instalando dependencias..." -ForegroundColor Yellow
Write-Host "  - Actualizando pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip

Write-Host "  - Instalando setuptools y wheel..." -ForegroundColor Cyan
pip install --upgrade setuptools wheel

Write-Host "  - Instalando dependencias del proyecto..." -ForegroundColor Cyan
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "OK Todas las dependencias instaladas correctamente" -ForegroundColor Green
} else {
    Write-Host "ERROR al instalar dependencias" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  OK Configuracion completada exitosamente" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para activar el entorno virtual en el futuro, ejecuta:" -ForegroundColor Yellow
Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Para ejecutar la GUI:" -ForegroundColor Yellow
Write-Host "  python src\gui.py" -ForegroundColor White
Write-Host ""
