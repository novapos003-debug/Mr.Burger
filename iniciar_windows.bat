@echo off
title Mr. Burger POS - Servidor Maestro Windows
cd /d "%~dp0"

echo ============================================================
echo   MR. BURGER POS - SERVIDOR MAESTRO LOCAL (WINDOWS)
echo ============================================================
echo.

:: 0. Auto-actualización silenciosa si hay conexión a internet y Git
if exist ".git" (
    echo [0/3] Verificando actualizaciones en GitHub...
    git pull origin main --quiet 2>nul
)

:: IMPORTANTE: no modificar nada de aqui hacia ARRIBA. Mientras este archivo se ejecuta,
:: 'git pull' puede reemplazarlo; Windows sigue leyendo desde la misma posicion, asi que el
:: inicio debe permanecer igual. Todo lo demas vive en scripts\arrancar_servicios.bat,
:: que se lee ya actualizado.
call "%~dp0scripts\arrancar_servicios.bat"
exit /b
