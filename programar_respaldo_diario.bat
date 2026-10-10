@echo off
chcp 65001 >nul
title Programar respaldo diario - Mr. Burger
cd /d "%~dp0"

echo ============================================================
echo   PROGRAMAR RESPALDO AUTOMATICO DIARIO DE LA BASE DE DATOS
echo ============================================================
echo.
echo Crea una tarea de Windows que ejecuta respaldar_bd_windows.bat
echo todos los dias a las 4:00 p.m. (antes de abrir el restaurante).
echo Si el computador estaba apagado a esa hora, lo hace al encender.
echo.

schtasks /Create /F /TN "MrBurger - Respaldo diario" /SC DAILY /ST 16:00 ^
  /TR "\"%~dp0respaldar_bd_windows.bat\" /silencioso" >nul
if errorlevel 1 (
    echo [ERROR] No se pudo crear la tarea. Ejecuta este archivo con
    echo         clic derecho ^> "Ejecutar como administrador".
    echo.
    if /i not "%~1"=="/silencioso" pause
    exit /b 1
)

:: Que la tarea se ejecute al encender si se perdio la hora programada
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$t = Get-ScheduledTask -TaskName 'MrBurger - Respaldo diario'; $t.Settings.StartWhenAvailable = $true; $t.Settings.DisallowStartIfOnBatteries = $false; Set-ScheduledTask -InputObject $t | Out-Null"

echo [OK] Respaldo diario programado para las 4:00 p.m.
echo      Los archivos quedan en la carpeta "backups" (se conservan 30 dias).
echo.
if /i not "%~1"=="/silencioso" pause
