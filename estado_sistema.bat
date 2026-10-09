@echo off
title Diagnostico de Estado del Sistema - Mr. Burger POS
cd /d "%~dp0"

echo ============================================================
echo   MR. BURGER POS - DIAGNOSTICO DE ESTADO EN VIVO
echo ============================================================
echo.

:: 1. Verificar PostgreSQL
echo [1/4] Verificando Base de Datos PostgreSQL...
powershell -Command "if (Test-NetConnection -ComputerName 127.0.0.1 -Port 5432 -InformationLevel Quiet) { Write-Host '  [OK] PostgreSQL respondiendo en puerto 5432' -ForegroundColor Green } elseif (Test-NetConnection -ComputerName 127.0.0.1 -Port 5433 -InformationLevel Quiet) { Write-Host '  [OK] PostgreSQL respondiendo en puerto 5433' -ForegroundColor Green } else { Write-Host '  [FALLO] PostgreSQL NO esta escuchando en puertos 5432 ni 5433' -ForegroundColor Red }"

:: 2. Verificar Backend FastAPI
echo.
echo [2/4] Verificando Cerebro Backend (Puerto 8000)...
powershell -Command "try { $r = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/health' -TimeoutSec 3; Write-Host '  [OK] Backend VIVO y respondiendo exitosamente (status: ' $r.status ')' -ForegroundColor Green } catch { Write-Host '  [FALLO] Backend NO responde en http://127.0.0.1:8000 (' $_.Exception.Message ')' -ForegroundColor Red }"

:: 3. Verificar Frontend PWA
echo.
echo [3/4] Verificando Frontend Web (Puerto 5173)...
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:5173' -TimeoutSec 3; Write-Host '  [OK] Frontend Web VIVO en puerto 5173' -ForegroundColor Green } catch { Write-Host '  [FALLO] Frontend Web NO responde en puerto 5173' -ForegroundColor Red }"

:: 4. Direcciones IP de la PC
echo.
echo [4/4] Direcciones IP locales para conectar celulares:
powershell -Command "Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch 'Loopback|vEthernet' } | ForEach-Object { Write-Host '  -> http://' $_.IPAddress ':5173' -ForegroundColor Cyan }"

:: 5. Ultimas lineas del registro de backend si existe
if exist "backend.log" (
    echo.
    echo ============================================================
    echo   ULTIMAS LINEAS DE BACKEND.LOG:
    echo ============================================================
    powershell -Command "Get-Content backend.log -Tail 15"
)

echo.
echo ============================================================
pause
