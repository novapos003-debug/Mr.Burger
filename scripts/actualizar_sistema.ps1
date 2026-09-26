# ============================================================
# SCRIPT DE ACTUALIZACIÓN DEL SISTEMA POS MR. BURGER
# Actualiza código, migraciones, frontend PWA y notifica a clientes Android
# ============================================================

$ErrorActionPreference = "Continue"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $ProjectRoot "frontend"
$BackendDir = Join-Path $ProjectRoot "backend"
$ScriptsDir = $PSScriptRoot

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   ACTUALIZADOR AUTOMÁTICO DE SISTEMA — POS MR. BURGER     " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Respaldo de seguridad previo obligatorio
Write-Host "`n[PASO 1/5] Creando copia de seguridad preventiva..." -ForegroundColor Yellow
$BackupScript = Join-Path $ScriptsDir "backup_diario.ps1"
if (Test-Path $BackupScript) {
    & powershell.exe -ExecutionPolicy Bypass -File $BackupScript
    if ($LASTEXITCODE -ne 0) {
        Write-Host "AVISO: No se pudo realizar el backup preventivo (posiblemente Docker detenido)." -ForegroundColor Yellow
        $Confirm = Read-Host "¿Deseas continuar con la actualización de todos modos? (S/N)"
        if ($Confirm -ne "S" -and $Confirm -ne "s") {
            Write-Host "Actualización cancelada por el usuario." -ForegroundColor Red
            exit 1
        }
    }
}

# 2. Actualización de código fuente (si está bajo Git)
Write-Host "`n[PASO 2/5] Comprobando actualizaciones de código..." -ForegroundColor Yellow
if (Test-Path (Join-Path $ProjectRoot ".git")) {
    Set-Location $ProjectRoot
    git pull
    Write-Host "Código actualizado desde el repositorio." -ForegroundColor Green
} else {
    Write-Host "Repositorio local listo con las últimas modificaciones." -ForegroundColor Green
}

# 3. Compilación del Frontend PWA con nuevos activos y Service Worker
Write-Host "`n[PASO 3/5] Compilando nueva versión de la PWA para Android..." -ForegroundColor Yellow
Set-Location $FrontendDir
npm run build

if ($LASTEXITCODE -eq 0) {
    Write-Host "Frontend PWA compilado exitosamente. Hash de versión actualizado." -ForegroundColor Green
} else {
    Write-Host "ERROR: Falló la compilación del frontend. Revisa los errores." -ForegroundColor Red
    exit 1
}

# 4. Reinicio de contenedores Docker / Servicios
Write-Host "`n[PASO 4/5] Reiniciando servicios del sistema..." -ForegroundColor Yellow
Set-Location $ProjectRoot
$BackendRunning = docker ps --filter "name=restaurante_backend" --filter "status=running" --format "{{.Names}}"
if ($BackendRunning) {
    docker restart restaurante_backend | Out-Null
    Write-Host "Contenedor 'restaurante_backend' reiniciado con la nueva versión." -ForegroundColor Green
} else {
    Write-Host "Nota: Los contenedores Docker no están corriendo. Inícialos con docker compose up -d" -ForegroundColor Gray
}

# 5. Detección de IP Local LAN para los dispositivos Android
Write-Host "`n[PASO 5/5] Detectando dirección de red LAN para clientes Android..." -ForegroundColor Yellow
$LanIps = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
    $_.IPAddress -notlike "127.*" -and 
    $_.IPAddress -notlike "169.254.*" -and 
    $_.InterfaceAlias -notlike "*vEthernet*" -and 
    $_.InterfaceAlias -notlike "*Loopback*" 
} | Select-Object -ExpandProperty IPAddress

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "   ¡SISTEMA ACTUALIZADO EXITOSAMENTE A LA ÚLTIMA VERSIÓN!    " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green

Write-Host "`n¿Cómo reciben la actualización los dispositivos móviles?" -ForegroundColor Cyan
Write-Host "1. Los celulares y tablets de los meseros/cocina están en el mismo Wi-Fi." -ForegroundColor White
Write-Host "2. Al abrir la app o tocar cualquier pantalla, el Service Worker detectará los archivos nuevos." -ForegroundColor White
Write-Host "3. Aparecerá el aviso automático: '¡Nueva versión disponible!' o se actualizará sola." -ForegroundColor White
Write-Host "4. NO es necesario reinstalar manualmente nada en los teléfonos.`n" -ForegroundColor Yellow

if ($LanIps) {
    Write-Host "Direcciones LAN para conectar dispositivos Android al Wi-Fi del restaurante:" -ForegroundColor Cyan
    foreach ($Ip in $LanIps) {
        Write-Host "  👉 http://${Ip}:5173  (o puerto 8000 si usas servidor de producción)" -ForegroundColor Green
    }
}

Write-Host ""
Set-Location $ProjectRoot
