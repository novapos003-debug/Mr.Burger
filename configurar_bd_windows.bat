@echo off
title Configurar Base de Datos PostgreSQL - Mr. Burger
cd /d "%~dp0"

echo ============================================================
echo   CONFIGURANDO BASE DE DATOS LOCAL POSTGRESQL (WINDOWS)
echo ============================================================
echo.

:: 1. Buscar psql.exe en rutas de instalacion de Windows
where psql >nul 2>nul
if %errorlevel% neq 0 (
    if exist "C:\Program Files\PostgreSQL\18\bin\psql.exe" set "PATH=C:\Program Files\PostgreSQL\18\bin;%PATH%"
    if exist "C:\Program Files\PostgreSQL\17\bin\psql.exe" set "PATH=C:\Program Files\PostgreSQL\17\bin;%PATH%"
    if exist "C:\Program Files\PostgreSQL\16\bin\psql.exe" set "PATH=C:\Program Files\PostgreSQL\16\bin;%PATH%"
    if exist "C:\Program Files\PostgreSQL\15\bin\psql.exe" set "PATH=C:\Program Files\PostgreSQL\15\bin;%PATH%"
    if exist "C:\Program Files\PostgreSQL\14\bin\psql.exe" set "PATH=C:\Program Files\PostgreSQL\14\bin;%PATH%"
    if exist "C:\Program Files (x86)\PostgreSQL\16\bin\psql.exe" set "PATH=C:\Program Files (x86)\PostgreSQL\16\bin;%PATH%"
)

where psql >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] No se encontro 'psql.exe' en el sistema.
    echo Asegurate de que PostgreSQL este instalado en C:\Program Files\PostgreSQL
    echo.
    pause
    exit /b 1
)

set PGPASSWORD=restaurante_dev

:: SEGURIDAD: si la base ya tiene productos, no se toca (evita duplicar el catalogo)
set "YA_TIENE="
for /f "usebackq delims=" %%N in (`psql -U restaurante -h 127.0.0.1 -d restaurante -tAc "select count(*) from producto" 2^>nul`) do set "YA_TIENE=%%N"
if defined YA_TIENE if not "%YA_TIENE%"=="0" goto ya_configurada

echo [1/4] Creando usuario 'restaurante' y base de datos 'restaurante'...
psql -U postgres -c "CREATE USER restaurante WITH PASSWORD 'restaurante_dev' SUPERUSER;"
psql -U postgres -c "CREATE DATABASE restaurante OWNER restaurante;"
psql -U postgres -c "ALTER USER restaurante WITH PASSWORD 'restaurante_dev';"

echo.
echo [2/4] Inyectando tablas y estructura (01_schema.sql)...
set PGPASSWORD=restaurante_dev
psql -U restaurante -d restaurante -f database\init\01_schema.sql

echo.
echo [3/4] Inyectando catalogo inicial y usuarios (02_seeds.sql)...
psql -U restaurante -d restaurante -f database\init\02_seeds.sql

echo.
echo [4/4] Inyectando insumos y empaques (03_migracion_arquitectura_e_insumos.sql)...
psql -U restaurante -d restaurante -f database\init\03_migracion_arquitectura_e_insumos.sql

echo.
echo ============================================================
echo   ¡BASE DE DATOS CONFIGURADA CON ÉXITO EN POSTGRESQL!
echo ============================================================
echo.
pause
exit /b 0

:ya_configurada
echo La base de datos "restaurante" ya existe y tiene %YA_TIENE% productos.
echo No se modifico nada. Para empezar de cero hay que borrarla a mano primero.
echo.
pause
exit /b 0
