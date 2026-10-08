@echo off
title Configurar Base de Datos PostgreSQL - Mr. Burger
cd /d "%~dp0"

echo ============================================================
echo   CONFIGURANDO BASE DE DATOS LOCAL POSTGRESQL (WINDOWS)
echo ============================================================
echo.

set PGPASSWORD=restaurante_dev

echo [1/4] Creando usuario 'restaurante' y base de datos 'restaurante'...
psql -U postgres -c "CREATE USER restaurante WITH PASSWORD 'restaurante_dev' SUPERUSER;" 2>nul
psql -U postgres -c "CREATE DATABASE restaurante OWNER restaurante;" 2>nul
psql -U postgres -c "ALTER USER restaurante WITH PASSWORD 'restaurante_dev';" 2>nul

echo [2/4] Inyectando tablas y estructura (01_schema.sql)...
psql -U restaurante -d restaurante -f database\init\01_schema.sql

echo [3/4] Inyectando catalogo inicial y usuarios (02_seeds.sql)...
psql -U restaurante -d restaurante -f database\init\02_seeds.sql

echo [4/4] Inyectando insumos y empaques (03_migracion_arquitectura_e_insumos.sql)...
psql -U restaurante -d restaurante -f database\init\03_migracion_arquitectura_e_insumos.sql

echo.
echo ============================================================
echo   ¡BASE DE DATOS CONFIGURADA CON ÉXITO EN POSTGRESQL!
echo ============================================================
echo.
pause
