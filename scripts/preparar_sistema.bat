@echo off
chcp 65001 >nul
:: ============================================================
:: Deja este computador listo para operar. Lo llama actualizar_windows.bat
:: DESPUES de descargar la ultima version. Se puede ejecutar las veces
:: que haga falta: solo hace lo que falte.
:: ============================================================
cd /d "%~dp0.."

:: Se prueba ejecutandolo: en algunos Windows "python" es solo un acceso a la Tienda
set PY_CMD=python
python -c "import sys" >nul 2>nul
if errorlevel 1 set PY_CMD=py
%PY_CMD% -c "import sys" >nul 2>nul
if errorlevel 1 (
    echo [ERROR] No se encontro Python. Instala Python 3.11 y marca "Add Python to PATH".
    pause
    exit /b 1
)

echo.
echo [A] Verificando componentes de Python...
%PY_CMD% -c "import fastapi, sqlalchemy, psycopg2, httpx, jose, passlib, uvicorn, websockets, multipart" >nul 2>nul
if errorlevel 1 (
    echo     Instalando componentes que faltan (requiere internet^)...
    %PY_CMD% -m pip install --disable-pip-version-check -q -r backend\requirements.txt
    if errorlevel 1 echo     [AVISO] No se pudieron instalar. Revisa la conexion a internet.
) else (
    echo     [OK] Componentes completos.
)

echo.
echo [B] Verificando la base de datos local...
for %%S in (postgresql-x64-18 postgresql-x64-17 postgresql-x64-16 postgresql-x64-15 postgresql-18 postgresql-17 postgresql-16 postgresql-15) do net start %%S >nul 2>nul
%PY_CMD% scripts\verificar_bd.py
set "ESTADO_BD=%errorlevel%"
if "%ESTADO_BD%"=="2" goto crear_bd
if "%ESTADO_BD%"=="0" goto respaldo_previo
echo.
echo     No se inicia el sistema para no arriesgar los datos.
echo     Revisa que PostgreSQL este instalado y encendido, y vuelve a ejecutar este archivo.
echo.
pause
exit /b 1

:crear_bd
echo             Es la primera vez en este computador: se va a crear ahora.
echo.
call "%~dp0..\configurar_bd_windows.bat"
goto fin_bd

:respaldo_previo
:: Copia de seguridad ANTES de arrancar la version nueva (queda en la carpeta backups)
echo     Guardando una copia de seguridad antes de actualizar...
call "%~dp0..\respaldar_bd_windows.bat" /silencioso
if errorlevel 1 echo     [AVISO] No se pudo hacer la copia de seguridad. Avisa antes de continuar.

:fin_bd

echo.
echo [C] Verificando la sincronizacion con la nube...
%PY_CMD% scripts\verificar_token.py
if not "%errorlevel%"=="2" goto fin_token
call "%~dp0..\configurar_sincronizacion_windows.bat"
%PY_CMD% scripts\verificar_token.py
if "%errorlevel%"=="2" (
    echo     [AVISO] El token sigue sin ser valido. La caja va a funcionar, pero NO subira
    echo             datos a la web hasta que ejecutes configurar_sincronizacion_windows.bat
    echo             con el token correcto.
    pause
)
:fin_token

echo.
echo [D] Verificando el respaldo diario automatico...
schtasks /Query /TN "MrBurger - Respaldo diario" >nul 2>nul
if errorlevel 1 (
    call "%~dp0..\programar_respaldo_diario.bat" /silencioso
) else (
    echo     [OK] Respaldo diario programado.
)

echo.
echo [E] Verificando el firewall para celulares y tablet...
netsh advfirewall firewall show rule name="MrBurger Backend (8000)" >nul 2>nul
if errorlevel 1 (
    echo     [FALTA] Los puertos no estan abiertos. Haz clic derecho sobre
    echo             configurar_firewall_windows.bat y elige "Ejecutar como administrador".
) else (
    echo     [OK] Puertos 5173 y 8000 abiertos.
)

echo.
echo [F] Impresora de tirillas...
powershell -NoProfile -Command "$p = Get-CimInstance Win32_Printer | Where-Object Default; if ($p) { Write-Host ('    Predeterminada de Windows: ' + $p.Name); if ($p.Name -match 'PDF|XPS|OneNote|Fax') { Write-Host '    [AVISO] La predeterminada NO es la termica. Cambiala en Configuracion > Impresoras.' -ForegroundColor Yellow } } else { Write-Host '    [AVISO] No hay impresora predeterminada. Instala la termica y marcala como predeterminada.' -ForegroundColor Yellow }"

echo.
exit /b 0
