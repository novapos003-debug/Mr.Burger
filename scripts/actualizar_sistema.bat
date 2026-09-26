@echo off
title Actualizador POS Mr. Burger
color 0A
echo ============================================================
echo   LANZANDO ACTUALIZADOR AUTOMATICO DEL SISTEMA POS
echo ============================================================
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0actualizar_sistema.ps1"

echo.
echo Presione cualquier tecla para cerrar esta ventana...
pause >nul
