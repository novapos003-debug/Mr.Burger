@echo off
title Mr. Burger POS - Modo Visible con Consolas
cd /d "%~dp0"

echo ============================================================
echo   INICIANDO MR. BURGER EN MODO VISIBLE CON CONSOLAS
echo ============================================================
echo.

:: Detectar comando de Python disponible
set PY_CMD=python
where python >nul 2>nul
if %errorlevel% neq 0 (
    set PY_CMD=py
)

:: Liberar puertos previos
%PY_CMD% liberar_puertos.py

:: Iniciar Backend en ventana visible
start "Backend MrBurger" cmd /k "cd /d %~dp0backend && set DATABASE_URL=postgresql://restaurante:restaurante_dev@127.0.0.1:5432/restaurante&& set SECRET_KEY=ymKGPH7kaMDwp4CJZluFvgU3BRcAnbrj&& %PY_CMD% -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

:: Iniciar Frontend en ventana visible
start "Frontend MrBurger" cmd /k "cd /d %~dp0 && %PY_CMD% serve_frontend.py"

timeout /t 3 /nobreak >nul
start http://localhost:5173

echo.
echo Las ventanas negras de Backend y Frontend estan abiertas.
echo Si sale algun error en letras rojas o amarillas, podras verlo directamente ahi.
echo.
pause
