@echo off
title Actualizar Mr. Burger POS - Windows
cd /d "%~dp0"

echo ============================================================
echo   ACTUALIZANDO MR. BURGER A LA ULTIMA VERSION DE GITHUB
echo ============================================================
echo.

git fetch origin main
git reset --hard origin/main

echo.
echo Reiniciando servicios con la nueva version...
call iniciar_windows.bat
