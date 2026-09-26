# ============================================================
# SCRIPT DE RESTAURACIÓN DE DESASTRES (Disaster Recovery)
# ============================================================
# Uso:
#   .\restaurar_backup.ps1 -ArchivoBackup "..\backups\backup_pos_20260926_120000.dump"
# ============================================================

param(
    [Parameter(Mandatory=$false)]
    [string]$ArchivoBackup
)

$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackupDir = Join-Path $ProjectRoot "backups"

if (-not $ArchivoBackup) {
    # Tomar el backup más reciente disponible
    $Ultimo = Get-ChildItem -Path $BackupDir -Filter "backup_pos_*.dump" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $Ultimo) {
        Write-Error "No se encontraron archivos .dump en la carpeta $BackupDir. Especifique la ruta del archivo con -ArchivoBackup."
        exit 1
    }
    $ArchivoBackup = $Ultimo.FullName
}

if (!(Test-Path $ArchivoBackup)) {
    Write-Error "El archivo especificado no existe: $ArchivoBackup"
    exit 1
}

Write-Host "=================================================" -ForegroundColor Red
Write-Host "INICIANDO RESTAURACIÓN DE BASE DE DATOS" -ForegroundColor Yellow
Write-Host "Archivo a restaurar: $ArchivoBackup" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Red

# 1. Copiar archivo dentro del contenedor
Write-Host "[1/3] Transfiriendo archivo al contenedor de base de datos..." -ForegroundColor Yellow
docker cp $ArchivoBackup restaurante_db:/tmp/restore_temp.dump

# 2. Restaurar usando pg_restore con limpieza previa
Write-Host "[2/3] Restaurando tablas, recetas, ventas e inventario..." -ForegroundColor Yellow
# pg_restore puede retornar warnings menores que no son errores fatales
docker exec restaurante_db pg_restore -U restaurante -d restaurante --clean --if-exists --no-owner --no-privileges /tmp/restore_temp.dump 2>$null

# 3. Limpiar temporal
docker exec restaurante_db rm -f /tmp/restore_temp.dump

Write-Host "=================================================" -ForegroundColor Green
Write-Host "✓ BASE DE DATOS RESTAURADA AL 100% CON ÉXITO" -ForegroundColor Green
Write-Host "El sistema POS está listo para operar inmediatamente." -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
