@echo off
chcp 65001 >nul
title Respaldo de la base de datos - Mr. Burger
cd /d "%~dp0"

:: ============================================================
:: RESPALDO DE LA BASE DE DATOS LOCAL (PostgreSQL nativo de Windows)
:: - Guarda un archivo en la carpeta "backups" con fecha y hora.
:: - Si hay una memoria USB conectada, deja una copia en X:\BACKUP_POS.
:: - Borra los respaldos locales con mas de 30 dias.
:: Con el parametro /silencioso no espera una tecla (para la tarea programada).
:: ============================================================

set "PG_BIN="
for %%V in (18 17 16 15 14) do (
    if not defined PG_BIN if exist "C:\Program Files\PostgreSQL\%%V\bin\pg_dump.exe" set "PG_BIN=C:\Program Files\PostgreSQL\%%V\bin"
)
if not defined PG_BIN (
    where pg_dump >nul 2>nul && for /f "delims=" %%P in ('where pg_dump') do if not defined PG_BIN set "PG_BIN=%%~dpP"
)
if not defined PG_BIN (
    echo [ERROR] No se encontro pg_dump.exe. Verifica que PostgreSQL este instalado.
    if /i not "%~1"=="/silencioso" pause
    exit /b 1
)

if not exist "backups" mkdir "backups"

for /f %%T in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "SELLO=%%T"
set "ARCHIVO=backups\backup_pos_%SELLO%.dump"

set PGPASSWORD=restaurante_dev
echo Respaldando la base de datos en %ARCHIVO% ...
"%PG_BIN%\pg_dump.exe" -U restaurante -h 127.0.0.1 -p 5432 -d restaurante -F c -b -f "%ARCHIVO%"
if errorlevel 1 (
    echo [ERROR] El respaldo fallo. Revisa que PostgreSQL este encendido.
    if exist "%ARCHIVO%" del "%ARCHIVO%"
    if /i not "%~1"=="/silencioso" pause
    exit /b 1
)

:: Copia a memoria USB si hay alguna conectada, y limpieza de respaldos viejos
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$a = Get-Item '%ARCHIVO%'; Write-Host ('  [OK] Respaldo creado: {0:N0} KB' -f ($a.Length/1KB));" ^
  "Get-CimInstance Win32_LogicalDisk | Where-Object DriveType -eq 2 | ForEach-Object {" ^
  "  try { $d = Join-Path ($_.DeviceID + '\') 'BACKUP_POS'; New-Item -ItemType Directory -Force $d | Out-Null; Copy-Item $a.FullName $d -Force; Write-Host ('  [OK] Copia en memoria USB: ' + $d) } catch { Write-Host ('  [AVISO] No se pudo copiar a ' + $_.DeviceID) } };" ^
  "Get-ChildItem 'backups' -Filter 'backup_pos_*.dump' | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } | Remove-Item -Force"

echo.
echo Respaldo terminado.
if /i not "%~1"=="/silencioso" pause
exit /b 0
