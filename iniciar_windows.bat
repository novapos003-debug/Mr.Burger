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
    git fetch origin main --quiet 2>nul
    git reset --hard origin/main --quiet 2>nul
)

:: Cerrar procesos previos si estaban abiertos para evitar puertos ocupados
taskkill /F /FI "WINDOWTITLE eq MrBurger-Backend*" 2>nul
taskkill /F /FI "WINDOWTITLE eq MrBurger-Frontend*" 2>nul

:: Detectar comando de Python disponible
set PY_CMD=python
where python >nul 2>nul
if %errorlevel% neq 0 (
    set PY_CMD=py
)

:: 1. Iniciar Backend FastAPI
echo [1/3] Iniciando Cerebro Backend (Puerto 8000)...
start "MrBurger-Backend" /min cmd /c "cd /d %~dp0backend && set DATABASE_URL=postgresql://restaurante:restaurante_dev@localhost:5432/restaurante&& set SECRET_KEY=ymKGPH7kaMDwp4CJZluFvgU3BRcAnbrj&& %PY_CMD% -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

:: 2. Iniciar Frontend PWA (Usa Node si existe, o Python directamente sin instalar nada extra)
echo [2/3] Iniciando Servidor Web PWA (Puerto 5173)...
where npx >nul 2>nul
if %errorlevel% equ 0 (
    start "MrBurger-Frontend" /min cmd /c "cd /d %~dp0frontend && npx serve -s dist -l 5173 --cors"
) else (
    start "MrBurger-Frontend" /min cmd /c "cd /d %~dp0 && %PY_CMD% serve_frontend.py"
)

:: 3. Abrir la Caja POS en el navegador
echo [3/3] Abriendo pantalla de Caja en el navegador...
timeout /t 2 /nobreak >nul
start http://localhost:5173

echo.
echo ============================================================
echo   ¡SISTEMA MR. BURGER EN VIVO Y CORRIENDO EXITOSAMENTE!
echo ============================================================
echo   - Pantalla de Caja:  http://localhost:5173
echo   - Celulares Meseros: http://[IP_DE_ESTA_PC]:5173
echo   - Tablet Cocina:     http://[IP_DE_ESTA_PC]:5173
echo ============================================================
echo.
timeout /t 5 >nul
