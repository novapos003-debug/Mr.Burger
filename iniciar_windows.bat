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

:: Asegurar que el servicio de PostgreSQL esté iniciado
net start postgresql-x64-15 >nul 2>nul
net start postgresql-x64-16 >nul 2>nul
net start postgresql-x64-17 >nul 2>nul
net start postgresql-15 >nul 2>nul
net start postgresql-16 >nul 2>nul

:: Detectar comando de Python disponible
set PY_CMD=python
where python >nul 2>nul
if %errorlevel% neq 0 (
    set PY_CMD=py
)

:: Cerrar procesos previos y liberar estrictamente los puertos 8000 y 5173
taskkill /F /FI "WINDOWTITLE eq MrBurger-Backend*" 2>nul
taskkill /F /FI "WINDOWTITLE eq MrBurger-Frontend*" 2>nul
%PY_CMD% liberar_puertos.py >nul 2>nul

:: 1. Iniciar Backend FastAPI (con IPv4 127.0.0.1 para máxima compatibilidad Windows)
echo [1/3] Iniciando Cerebro Backend (Puerto 8000)...
start "MrBurger-Backend" /min cmd /c "cd /d %~dp0backend && set PYTHONUTF8=1&& set PYTHONIOENCODING=utf-8&& set DATABASE_URL=postgresql://restaurante:restaurante_dev@127.0.0.1:5432/restaurante&& set SECRET_KEY=ymKGPH7kaMDwp4CJZluFvgU3BRcAnbrj&& %PY_CMD% -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ..\backend.log 2>&1"

:: 2. Iniciar Frontend PWA estrictamente en el puerto 5173
echo [2/3] Iniciando Servidor Web PWA (Puerto 5173)...
start "MrBurger-Frontend" /min cmd /c "cd /d %~dp0 && %PY_CMD% serve_frontend.py"

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
