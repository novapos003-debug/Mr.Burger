# ============================================================
# SCRIPT DE RESPALDO AUTOMÁTICO DE BASE DE DATOS
# Restaurante Mr. Burger (Servidor en Computador de Caja)
# ============================================================

$ErrorActionPreference = "Continue"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackupDir = Join-Path $ProjectRoot "backups"

if (!(Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupFileName = "backup_pos_$Timestamp.dump"
$LocalBackupPath = Join-Path $BackupDir $BackupFileName

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "INICIANDO RESPALDO DE BASE DE DATOS: $Timestamp" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

# 1. Comprobar que el contenedor de base de datos esté corriendo
$DbContainer = docker ps --filter "name=restaurante_db" --filter "status=running" --format "{{.Names}}"
if (-not $DbContainer) {
    Write-Host "ERROR: El contenedor 'restaurante_db' no está activo. Inicie Docker antes de hacer el backup." -ForegroundColor Red
    exit 1
}

# 2. Ejecutar pg_dump dentro del contenedor (sin verbose para no emitir a stderr)
Write-Host "[1/4] Volcando datos con compresión..." -ForegroundColor Yellow
docker exec restaurante_db pg_dump -U restaurante -d restaurante -F c -b -f /tmp/backup_temp.dump

# 3. Copiar archivo desde el contenedor al host
Write-Host "[2/4] Extrayendo archivo a carpeta local: $LocalBackupPath" -ForegroundColor Yellow
docker cp restaurante_db:/tmp/backup_temp.dump $LocalBackupPath
docker exec restaurante_db rm -f /tmp/backup_temp.dump

if (Test-Path $LocalBackupPath) {
    $SizeKb = [math]::Round(((Get-Item $LocalBackupPath).Length / 1024), 2)
    Write-Host "Respaldo creado exitosamente ($SizeKb KB)" -ForegroundColor Green
} else {
    Write-Host "ERROR: No se pudo generar el archivo de respaldo." -ForegroundColor Red
    exit 1
}

# 4. Detección automática de memoria USB para respaldo físico externo
Write-Host "[3/4] Buscando memoria USB para copia espejo externa..." -ForegroundColor Yellow
$UsbDrives = Get-CimInstance Win32_LogicalDisk | Where-Object { $_.DriveType -eq 2 }
$CopiaUsbRealizada = $false

foreach ($Drive in $UsbDrives) {
    $UsbTargetDir = Join-Path ($Drive.DeviceID + "\") "BACKUP_POS"
    try {
        if (!(Test-Path $UsbTargetDir)) {
            New-Item -ItemType Directory -Path $UsbTargetDir -Force | Out-Null
        }
        $UsbFilePath = Join-Path $UsbTargetDir $BackupFileName
        Copy-Item -Path $LocalBackupPath -Destination $UsbFilePath -Force
        Write-Host "Copia física guardada en memoria USB: $UsbFilePath" -ForegroundColor Green
        $CopiaUsbRealizada = $true
    } catch {
        Write-Host "Aviso: No se pudo escribir en la unidad $($Drive.DeviceID)" -ForegroundColor Yellow
    }
}

if (-not $CopiaUsbRealizada) {
    Write-Host "No se detectó memoria USB externa. El respaldo se conserva seguro en disco SSD local." -ForegroundColor Gray
}

# 5. Rotación de copias: eliminar respaldos con más de 30 días de antigüedad
Write-Host "[4/4] Limpiando respaldos antiguos (retención 30 días)..." -ForegroundColor Yellow
$DiasRetencion = 30
$FechaLimite = (Get-Date).AddDays(-$DiasRetencion)
$ArchivosAntiguos = Get-ChildItem -Path $BackupDir -Filter "backup_pos_*.dump" | Where-Object { $_.LastWriteTime -lt $FechaLimite }

$Borrados = 0
foreach ($Archivo in $ArchivosAntiguos) {
    Remove-Item $Archivo.FullName -Force
    $Borrados++
}
Write-Host "Depuración completada ($Borrados archivos rotados)" -ForegroundColor Green

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "RESPALDO FINALIZADO EXITOSAMENTE" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Cyan
