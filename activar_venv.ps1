# Script de Activación Rápida del Entorno Virtual
# Uso: .\activar_venv.ps1

Write-Host "🚀 Activando entorno virtual..." -ForegroundColor Cyan

# Verificar si existe el entorno virtual
if (-Not (Test-Path ".\venv\Scripts\Activate.ps1")) {
    Write-Host "❌ Error: No se encontró el entorno virtual." -ForegroundColor Red
    Write-Host "   Ejecuta primero: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Activar el entorno virtual
& ".\venv\Scripts\Activate.ps1"

Write-Host "✅ Entorno virtual activado correctamente!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Comandos disponibles:" -ForegroundColor Cyan
Write-Host "  - GUI:              python src\gui.py" -ForegroundColor White
Write-Host "  - Procesador RSS:   python src\main.py" -ForegroundColor White
Write-Host "  - Extractor:        python src\main_extractor.py" -ForegroundColor White
Write-Host "  - Ayuda:            python src\main.py --help" -ForegroundColor White
Write-Host ""
Write-Host "Para desactivar: deactivate" -ForegroundColor Yellow
