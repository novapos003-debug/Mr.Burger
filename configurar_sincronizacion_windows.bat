@echo off
chcp 65001 >nul
title Configurar sincronizacion con la nube - Mr. Burger
cd /d "%~dp0"

echo ============================================================
echo   CONFIGURAR SINCRONIZACION DE LA CAJA CON LA NUBE
echo ============================================================
echo.
echo Este paso se hace UNA sola vez por computador.
echo Pega el token de sincronizacion (el mismo valor que tiene la
echo variable CLOUD_SYNC_TOKEN del servicio "mrburger-api" en Render).
echo.

set "TOKEN="
set /p "TOKEN=Token de sincronizacion: "
if "%TOKEN%"=="" (
    echo.
    echo [CANCELADO] No escribiste ningun token. No se cambio nada.
    echo.
    pause
    exit /b 1
)

:: Conserva cualquier otra linea que ya exista en .env y reemplaza solo las de sincronizacion
if exist ".env" (
    findstr /v /b /i "CLOUD_SYNC_URL= CLOUD_SYNC_TOKEN= CLOUD_SYNC_ENABLED=" ".env" > ".env.tmp"
) else (
    type nul > ".env.tmp"
)
>> ".env.tmp" echo CLOUD_SYNC_URL=https://mrburger-api.onrender.com
>> ".env.tmp" echo CLOUD_SYNC_TOKEN=%TOKEN%
>> ".env.tmp" echo CLOUD_SYNC_ENABLED=true
move /y ".env.tmp" ".env" >nul

echo.
echo ============================================================
echo   LISTO. La caja quedo configurada para sincronizar.
echo   Cierra y vuelve a abrir el sistema (iniciar_windows.bat)
echo   para que tome el cambio.
echo ============================================================
echo.
pause
