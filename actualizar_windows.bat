@echo off
title Actualizar Mr. Burger POS - Windows
cd /d "%~dp0"

echo ============================================================
echo   ACTUALIZANDO MR. BURGER A LA ULTIMA VERSION DE GITHUB
echo ============================================================
echo.

git fetch origin main
git reset --hard origin/main

:: IMPORTANTE: no modificar nada de aqui hacia ARRIBA (ver nota en iniciar_windows.bat).
call "%~dp0scripts\preparar_sistema.bat"
if errorlevel 1 exit /b 1

echo.
echo Iniciando el sistema con la nueva version...
call "%~dp0scripts\arrancar_servicios.bat"
exit /b
