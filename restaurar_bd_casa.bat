@echo off
chcp 65001 > nul
echo ========================================================
echo       RESTAURAR BASE DE DATOS MR. BURGER (CASA / PORTATIL)
echo ========================================================
echo.

set PGPASSWORD=restaurante_dev

REM Buscar ruta de PostgreSQL instalada en la maquina
set PG_BIN="C:\Program Files\PostgreSQL\18\bin"
if not exist %PG_BIN% set PG_BIN="C:\Program Files\PostgreSQL\17\bin"
if not exist %PG_BIN% set PG_BIN="C:\Program Files\PostgreSQL\16\bin"
if not exist %PG_BIN% set PG_BIN="C:\Program Files\PostgreSQL\15\bin"

echo Ubicacion detectada: %PG_BIN%
echo Restaurando archivo: database\backup_restaurante_completo.sql ...
echo.

%PG_BIN%\psql.exe -U restaurante -h 127.0.0.1 -p 5432 -d restaurante -f "%~dp0database\backup_restaurante_completo.sql"

if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo  [EXITO] Base de datos restaurada correctamente.
    echo  Todos los usuarios, recetas, compras y pedidos listos.
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo  [AVISO] Si la base de datos o el usuario no existen,
    echo  ejecuta primero: configurar_bd_windows.bat
    echo ========================================================
)
echo.
pause
