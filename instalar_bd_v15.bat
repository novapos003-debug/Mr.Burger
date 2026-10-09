@echo off
title Inicializar Base de Datos PostgreSQL 15 - Mr. Burger
cd /d "C:\mrburger"

echo ============================================================
echo   INICIALIZANDO BASE DE DATOS MR. BURGER (POSTGRESQL 15)
echo ============================================================
echo.

set "PG_BIN=C:\Program Files\PostgreSQL\15\bin\psql.exe"
if not exist "%PG_BIN%" (
    if exist "C:\Program Files\PostgreSQL\16\bin\psql.exe" set "PG_BIN=C:\Program Files\PostgreSQL\16\bin\psql.exe"
    if exist "C:\Program Files\PostgreSQL\17\bin\psql.exe" set "PG_BIN=C:\Program Files\PostgreSQL\17\bin\psql.exe"
    if exist "C:\Program Files (x86)\PostgreSQL\15\bin\psql.exe" set "PG_BIN=C:\Program Files (x86)\PostgreSQL\15\bin\psql.exe"
)

echo Usando ejecutable: "%PG_BIN%"
echo.

set PGPASSWORD=restaurante_dev

echo [1/5] Creando usuario 'restaurante'...
"%PG_BIN%" -U postgres -c "CREATE USER restaurante WITH PASSWORD 'restaurante_dev' SUPERUSER;"
"%PG_BIN%" -U postgres -c "ALTER USER restaurante WITH PASSWORD 'restaurante_dev';"

echo.
echo [2/5] Creando base de datos 'restaurante'...
"%PG_BIN%" -U postgres -c "CREATE DATABASE restaurante OWNER restaurante;"

echo.
echo [3/5] Creando tablas del sistema (01_schema.sql)...
set PGPASSWORD=restaurante_dev
"%PG_BIN%" -U restaurante -d restaurante -f "C:\mrburger\database\init\01_schema.sql"

echo.
echo [4/5] Creando usuarios y recetas (02_seeds.sql)...
"%PG_BIN%" -U restaurante -d restaurante -f "C:\mrburger\database\init\02_seeds.sql"

echo.
echo [5/5] Creando insumos y empaques (03_migracion_arquitectura_e_insumos.sql)...
"%PG_BIN%" -U restaurante -d restaurante -f "C:\mrburger\database\init\03_migracion_arquitectura_e_insumos.sql"

echo.
echo ============================================================
echo   ¡PROCESO COMPLETADO!
echo ============================================================
echo Revisa arriba si salieron mensajes de CREATE TABLE y INSERT.
echo.
pause
