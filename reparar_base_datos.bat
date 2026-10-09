@echo off
title Mr. Burger POS - Reparar Base de Datos PostgreSQL
cd /d "%~dp0"

echo ============================================================
echo   MR. BURGER POS - REPARADOR AUTOMATICO DE BASE DE DATOS
echo ============================================================
echo.

:: Detectar comando de Python disponible
set PY_CMD=python
where python >nul 2>nul
if %errorlevel% neq 0 (
    set PY_CMD=py
)

%PY_CMD% reparar_base_datos.py

pause
